from __future__ import annotations

import re
from typing import Any

from neo4j import AsyncDriver

from backend.models.graph_models import (
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
    SearchResult,
)


def _safe_props(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert neo4j native types (Date, DateTime, etc.) to JSON-serializable values."""
    out: dict[str, Any] = {}
    for k, v in raw.items():
        if hasattr(v, "iso_format"):
            out[k] = v.iso_format()
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def _parse_node(record: dict[str, Any], prefix: str = "n") -> GraphNode:
    """Convert a Neo4j node record into a GraphNode."""
    node = record[prefix]
    labels = list(node.labels) if hasattr(node, "labels") else node.get("labels", [])
    props = _safe_props(
        dict(node) if hasattr(node, "items") else dict(node.get("properties", {}))
    )
    node_type = _resolve_node_type(labels)
    label = props.pop(
        "name",
        props.get("title", props.get("reference_number", props.get("description", ""))),
    )
    element_id = (
        node.element_id
        if hasattr(node, "element_id")
        else record.get(f"{prefix}_id", "")
    )
    risk_score = props.pop("risk_score", None)
    return GraphNode(
        id=str(element_id),
        label=str(label),
        type=node_type,
        properties=props,
        risk_score=risk_score,
    )


def _resolve_node_type(labels: list[str]) -> NodeType:
    """Map Neo4j labels to our NodeType enum."""
    type_map = {nt.value: nt for nt in NodeType}
    for lbl in labels:
        if lbl in type_map:
            return type_map[lbl]
    return NodeType.PERSON  # fallback


def _parse_edge(record: dict[str, Any], prefix: str = "r") -> GraphEdge:
    """Convert a Neo4j relationship record into a GraphEdge."""
    rel = record[prefix]
    props = _safe_props(
        dict(rel) if hasattr(rel, "items") else dict(rel.get("properties", {}))
    )
    rel_type = rel.type if hasattr(rel, "type") else record.get(f"{prefix}_type", "")
    element_id = (
        rel.element_id if hasattr(rel, "element_id") else record.get(f"{prefix}_id", "")
    )
    start_id = (
        rel.start_node.element_id
        if hasattr(rel, "start_node")
        else record.get("source_id", "")
    )
    end_id = (
        rel.end_node.element_id
        if hasattr(rel, "end_node")
        else record.get("target_id", "")
    )

    edge_type = _resolve_edge_type(str(rel_type))
    return GraphEdge(
        id=str(element_id),
        source=str(start_id),
        target=str(end_id),
        type=edge_type,
        properties=props,
    )


def _resolve_edge_type(rel_type: str) -> EdgeType:
    type_map = {et.value: et for et in EdgeType}
    return type_map.get(rel_type, EdgeType.AWARDED_TO)


_LUCENE_SPECIAL = re.compile(r'([+\-&|!(){}\[\]^"~*?:\\/])')


def _escape_lucene(query: str) -> str:
    return _LUCENE_SPECIAL.sub(r"\\\1", query.strip())


class Neo4jService:
    def __init__(self, driver: AsyncDriver) -> None:
        self.driver = driver

    async def get_node(self, node_id: str) -> GraphNode | None:
        query = """
        MATCH (n)
        WHERE elementId(n) = $node_id
        RETURN n
        """
        async with self.driver.session() as session:
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            if not record:
                return None
            return _parse_node(dict(record))

    async def get_neighbors(
        self,
        node_id: str,
        node_type_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        type_clause = ""
        if node_type_filter:
            type_clause = "AND $type_filter IN labels(m)"

        query = f"""
        MATCH (n)-[r]-(m)
        WHERE elementId(n) = $node_id {type_clause}
        RETURN n, r, m
        ORDER BY elementId(m)
        SKIP $offset LIMIT $limit
        """
        params: dict[str, Any] = {"node_id": node_id, "offset": offset, "limit": limit}
        if node_type_filter:
            params["type_filter"] = node_type_filter

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        seen_nodes: set[str] = set()

        async with self.driver.session() as session:
            result = await session.run(query, **params)
            async for record in result:
                rec = dict(record)
                neighbor = _parse_node(rec, "m")
                edge = _parse_edge(rec, "r")
                if neighbor.id not in seen_nodes:
                    nodes.append(neighbor)
                    seen_nodes.add(neighbor.id)
                edges.append(edge)

        return {"nodes": nodes, "edges": edges}

    async def search(
        self,
        query_text: str,
        node_type: str | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        safe_query = _escape_lucene(query_text)
        if not safe_query:
            return []
        safe_query = f"{safe_query}*"

        cypher = """
        CALL db.index.fulltext.queryNodes('entity_search', $search_term)
        YIELD node, score
        RETURN node, score, labels(node) as labels
        LIMIT $limit
        """

        results: list[SearchResult] = []
        async with self.driver.session() as session:
            result = await session.run(cypher, search_term=safe_query, limit=limit)
            async for record in result:
                rec = dict(record)
                node = rec["node"]
                labels = rec["labels"]
                score = rec["score"]
                node_type_resolved = _resolve_node_type(labels)

                if node_type and node_type_resolved.value != node_type:
                    continue

                props = dict(node)
                name = props.get("name", props.get("title", ""))
                context_parts = []
                if "province" in props:
                    context_parts.append(props["province"])
                if "classification" in props:
                    context_parts.append(props["classification"])
                if "position" in props:
                    context_parts.append(props["position"])

                results.append(
                    SearchResult(
                        id=str(node.element_id),
                        name=str(name),
                        type=node_type_resolved,
                        context=" - ".join(context_parts),
                        score=float(score),
                    )
                )

        return results

    async def get_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 6,
    ) -> dict[str, Any] | None:
        query = (
            """
        MATCH (start), (end)
        WHERE elementId(start) = $from_id AND elementId(end) = $to_id
        MATCH p = shortestPath((start)-[*..%d]-(end))
        RETURN nodes(p) as path_nodes, relationships(p) as path_rels, length(p) as path_length
        """
            % max_depth
        )

        async with self.driver.session() as session:
            result = await session.run(query, from_id=from_id, to_id=to_id)
            record = await result.single()
            if not record:
                return None

            rec = dict(record)
            nodes = []
            for node in rec["path_nodes"]:
                labels = list(node.labels) if hasattr(node, "labels") else []
                props = _safe_props(dict(node))
                nt = _resolve_node_type(labels)
                label = props.pop("name", props.get("title", ""))
                eid = str(node.element_id) if hasattr(node, "element_id") else ""
                risk = props.pop("risk_score", None)
                nodes.append(
                    GraphNode(
                        id=eid,
                        label=str(label),
                        type=nt,
                        properties=props,
                        risk_score=risk,
                    )
                )

            edges = []
            for rel in rec["path_rels"]:
                props = _safe_props(dict(rel))
                et = _resolve_edge_type(rel.type)
                eid = str(rel.element_id) if hasattr(rel, "element_id") else ""
                src = (
                    str(rel.start_node.element_id) if hasattr(rel, "start_node") else ""
                )
                tgt = str(rel.end_node.element_id) if hasattr(rel, "end_node") else ""
                edges.append(
                    GraphEdge(
                        id=eid,
                        source=src,
                        target=tgt,
                        type=et,
                        properties=props,
                    )
                )

            return {
                "nodes": nodes,
                "edges": edges,
                "length": int(rec["path_length"]),
            }

    async def get_subgraph(
        self,
        center_id: str,
        depth: int = 2,
    ) -> dict[str, Any]:
        query = """
        MATCH (center)
        WHERE elementId(center) = $center_id
        CALL apoc.path.subgraphAll(center, {maxLevel: $depth})
        YIELD nodes as sg_nodes, relationships as sg_rels
        RETURN sg_nodes, sg_rels
        """
        # fallback if APOC not available
        fallback_query = (
            """
        MATCH path = (center)-[*1..%d]-(connected)
        WHERE elementId(center) = $center_id
        UNWIND nodes(path) as n
        UNWIND relationships(path) as r
        RETURN collect(DISTINCT n) as sg_nodes, collect(DISTINCT r) as sg_rels
        """
            % depth
        )

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        seen_nodes: set[str] = set()
        seen_edges: set[str] = set()

        async with self.driver.session() as session:
            try:
                result = await session.run(query, center_id=center_id, depth=depth)
            except Exception:
                result = await session.run(fallback_query, center_id=center_id)

            record = await result.single()
            if not record:
                return {"nodes": nodes, "edges": edges}

            rec = dict(record)
            for node in rec["sg_nodes"]:
                eid = str(node.element_id) if hasattr(node, "element_id") else ""
                if eid in seen_nodes:
                    continue
                seen_nodes.add(eid)
                labels = list(node.labels) if hasattr(node, "labels") else []
                props = _safe_props(dict(node))
                nt = _resolve_node_type(labels)
                label = props.pop("name", props.get("title", ""))
                risk = props.pop("risk_score", None)
                nodes.append(
                    GraphNode(
                        id=eid,
                        label=str(label),
                        type=nt,
                        properties=props,
                        risk_score=risk,
                    )
                )

            for rel in rec["sg_rels"]:
                eid = str(rel.element_id) if hasattr(rel, "element_id") else ""
                if eid in seen_edges:
                    continue
                seen_edges.add(eid)
                props = _safe_props(dict(rel))
                et = _resolve_edge_type(rel.type)
                src = (
                    str(rel.start_node.element_id) if hasattr(rel, "start_node") else ""
                )
                tgt = str(rel.end_node.element_id) if hasattr(rel, "end_node") else ""
                edges.append(
                    GraphEdge(
                        id=eid,
                        source=src,
                        target=tgt,
                        type=et,
                        properties=props,
                    )
                )

        return {"nodes": nodes, "edges": edges}

    async def get_stats(self) -> dict[str, Any]:
        node_labels = [nt.value for nt in NodeType]
        edge_types = [et.value for et in EdgeType]

        node_counts: dict[str, int] = {}
        edge_counts: dict[str, int] = {}
        total_nodes = 0
        total_edges = 0
        total_contract_value = 0.0
        min_date = None
        max_date = None

        async with self.driver.session() as session:
            for label in node_labels:
                result = await session.run(f"MATCH (n:{label}) RETURN count(n) as cnt")
                record = await result.single()
                cnt = record["cnt"] if record else 0
                node_counts[label] = cnt
                total_nodes += cnt

            for etype in edge_types:
                result = await session.run(
                    f"MATCH ()-[r:{etype}]->() RETURN count(r) as cnt"
                )
                record = await result.single()
                cnt = record["cnt"] if record else 0
                edge_counts[etype] = cnt
                total_edges += cnt

            result = await session.run(
                "MATCH (c:Contract) RETURN sum(c.amount) as total, "
                "min(c.award_date) as min_date, max(c.award_date) as max_date"
            )
            record = await result.single()
            if record:
                total_contract_value = float(record["total"] or 0)
                min_date = str(record["min_date"]) if record["min_date"] else None
                max_date = str(record["max_date"]) if record["max_date"] else None

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_counts": node_counts,
            "edge_counts": edge_counts,
            "total_contract_value": total_contract_value,
            "date_range": {"min": min_date, "max": max_date},
        }

    async def get_agency_concentration(self, agency_id: str) -> dict[str, Any] | None:
        query = """
        MATCH (a:Agency)
        WHERE elementId(a) = $agency_id
        OPTIONAL MATCH (a)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(con:Contractor)
        WITH a, con, sum(c.amount) as contractor_value, count(c) as contract_count
        WITH a,
             collect({
                 name: con.name,
                 id: elementId(con),
                 value: contractor_value,
                 contracts: contract_count
             }) as contractors,
             sum(contractor_value) as grand_total,
             sum(contract_count) as total_contracts
        UNWIND contractors as contractor
        WITH a, contractor, grand_total, total_contracts,
             CASE WHEN grand_total > 0
                  THEN (toFloat(contractor.value) / grand_total)
                  ELSE 0 END as share
        WITH a, grand_total, total_contracts,
             sum(share * share) as hhi,
             collect({
                 name: contractor.name,
                 id: contractor.id,
                 share: share,
                 value: contractor.value,
                 contracts: contractor.contracts
             }) as top_contractors
        RETURN a.name as agency_name,
               elementId(a) as agency_id,
               hhi,
               top_contractors,
               grand_total as total_value,
               total_contracts
        """
        async with self.driver.session() as session:
            result = await session.run(query, agency_id=agency_id)
            record = await result.single()
            if not record:
                return None

            rec = dict(record)

            # get procurement methods separately
            methods_query = """
            MATCH (a:Agency)-[:PROCURED]->(c:Contract)
            WHERE elementId(a) = $agency_id
            RETURN c.procurement_method as method, count(c) as count, sum(c.amount) as value
            ORDER BY count DESC
            """
            methods_result = await session.run(methods_query, agency_id=agency_id)
            methods = []
            async for mr in methods_result:
                mrd = dict(mr)
                methods.append(
                    {
                        "method": mrd["method"],
                        "count": mrd["count"],
                        "total_value": float(mrd["value"] or 0),
                    }
                )

            # sort contractors by value descending, take top 10
            sorted_contractors = sorted(
                rec["top_contractors"],
                key=lambda x: x.get("value", 0) or 0,
                reverse=True,
            )[:10]

            top_contractors = [
                {
                    "id": str(c.get("id", "")),
                    "name": c.get("name", ""),
                    "contract_count": int(c.get("contracts", 0) or 0),
                    "total_value": float(c.get("value", 0) or 0),
                    "share": float(c.get("share", 0) or 0),
                }
                for c in sorted_contractors
                if c.get("name") is not None
            ]

            return {
                "agency_id": str(rec["agency_id"]),
                "agency_name": rec["agency_name"],
                "hhi": float(rec["hhi"] or 0),
                "top_contractors": top_contractors,
                "procurement_methods": methods,
                "total_contracts": int(rec["total_contracts"] or 0),
                "total_value": float(rec["total_value"] or 0),
            }

    async def get_contractor_profile(self, contractor_id: str) -> dict[str, Any] | None:
        basic_query = """
        MATCH (con:Contractor)
        WHERE elementId(con) = $contractor_id
        OPTIONAL MATCH (c:Contract)-[:AWARDED_TO]->(con)
        WITH con, count(c) as wins, sum(c.amount) as total_value
        OPTIONAL MATCH (con)-[:BID_ON]->(b:Contract)
        WITH con, wins, total_value, count(b) as total_bids
        RETURN elementId(con) as contractor_id,
               con.name as name,
               con.registration_number as reg_number,
               con.classification as classification,
               wins as total_contracts,
               total_value,
               CASE WHEN total_bids > 0
                    THEN toFloat(wins) / total_bids
                    ELSE 0.0 END as win_rate
        """
        async with self.driver.session() as session:
            result = await session.run(basic_query, contractor_id=contractor_id)
            record = await result.single()
            if not record:
                return None
            rec = dict(record)

            # Per-agency contract stats (separate query avoids cartesian products)
            agencies_query = """
            MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(con:Contractor)
            WHERE elementId(con) = $contractor_id
            WITH a, count(c) as contract_count, sum(c.amount) as total_value
            RETURN a.name as name, elementId(a) as id, contract_count, total_value
            ORDER BY total_value DESC
            """
            agencies_result = await session.run(
                agencies_query, contractor_id=contractor_id
            )
            agencies = []
            async for ar in agencies_result:
                ard = dict(ar)
                agencies.append(
                    {
                        "id": str(ard["id"]),
                        "name": ard["name"],
                        "contract_count": int(ard["contract_count"] or 0),
                        "total_value": float(ard["total_value"] or 0),
                    }
                )

            # Co-bidder details from relationship properties
            co_bidders_query = """
            MATCH (con:Contractor)-[r:CO_BID_WITH]-(other:Contractor)
            WHERE elementId(con) = $contractor_id
            RETURN other.name as name, elementId(other) as id,
                   r.contract_count as co_bid_count, r.win_pattern as win_pattern
            ORDER BY r.contract_count DESC
            """
            co_bidders_result = await session.run(
                co_bidders_query, contractor_id=contractor_id
            )
            co_bidders = []
            async for cr in co_bidders_result:
                crd = dict(cr)
                co_bidders.append(
                    {
                        "id": str(crd["id"]),
                        "name": crd["name"],
                        "co_bid_count": int(crd["co_bid_count"] or 0),
                        "win_pattern": crd["win_pattern"] or "unknown",
                    }
                )

            return {
                "contractor_id": str(rec["contractor_id"]),
                "name": rec["name"],
                "registration_number": rec["reg_number"],
                "classification": rec["classification"],
                "total_contracts": int(rec["total_contracts"] or 0),
                "total_value": float(rec["total_value"] or 0),
                "agencies": agencies,
                "co_bidders": co_bidders,
                "win_rate": float(rec["win_rate"] or 0),
                "red_flags": [],
            }

    async def get_red_flags(
        self,
        severity: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        severity_clause = ""
        if severity:
            severity_clause = "AND rf.severity = $severity"

        query = f"""
        MATCH (n)-[:HAS_RED_FLAG]->(rf:RedFlag)
        WHERE true {severity_clause}
        RETURN n, elementId(n) as entity_id, labels(n) as labels,
               collect(rf) as flags, n.risk_score as risk_score
        ORDER BY risk_score DESC
        LIMIT $limit
        """
        params: dict[str, Any] = {"limit": limit}
        if severity:
            params["severity"] = severity

        results: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            async for record in result:
                rec = dict(record)
                node = rec["n"]
                props = dict(node)
                name = props.get("name", props.get("title", ""))
                node_type = _resolve_node_type(rec["labels"])

                flags = []
                for flag in rec["flags"]:
                    fp = dict(flag)
                    flags.append(
                        {
                            "type": fp.get("type", ""),
                            "severity": fp.get("severity", "medium"),
                            "description": fp.get("description", ""),
                            "evidence": fp.get("evidence", {}),
                            "detected_at": fp.get("detected_at"),
                        }
                    )

                results.append(
                    {
                        "entity_id": str(rec["entity_id"]),
                        "entity_name": str(name),
                        "entity_type": node_type.value,
                        "red_flags": flags,
                        "risk_score": float(rec["risk_score"] or 0),
                    }
                )

        return results

    async def get_community(self, community_id: str) -> dict[str, Any]:
        query = """
        MATCH (n)
        WHERE n.community_id = $community_id
        OPTIONAL MATCH (n)-[r]-(m)
        WHERE m.community_id = $community_id
        RETURN collect(DISTINCT n) as members,
               collect(DISTINCT r) as internal_edges
        """
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        seen_nodes: set[str] = set()
        seen_edges: set[str] = set()

        async with self.driver.session() as session:
            result = await session.run(query, community_id=community_id)
            record = await result.single()
            if not record:
                return {"nodes": nodes, "edges": edges, "summary": ""}

            rec = dict(record)
            for node in rec["members"]:
                eid = str(node.element_id) if hasattr(node, "element_id") else ""
                if eid in seen_nodes:
                    continue
                seen_nodes.add(eid)
                labels = list(node.labels) if hasattr(node, "labels") else []
                props = _safe_props(dict(node))
                nt = _resolve_node_type(labels)
                label = props.pop("name", props.get("title", ""))
                risk = props.pop("risk_score", None)
                nodes.append(
                    GraphNode(
                        id=eid,
                        label=str(label),
                        type=nt,
                        properties=props,
                        risk_score=risk,
                    )
                )

            for rel in rec.get("internal_edges", []):
                if rel is None:
                    continue
                eid = str(rel.element_id) if hasattr(rel, "element_id") else ""
                if eid in seen_edges:
                    continue
                seen_edges.add(eid)
                props = _safe_props(dict(rel))
                et = _resolve_edge_type(rel.type)
                src = (
                    str(rel.start_node.element_id) if hasattr(rel, "start_node") else ""
                )
                tgt = str(rel.end_node.element_id) if hasattr(rel, "end_node") else ""
                edges.append(
                    GraphEdge(
                        id=eid,
                        source=src,
                        target=tgt,
                        type=et,
                        properties=props,
                    )
                )

        # try to get community summary if it exists
        summary = ""
        async with self.driver.session() as session:
            sum_result = await session.run(
                "MATCH (cs:CommunitySummary {community_id: $cid}) RETURN cs.summary as summary",
                cid=community_id,
            )
            sum_record = await sum_result.single()
            if sum_record and sum_record["summary"]:
                summary = sum_record["summary"]

        return {"nodes": nodes, "edges": edges, "summary": summary}

    async def get_node_detail(self, node_id: str) -> dict[str, Any] | None:
        """Get a node with its neighbors and basic stats."""
        node = await self.get_node(node_id)
        if not node:
            return None

        neighbor_data = await self.get_neighbors(node_id, limit=50)

        # compute basic stats depending on node type
        stats: dict[str, Any] = {}
        async with self.driver.session() as session:
            if node.type == NodeType.CONTRACTOR:
                result = await session.run(
                    "MATCH (c:Contract)-[:AWARDED_TO]->(con) "
                    "WHERE elementId(con) = $nid "
                    "RETURN count(c) as contracts, sum(c.amount) as total_value",
                    nid=node_id,
                )
                rec = await result.single()
                if rec:
                    stats["total_contracts"] = rec["contracts"]
                    stats["total_value"] = float(rec["total_value"] or 0)

            elif node.type == NodeType.AGENCY:
                result = await session.run(
                    "MATCH (a:Agency)-[:PROCURED]->(c:Contract) "
                    "WHERE elementId(a) = $nid "
                    "RETURN count(c) as contracts, sum(c.amount) as total_value",
                    nid=node_id,
                )
                rec = await result.single()
                if rec:
                    stats["total_contracts"] = rec["contracts"]
                    stats["total_value"] = float(rec["total_value"] or 0)

            elif node.type == NodeType.POLITICIAN:
                result = await session.run(
                    "MATCH (p:Politician)-[:GOVERNS]->(m:Municipality) "
                    "WHERE elementId(p) = $nid "
                    "RETURN count(m) as municipalities",
                    nid=node_id,
                )
                rec = await result.single()
                if rec:
                    stats["municipalities_governed"] = rec["municipalities"]

        return {
            "node": node,
            "neighbors": neighbor_data["nodes"],
            "edges": neighbor_data["edges"],
            "stats": stats,
        }

    async def get_all_subcontract_cycles(
        self, max_depth: int = 6
    ) -> list[dict[str, Any]]:
        """Find all cycles in the subcontracting graph."""
        query = (
            """
        MATCH path = (start:Contractor)-[:SUBCONTRACTED_TO*2..%d]->(start)
        WITH path, [n IN nodes(path) | n.name] as contractor_names,
             [n IN nodes(path) | elementId(n)] as contractor_ids,
             length(path) as cycle_length
        RETURN contractor_names,
               contractor_ids,
               cycle_length
        ORDER BY cycle_length ASC
        LIMIT 100
        """
            % max_depth
        )

        cycles: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                rec = dict(record)
                cycles.append(
                    {
                        "contractors": rec["contractor_names"],
                        "contractor_ids": [str(cid) for cid in rec["contractor_ids"]],
                        "cycle_length": int(rec["cycle_length"]),
                    }
                )

        return cycles

    async def get_network_communities(
        self, min_connections: int = 3
    ) -> list[dict[str, Any]]:
        """Find densely connected clusters using Cypher-based community detection."""
        query = """
        MATCH (c1:Contractor)-[r:CO_BID_WITH]-(c2:Contractor)
        WHERE r.contract_count >= $min_connections
        OPTIONAL MATCH (c1)-[:SHARES_DIRECTOR_WITH]-(c2)
        WITH c1, c2, r.contract_count as co_bid_weight,
             CASE WHEN EXISTS { MATCH (c1)-[:SHARES_DIRECTOR_WITH]-(c2) } THEN 1 ELSE 0 END as director_weight
        WITH c1, c2, co_bid_weight + director_weight as total_weight
        WHERE total_weight >= $min_connections
        WITH collect(DISTINCT c1) + collect(DISTINCT c2) as all_contractors
        UNWIND all_contractors as contractor
        WITH DISTINCT contractor
        MATCH (contractor)-[r:CO_BID_WITH|SHARES_DIRECTOR_WITH]-(connected)
        WITH contractor, count(DISTINCT connected) as connection_count
        WHERE connection_count >= $min_connections
        WITH contractor, connection_count
        ORDER BY connection_count DESC
        LIMIT 50
        RETURN contractor.name as contractor_name,
               elementId(contractor) as contractor_id,
               connection_count
        """
        communities: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            result = await session.run(query, min_connections=min_connections)
            async for record in result:
                rec = dict(record)
                # get connected contractors for this node
                connected_query = """
                MATCH (c:Contractor)-[r:CO_BID_WITH|SHARES_DIRECTOR_WITH]-(connected:Contractor)
                WHERE elementId(c) = $contractor_id
                RETURN connected.name as name,
                       elementId(connected) as id,
                       type(r) as relationship_type
                LIMIT 20
                """
                connected_result = await session.run(
                    connected_query, contractor_id=rec["contractor_id"]
                )
                connected = []
                async for conn_rec in connected_result:
                    crd = dict(conn_rec)
                    connected.append(
                        {
                            "name": crd["name"],
                            "id": str(crd["id"]),
                            "relationship": crd["relationship_type"],
                        }
                    )

                communities.append(
                    {
                        "center_contractor": rec["contractor_name"],
                        "center_contractor_id": str(rec["contractor_id"]),
                        "connection_count": int(rec["connection_count"]),
                        "connected_entities": connected,
                    }
                )

        return communities

    async def get_multi_hop_paths(
        self,
        entity_id: str,
        min_hops: int = 3,
        max_hops: int = 6,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Find all interesting paths of length 3-6 from an entity, filtering for paths that cross multiple entity types."""
        query = """
        MATCH (start)
        WHERE elementId(start) = $entity_id
        MATCH path = (start)-[*%d..%d]-(end)
        WHERE start <> end
        WITH path,
             [n IN nodes(path) | labels(n)[0]] as node_types,
             [n IN nodes(path) | COALESCE(n.name, n.title, n.reference_number, '')] as node_labels,
             [n IN nodes(path) | elementId(n)] as node_ids,
             [r IN relationships(path) | type(r)] as rel_types,
             length(path) as path_length
        WITH path, node_types, node_labels, node_ids, rel_types, path_length,
             size([t IN node_types WHERE t IS NOT NULL]) as type_count,
             size(apoc.coll.toSet(node_types)) as unique_type_count
        WHERE unique_type_count >= 3
        RETURN node_types,
               node_labels,
               node_ids,
               rel_types,
               path_length
        ORDER BY unique_type_count DESC, path_length ASC
        LIMIT $limit
        """ % (min_hops, max_hops)

        # fallback if APOC not available
        fallback_query = """
        MATCH (start)
        WHERE elementId(start) = $entity_id
        MATCH path = (start)-[*%d..%d]-(end)
        WHERE start <> end
        WITH path,
             [n IN nodes(path) | labels(n)[0]] as node_types,
             [n IN nodes(path) | COALESCE(n.name, n.title, n.reference_number, '')] as node_labels,
             [n IN nodes(path) | elementId(n)] as node_ids,
             [r IN relationships(path) | type(r)] as rel_types,
             length(path) as path_length
        WITH path, node_types, node_labels, node_ids, rel_types, path_length,
             size([t IN node_types WHERE t IS NOT NULL]) as type_count
        RETURN node_types,
               node_labels,
               node_ids,
               rel_types,
               path_length
        ORDER BY path_length ASC
        LIMIT $limit
        """ % (min_hops, max_hops)

        paths: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            try:
                result = await session.run(query, entity_id=entity_id, limit=limit)
            except Exception:
                # fallback without APOC
                result = await session.run(
                    fallback_query, entity_id=entity_id, limit=limit
                )

            async for record in result:
                rec = dict(record)
                paths.append(
                    {
                        "node_types": rec["node_types"],
                        "node_labels": rec["node_labels"],
                        "node_ids": [str(nid) for nid in rec["node_ids"]],
                        "relationship_types": rec["rel_types"],
                        "path_length": int(rec["path_length"]),
                    }
                )

        return paths

    async def get_subcontract_cycles(self, contractor_id: str) -> list[dict[str, Any]]:
        """Find circular subcontracting paths involving a contractor."""
        query = """
        MATCH (target:Contractor)
        WHERE elementId(target) = $contractor_id
        MATCH path = (target)-[:SUBCONTRACTED_TO*2..6]->(target)
        WITH path,
             [n IN nodes(path) | n.name] as contractor_names,
             [n IN nodes(path) | elementId(n)] as contractor_ids,
             [r IN relationships(path) | r.amount] as subcontract_amounts,
             length(path) as cycle_length
        RETURN contractor_names,
               contractor_ids,
               subcontract_amounts,
               cycle_length
        ORDER BY cycle_length ASC
        LIMIT 50
        """
        cycles: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            result = await session.run(query, contractor_id=contractor_id)
            async for record in result:
                rec = dict(record)
                cycles.append(
                    {
                        "contractors": rec["contractor_names"],
                        "contractor_ids": [str(cid) for cid in rec["contractor_ids"]],
                        "subcontract_amounts": [
                            float(amt) if amt is not None else None
                            for amt in rec["subcontract_amounts"]
                        ],
                        "cycle_length": int(rec["cycle_length"]),
                    }
                )
        return cycles

    async def get_campaign_contract_paths(
        self, politician_id: str
    ) -> list[dict[str, Any]]:
        """Trace donation-to-contract paths for a specific politician."""
        query = """
        MATCH (pol:Politician)
        WHERE elementId(pol) = $politician_id
        MATCH path = (con:Contractor)-[:DONATED_TO]->(cd:CampaignDonation)-[:DONATED_TO]->(pol)-[:GOVERNS]->(m:Municipality)-[:HAS_AGENCY]->(a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(con)
        WITH con, pol, cd, a, c, path
        RETURN con.name as contractor_name,
               elementId(con) as contractor_id,
               cd.amount as donation_amount,
               cd.year as donation_year,
               c.reference_number as contract_ref,
               c.amount as contract_amount,
               c.award_date as contract_date,
               a.name as agency_name,
               elementId(a) as agency_id,
               length(path) as path_length
        ORDER BY cd.year DESC, c.award_date DESC
        LIMIT 100
        """
        paths: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            result = await session.run(query, politician_id=politician_id)
            async for record in result:
                rec = dict(record)
                paths.append(
                    {
                        "contractor_name": rec["contractor_name"],
                        "contractor_id": str(rec["contractor_id"]),
                        "donation_amount": float(rec["donation_amount"] or 0),
                        "donation_year": rec["donation_year"],
                        "contract_ref": rec["contract_ref"],
                        "contract_amount": float(rec["contract_amount"] or 0),
                        "contract_date": (
                            str(rec["contract_date"]) if rec["contract_date"] else None
                        ),
                        "agency_name": rec["agency_name"],
                        "agency_id": str(rec["agency_id"]),
                        "path_length": int(rec["path_length"]),
                    }
                )
        return paths

    async def get_phoenix_companies(self) -> list[dict[str, Any]]:
        """Find all potential phoenix company pairs."""
        query = """
        MATCH (old:Contractor)-[:BLACKLISTED]->(bl:BlacklistEntry)
        MATCH (old)-[rel:SHARES_DIRECTOR_WITH|SAME_ADDRESS_AS]-(new:Contractor)
        WHERE NOT EXISTS { MATCH (new)-[:BLACKLISTED]->() }
        RETURN old.name as old_company,
               elementId(old) as old_id,
               new.name as new_company,
               elementId(new) as new_id,
               type(rel) as relationship_type,
               bl.offense as offense,
               bl.sanction_date as blacklist_date,
               old.address as shared_address
        ORDER BY bl.sanction_date DESC
        LIMIT 100
        """
        companies: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                rec = dict(record)
                companies.append(
                    {
                        "old_company": rec["old_company"],
                        "old_company_id": str(rec["old_id"]),
                        "new_company": rec["new_company"],
                        "new_company_id": str(rec["new_id"]),
                        "relationship_type": rec["relationship_type"],
                        "offense": rec["offense"],
                        "blacklist_date": (
                            str(rec["blacklist_date"])
                            if rec["blacklist_date"]
                            else None
                        ),
                        "shared_attribute": (
                            rec["shared_address"]
                            if rec["relationship_type"] == "SAME_ADDRESS_AS"
                            else "director"
                        ),
                    }
                )
        return companies

    async def get_saln_timeline(self, politician_id: str) -> list[dict[str, Any]]:
        """Get SALN records over time for a politician."""
        query = """
        MATCH (p:Politician)-[:DECLARED_WEALTH]->(s:SALNRecord)
        WHERE elementId(p) = $politician_id
        RETURN s.year as year,
               s.net_worth as net_worth,
               s.real_property as real_property,
               s.personal_property as personal_property,
               s.liabilities as liabilities,
               s.assets as assets
        ORDER BY s.year ASC
        """
        timeline: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            result = await session.run(query, politician_id=politician_id)
            async for record in result:
                rec = dict(record)
                timeline.append(
                    {
                        "year": int(rec["year"]) if rec["year"] else None,
                        "net_worth": float(rec["net_worth"] or 0),
                        "real_property": float(rec["real_property"] or 0),
                        "personal_property": float(rec["personal_property"] or 0),
                        "liabilities": float(rec["liabilities"] or 0),
                        "assets": float(rec["assets"] or 0),
                    }
                )
        return timeline

    async def get_entity_contracts(
        self,
        entity_id: str,
        entity_type: str,
        counterpart_id: str | None = None,
        limit: int = 15,
    ) -> list[dict[str, Any]]:
        """Get contracts for an entity, optionally filtered to a specific counterpart."""
        if counterpart_id:
            # cross-entity: contracts between agency and contractor
            query = """
            MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(con:Contractor)
            WHERE elementId(a) = $agency_id AND elementId(con) = $contractor_id
            RETURN c.reference_number as reference_number, c.title as title,
                   c.amount as amount, c.procurement_method as procurement_method,
                   c.award_date as award_date, c.bid_count as bid_count,
                   c.status as status
            ORDER BY c.award_date DESC
            LIMIT $limit
            """
            params: dict[str, Any] = {
                "agency_id": entity_id,
                "contractor_id": counterpart_id,
                "limit": limit,
            }
        elif entity_type == "Agency":
            query = """
            MATCH (a:Agency)-[:PROCURED]->(c:Contract)
            WHERE elementId(a) = $entity_id
            OPTIONAL MATCH (c)-[:AWARDED_TO]->(con:Contractor)
            RETURN c.reference_number as reference_number, c.title as title,
                   c.amount as amount, c.procurement_method as procurement_method,
                   c.award_date as award_date, c.bid_count as bid_count,
                   c.status as status, con.name as counterparty_name
            ORDER BY c.amount DESC LIMIT $limit
            """
            params = {"entity_id": entity_id, "limit": limit}
        else:
            # Contractor (or fallback)
            query = """
            MATCH (c:Contract)-[:AWARDED_TO]->(con:Contractor)
            WHERE elementId(con) = $entity_id
            OPTIONAL MATCH (a:Agency)-[:PROCURED]->(c)
            RETURN c.reference_number as reference_number, c.title as title,
                   c.amount as amount, c.procurement_method as procurement_method,
                   c.award_date as award_date, c.bid_count as bid_count,
                   c.status as status, a.name as counterparty_name
            ORDER BY c.amount DESC LIMIT $limit
            """
            params = {"entity_id": entity_id, "limit": limit}

        contracts: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            async for record in result:
                rec = _safe_props(dict(record))
                contracts.append(
                    {
                        "reference_number": rec.get("reference_number"),
                        "title": rec.get("title"),
                        "amount": float(rec.get("amount") or 0),
                        "procurement_method": rec.get("procurement_method"),
                        "award_date": rec.get("award_date"),
                        "bid_count": int(rec.get("bid_count") or 0),
                        "status": rec.get("status"),
                        "counterparty_name": rec.get("counterparty_name"),
                    }
                )
        return contracts

    async def get_entity_audit_findings(
        self,
        entity_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get COA audit findings for an entity."""
        query = """
        MATCH (a)-[:AUDITED]->(af:AuditFinding)
        WHERE elementId(a) = $entity_id
        RETURN af.type as type, af.severity as severity,
               af.description as description, af.amount as amount,
               af.year as year, af.recommendation as recommendation,
               af.recommendation_status as recommendation_status
        ORDER BY af.year DESC, af.severity DESC LIMIT $limit
        """
        findings: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            result = await session.run(query, entity_id=entity_id, limit=limit)
            async for record in result:
                rec = dict(record)
                findings.append(
                    {
                        "type": rec.get("type"),
                        "severity": rec.get("severity"),
                        "description": rec.get("description"),
                        "amount": float(rec.get("amount") or 0),
                        "year": rec.get("year"),
                        "recommendation": rec.get("recommendation"),
                        "recommendation_status": str(
                            rec.get("recommendation_status") or ""
                        ),
                    }
                )
        return findings
