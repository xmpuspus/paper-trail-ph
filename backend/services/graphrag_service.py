from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from backend.services.llm_service import LLMService
from backend.services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Philippine public accountability analyst. You answer questions about
government procurement, political connections, and audit findings using data from the paper-trail-ph
knowledge graph.

Rules:
- Ground every claim in the provided graph context. Cite specific entities, contracts, and amounts.
- Reference specific contract reference numbers, contractor names, and peso amounts when available.
- All monetary amounts are in Philippine Pesos (PHP).
- Red flags are statistical indicators, not accusations of wrongdoing.
- Be precise with numbers. Don't round unless asked.
- If the graph context doesn't contain enough information to answer, say so clearly.
- Keep answers concise but complete.
- The graph now includes campaign donation records (COMELEC SOCE data), blacklist entries,
  SALN wealth declarations, and subcontracting relationships.
- When discussing SALN data, note that these are public records filed annually by all government officials.
- Campaign donations are from COMELEC Statement of Contributions and Expenses (SOCE).
- Blacklist entries are from the GPPB consolidated blacklisting records."""

INTENT_PROMPT = """Classify this user question into exactly one category. Respond with ONLY the category name.

Categories:
- entity_lookup: Questions about a specific entity (person, agency, contractor, etc.)
- relationship_query: Questions about connections between two entities
- analytical: Questions requiring aggregation, ranking, statistics, or red flag analysis
- open_ended: General questions, summaries, or broad exploratory queries

Question: {question}

Category:"""

ENTITY_EXTRACT_PROMPT = """Extract all entity names (agencies, contractors, people, regions, places) from this question.
Return ONLY a JSON array of strings. If no entities found, return [].

Question: {question}

Entities:"""


DATA_SOURCES = {
    "philgeps": "https://open.philgeps.gov.ph",
    "comelec": "https://comelec.gov.ph",
    "coa": "https://coa.gov.ph/reports/annual-audit-reports",
    "gppb": "https://www.gppb.gov.ph",
    "ombudsman": "https://www.ombudsman.gov.ph",
    "psa": "https://psa.gov.ph/classification/psgc",
    "congress": "https://open-congress-api.bettergov.ph",
}


def _determine_sources(context: str) -> list[str]:
    """Map answer context to actual government data source URLs."""
    sources = [DATA_SOURCES["philgeps"]]
    lower = context.lower()
    if "audit" in lower or "coa" in lower:
        sources.append(DATA_SOURCES["coa"])
    if "saln" in lower or "net worth" in lower or "wealth declaration" in lower:
        sources.append(DATA_SOURCES["ombudsman"])
    if "campaign" in lower or "donation" in lower or "soce" in lower:
        sources.append(DATA_SOURCES["comelec"])
    if "blacklist" in lower:
        sources.append(DATA_SOURCES["gppb"])
    if "bill" in lower or "congress" in lower or "legislat" in lower:
        sources.append(DATA_SOURCES["congress"])
    return sources


class GraphRAGService:
    def __init__(self, neo4j_service: Neo4jService, llm_service: LLMService) -> None:
        self.neo4j = neo4j_service
        self.llm = llm_service

    async def classify_intent(self, question: str) -> str:
        result = await self.llm.generate(
            INTENT_PROMPT.format(question=question),
            max_tokens=20,
        )
        intent = result.strip().lower().replace('"', "").replace("'", "")
        valid = {"entity_lookup", "relationship_query", "analytical", "open_ended"}
        if intent not in valid:
            q = question.lower()
            if any(
                w in q
                for w in [
                    "connect",
                    "path",
                    "link",
                    "between",
                    "relationship",
                    "donate",
                    "alliance",
                    "ally",
                ]
            ):
                return "relationship_query"
            if any(
                w in q
                for w in [
                    "top",
                    "most",
                    "highest",
                    "risk",
                    "flag",
                    "hhi",
                    "concentration",
                    "bid",
                    "pattern",
                    "campaign",
                    "donation",
                    "saln",
                    "wealth",
                    "blacklist",
                    "phoenix",
                    "subcontract",
                    "circular",
                    "shell",
                ]
            ):
                return "analytical"
            if any(w in q for w in ["who is", "what is", "tell me about", "show me"]):
                return "entity_lookup"
            return "open_ended"
        return intent

    async def _extract_entities(self, question: str) -> list[str]:
        """Use LLM to extract entity names from a question."""
        try:
            raw = await self.llm.generate(
                ENTITY_EXTRACT_PROMPT.format(question=question),
                max_tokens=200,
            )
            entities = json.loads(raw.strip())
            if isinstance(entities, list):
                return [str(e).strip() for e in entities if e]
        except (json.JSONDecodeError, Exception):
            pass
        return []

    async def _gather_entity_context(self, entities: list[str]) -> list[str]:
        """Search for entities and gather deep context for each."""
        context_parts: list[str] = []
        agency_hits: list[tuple[str, str]] = []  # (id, label)
        contractor_hits: list[tuple[str, str]] = []

        for entity_name in entities[:5]:
            results = await self.neo4j.search(entity_name, limit=3)
            if not results:
                continue

            for sr in results[:2]:
                detail = await self.neo4j.get_node_detail(sr.id)
                if not detail:
                    continue

                context_parts.append(_format_node_context(detail))

                node = detail["node"]
                node_type = node.type.value

                if node_type == "Agency":
                    agency_hits.append((sr.id, node.label))
                    try:
                        conc = await self.neo4j.get_agency_concentration(sr.id)
                        if conc:
                            context_parts.append(_format_agency_analytics(conc))
                    except Exception:
                        pass
                elif node_type == "Contractor":
                    contractor_hits.append((sr.id, node.label))
                    try:
                        profile = await self.neo4j.get_contractor_profile(sr.id)
                        if profile:
                            context_parts.append(_format_contractor_analytics(profile))
                    except Exception:
                        pass
                elif node.type.value == "Politician":
                    # SALN timeline
                    try:
                        saln_query = """
                        MATCH (p:Politician)-[:DECLARED_WEALTH]->(s:SALNRecord)
                        WHERE elementId(p) = $pid
                        RETURN s.year as year, s.net_worth as net_worth,
                               s.real_property as real_property,
                               s.personal_property as personal_property
                        ORDER BY s.year
                        """
                        async with self.neo4j.driver.session() as session:
                            result = await session.run(saln_query, pid=sr.id)
                            saln_records = []
                            async for rec in result:
                                r = dict(rec)
                                saln_records.append(r)
                            if saln_records:
                                saln_text = _format_saln_timeline(
                                    saln_records, node.label
                                )
                                context_parts.append(saln_text)
                    except Exception:
                        pass

                    # Campaign donations received
                    try:
                        donation_query = """
                        MATCH (con:Contractor)-[:DONATED_TO]->(d:CampaignDonation)-[:DONATED_TO]->(p:Politician)
                        WHERE elementId(p) = $pid
                        RETURN con.name as donor, d.amount as amount, d.election_year as year
                        """
                        async with self.neo4j.driver.session() as session:
                            result = await session.run(donation_query, pid=sr.id)
                            donations = []
                            async for rec in result:
                                r = dict(rec)
                                donations.append(r)
                            if donations:
                                donation_text = _format_campaign_donations(
                                    donations, node.label
                                )
                                context_parts.append(donation_text)
                    except Exception:
                        pass

                # contract-level detail
                try:
                    contracts = await self.neo4j.get_entity_contracts(sr.id, node_type)
                    formatted = _format_contracts(contracts, node.label)
                    if formatted:
                        context_parts.append(formatted)
                except Exception:
                    pass

                # audit findings
                try:
                    findings = await self.neo4j.get_entity_audit_findings(sr.id)
                    formatted = _format_audit_findings(findings, node.label)
                    if formatted:
                        context_parts.append(formatted)
                except Exception:
                    pass

        # cross-entity contracts between agencies and contractors found above
        for ag_id, ag_name in agency_hits:
            for con_id, con_name in contractor_hits:
                try:
                    cross = await self.neo4j.get_entity_contracts(
                        ag_id, "Agency", counterpart_id=con_id
                    )
                    formatted = _format_cross_entity_contracts(cross, ag_name, con_name)
                    if formatted:
                        context_parts.append(formatted)
                except Exception:
                    pass

        return context_parts

    async def entity_lookup(self, question: str) -> dict[str, Any]:
        extract_prompt = (
            "Extract the main entity name being asked about from this question. "
            "Return ONLY the entity name, nothing else.\n\n"
            f"Question: {question}\n\nEntity name:"
        )
        entity_name = (await self.llm.generate(extract_prompt, max_tokens=50)).strip()

        results = await self.neo4j.search(entity_name, limit=5)
        if not results:
            return {
                "answer_context": f"No entity found matching '{entity_name}'.",
                "graph_data": None,
            }

        top = results[0]
        detail = await self.neo4j.get_node_detail(top.id)
        if not detail:
            return {
                "answer_context": f"Found '{top.name}' but could not load details.",
                "graph_data": None,
            }

        context_parts = [_format_node_context(detail)]

        # pull analytics based on type
        node = detail["node"]
        if node.type.value == "Agency":
            try:
                conc = await self.neo4j.get_agency_concentration(top.id)
                if conc:
                    context_parts.append(_format_agency_analytics(conc))
            except Exception:
                pass
        elif node.type.value == "Contractor":
            try:
                profile = await self.neo4j.get_contractor_profile(top.id)
                if profile:
                    context_parts.append(_format_contractor_analytics(profile))
            except Exception:
                pass
        elif node.type.value == "Politician":
            # SALN timeline
            try:
                saln_query = """
                MATCH (p:Politician)-[:DECLARED_WEALTH]->(s:SALNRecord)
                WHERE elementId(p) = $pid
                RETURN s.year as year, s.net_worth as net_worth,
                       s.real_property as real_property,
                       s.personal_property as personal_property
                ORDER BY s.year
                """
                async with self.neo4j.driver.session() as session:
                    result = await session.run(saln_query, pid=top.id)
                    saln_records = []
                    async for rec in result:
                        r = dict(rec)
                        saln_records.append(r)
                    if saln_records:
                        saln_text = _format_saln_timeline(saln_records, node.label)
                        context_parts.append(saln_text)
            except Exception:
                pass

            # Campaign donations received
            try:
                donation_query = """
                MATCH (con:Contractor)-[:DONATED_TO]->(d:CampaignDonation)-[:DONATED_TO]->(p:Politician)
                WHERE elementId(p) = $pid
                RETURN con.name as donor, d.amount as amount, d.election_year as year
                """
                async with self.neo4j.driver.session() as session:
                    result = await session.run(donation_query, pid=top.id)
                    donations = []
                    async for rec in result:
                        r = dict(rec)
                        donations.append(r)
                    if donations:
                        donation_text = _format_campaign_donations(
                            donations, node.label
                        )
                        context_parts.append(donation_text)
            except Exception:
                pass

        # contract-level detail
        try:
            contracts = await self.neo4j.get_entity_contracts(top.id, node.type.value)
            formatted = _format_contracts(contracts, node.label)
            if formatted:
                context_parts.append(formatted)
        except Exception:
            pass

        # audit findings
        try:
            findings = await self.neo4j.get_entity_audit_findings(top.id)
            formatted = _format_audit_findings(findings, node.label)
            if formatted:
                context_parts.append(formatted)
        except Exception:
            pass

        return {
            "answer_context": "\n\n".join(context_parts),
            "graph_data": detail,
        }

    async def relationship_query(self, question: str) -> dict[str, Any]:
        extract_prompt = (
            "Extract the two entity names from this question about a relationship or connection. "
            "Return them as a JSON array of two strings.\n\n"
            f"Question: {question}\n\nEntities:"
        )
        raw = (await self.llm.generate(extract_prompt, max_tokens=100)).strip()
        try:
            entities = json.loads(raw)
        except json.JSONDecodeError:
            parts = [p.strip().strip('"').strip("'") for p in raw.split(",")]
            entities = parts[:2] if len(parts) >= 2 else [raw, ""]

        if len(entities) < 2:
            return {
                "answer_context": "Could not identify two entities in the question.",
                "graph_data": None,
            }

        results1 = await self.neo4j.search(entities[0], limit=1)
        results2 = await self.neo4j.search(entities[1], limit=1)

        if not results1 or not results2:
            missing = entities[0] if not results1 else entities[1]
            return {
                "answer_context": f"Could not find entity: {missing}",
                "graph_data": None,
            }

        path = await self.neo4j.get_path(results1[0].id, results2[0].id)
        if not path:
            return {
                "answer_context": (
                    f"No path found between {results1[0].name} and {results2[0].name} "
                    f"within 6 hops."
                ),
                "graph_data": None,
            }

        context = _format_path_context(path, results1[0].name, results2[0].name)
        return {"answer_context": context, "graph_data": path}

    async def analytical_query(self, question: str) -> dict[str, Any]:
        q = question.lower()
        context_parts: list[str] = []

        # always extract entities and gather their data
        entities = await self._extract_entities(question)
        if entities:
            entity_context = await self._gather_entity_context(entities)
            context_parts.extend(entity_context)

        if any(w in q for w in ["concentration", "hhi", "monopol"]):
            stats = await self.neo4j.get_stats()
            context_parts.append(
                f"Graph contains {stats['total_nodes']} nodes and {stats['total_edges']} edges. "
                f"Total contract value: PHP {stats['total_contract_value']:,.2f}."
            )

        if any(
            w in q
            for w in [
                "red flag",
                "risk",
                "anomaly",
                "suspicious",
                "bid-rigging",
                "bid rigging",
                "collusion",
                "pattern",
                "single bidder",
                "single-bidder",
            ]
        ):
            # pull red flags from RedFlagService via app state
            # (handled by the caller if available, or fall back to stats)
            stats = await self.neo4j.get_stats()
            context_parts.append(
                f"Graph statistics: {stats['total_nodes']} nodes, {stats['total_edges']} edges, "
                f"PHP {stats['total_contract_value']:,.2f} total contract value."
            )

        if any(w in q for w in ["stat", "overview", "summary", "total"]):
            stats = await self.neo4j.get_stats()
            context_parts.append(
                f"Graph statistics:\n"
                f"- Total nodes: {stats['total_nodes']}\n"
                f"- Total edges: {stats['total_edges']}\n"
                f"- Node types: {json.dumps(stats['node_counts'])}\n"
                f"- Total contract value: PHP {stats['total_contract_value']:,.2f}\n"
                f"- Date range: {stats['date_range']}"
            )

        if not context_parts:
            stats = await self.neo4j.get_stats()
            context_parts.append(
                f"Graph has {stats['total_nodes']} nodes, {stats['total_edges']} edges, "
                f"PHP {stats['total_contract_value']:,.2f} in contracts."
            )

        return {"answer_context": "\n\n".join(context_parts), "graph_data": None}

    def _build_messages(
        self,
        full_context: str,
        question: str,
        history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        """Build message list with conversation history."""
        messages: list[dict[str, str]] = []

        if history:
            # include last 10 messages for context
            for msg in history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # if last message is already the current question from history, just
        # prepend context to it; otherwise append as new user message
        context_block = (
            f"Graph context:\n{full_context}\n\n"
            f"Answer the question using the graph context above."
        )

        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] = context_block + "\n\n" + messages[-1]["content"]
        else:
            messages.append(
                {"role": "user", "content": f"{context_block}\n\nQuestion: {question}"}
            )

        return messages

    async def answer(
        self,
        question: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intent = await self.classify_intent(question)
        logger.info("GraphRAG intent: %s for question: %s", intent, question[:80])

        if intent == "entity_lookup":
            result = await self.entity_lookup(question)
        elif intent == "relationship_query":
            result = await self.relationship_query(question)
        elif intent == "analytical":
            result = await self.analytical_query(question)
        else:
            result = await self.analytical_query(question)

        extra_context = ""
        if context and context.get("focused_node_id"):
            detail = await self.neo4j.get_node_detail(context["focused_node_id"])
            if detail:
                extra_context = (
                    f"\n\nCurrently focused entity:\n{_format_node_context(detail)}"
                )

        full_context = result["answer_context"] + extra_context

        prompt = (
            f"Graph context:\n{full_context}\n\n"
            f"User question: {question}\n\n"
            f"Answer the question using the graph context above."
        )
        answer_text = await self.llm.generate(prompt, system=SYSTEM_PROMPT)

        return {
            "answer": answer_text,
            "intent": intent,
            "graph_context": result.get("graph_data"),
            "sources": _determine_sources(full_context),
        }

    async def answer_stream(
        self,
        question: str,
        context: dict[str, Any] | None = None,
        history: list[dict[str, str]] | None = None,
        api_key: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        intent = await self.classify_intent(question)
        logger.info(
            "GraphRAG stream intent: %s for question: %s", intent, question[:80]
        )

        if intent == "entity_lookup":
            result = await self.entity_lookup(question)
        elif intent == "relationship_query":
            result = await self.relationship_query(question)
        elif intent == "analytical":
            result = await self.analytical_query(question)
        else:
            result = await self.analytical_query(question)

        extra_context = ""
        if context and context.get("focused_node_id"):
            detail = await self.neo4j.get_node_detail(context["focused_node_id"])
            if detail:
                extra_context = (
                    f"\n\nCurrently focused entity:\n{_format_node_context(detail)}"
                )

        full_context = result["answer_context"] + extra_context

        # use conversation history if available
        if history:
            messages = self._build_messages(full_context, question, history)
            async for token in self.llm.stream_messages(
                messages, system=SYSTEM_PROMPT, api_key=api_key
            ):
                yield {"event": "token", "data": json.dumps({"content": token})}
        else:
            prompt = (
                f"Graph context:\n{full_context}\n\n"
                f"User question: {question}\n\n"
                f"Answer the question using the graph context above."
            )
            async for token in self.llm.stream(
                prompt, system=SYSTEM_PROMPT, api_key=api_key
            ):
                yield {"event": "token", "data": json.dumps({"content": token})}

        graph_data = result.get("graph_data")
        yield {
            "event": "done",
            "data": json.dumps(
                {
                    "intent": intent,
                    "graph_context": _serialize_graph_data(graph_data),
                    "sources": _determine_sources(full_context),
                }
            ),
        }


def _format_node_context(detail: dict[str, Any]) -> str:
    node = detail["node"]
    lines = [
        f"Entity: {node.label} (Type: {node.type.value})",
        f"Properties: {json.dumps(node.properties, default=str)}",
    ]
    if node.risk_score is not None:
        lines.append(f"Risk score: {node.risk_score}")

    stats = detail.get("stats", {})
    if stats:
        lines.append(f"Stats: {json.dumps(stats, default=str)}")

    neighbors = detail.get("neighbors", [])
    if neighbors:
        neighbor_summary = ", ".join(
            f"{n.label} ({n.type.value})" for n in neighbors[:15]
        )
        lines.append(f"Connected to: {neighbor_summary}")
        if len(neighbors) > 15:
            lines.append(f"  ... and {len(neighbors) - 15} more connections")

    # include edge/relationship details
    edges = detail.get("edges", [])
    if edges:
        edge_lines = []
        for e in edges[:20]:
            edge_lines.append(f"  {e.source} --[{e.type.value}]--> {e.target}")
        lines.append("Relationships:\n" + "\n".join(edge_lines))

    return "\n".join(lines)


def _format_agency_analytics(conc: dict[str, Any]) -> str:
    lines = [
        f"Agency Analytics for {conc['agency_name']}:",
        f"  HHI (concentration): {conc['hhi']:.3f}",
        f"  Total contracts: {conc['total_contracts']}",
        f"  Total value: PHP {conc['total_value']:,.2f}",
    ]
    for c in conc.get("top_contractors", [])[:5]:
        share = c.get("share", 0)
        lines.append(
            f"  - {c.get('name', 'Unknown')}: {share:.1%} share, "
            f"PHP {c.get('value', 0):,.2f}"
        )
    methods = conc.get("procurement_methods", [])
    if methods:
        lines.append("  Procurement methods:")
        for m in methods[:5]:
            lines.append(
                f"    - {m['method']}: {m['count']} contracts, PHP {m.get('total_value', 0):,.2f}"
            )
    return "\n".join(lines)


def _format_contractor_analytics(profile: dict[str, Any]) -> str:
    lines = [
        f"Contractor Profile: {profile.get('name', profile.get('contractor_name', 'Unknown'))}",
        f"  Total contracts won: {profile['total_contracts']}",
        f"  Total value: PHP {profile['total_value']:,.2f}",
        f"  Win rate: {profile['win_rate']:.1%}",
    ]
    agencies = profile.get("agencies", [])
    if agencies:
        lines.append(f"  Works with {len(agencies)} agencies:")
        for a in agencies[:5]:
            lines.append(f"    - {a.get('name', 'Unknown')}")
    co_bidders = profile.get("co_bidders", [])
    if co_bidders:
        lines.append(f"  Co-bidders ({len(co_bidders)}):")
        for b in co_bidders[:5]:
            lines.append(f"    - {b.get('name', 'Unknown')}")
    return "\n".join(lines)


def _format_contracts(contracts: list[dict[str, Any]], entity_name: str) -> str:
    """Format contract list for LLM context."""
    if not contracts:
        return ""
    lines = [f"Contracts for {entity_name} ({len(contracts)} shown):"]
    for c in contracts:
        amount = float(c.get("amount", 0) or 0)
        counterparty = c.get("counterparty_name", "Unknown")
        lines.append(
            f"  - {c.get('reference_number', 'N/A')}: {c.get('title', 'N/A')}"
            f"\n    Amount: PHP {amount:,.2f} | Method: {c.get('procurement_method', 'N/A')}"
            f" | Date: {c.get('award_date', 'N/A')} | Bids: {c.get('bid_count', 'N/A')}"
            f" | Status: {c.get('status', 'N/A')} | {counterparty}"
        )
    return "\n".join(lines)


def _format_cross_entity_contracts(
    contracts: list[dict[str, Any]], agency_name: str, contractor_name: str
) -> str:
    """Format contracts between a specific agency and contractor."""
    if not contracts:
        return f"No direct contracts found between {agency_name} and {contractor_name}."
    total = sum(float(c.get("amount", 0) or 0) for c in contracts)
    lines = [
        f"Contracts between {agency_name} and {contractor_name} "
        f"({len(contracts)} contracts, total PHP {total:,.2f}):"
    ]
    for c in contracts:
        amount = float(c.get("amount", 0) or 0)
        lines.append(
            f"  - {c.get('reference_number', 'N/A')}: {c.get('title', 'N/A')}"
            f"\n    PHP {amount:,.2f} | {c.get('procurement_method', 'N/A')}"
            f" | {c.get('award_date', 'N/A')} | {c.get('bid_count', 'N/A')} bidders"
        )
    return "\n".join(lines)


def _format_audit_findings(findings: list[dict[str, Any]], entity_name: str) -> str:
    """Format COA audit findings for LLM context."""
    if not findings:
        return ""
    lines = [f"COA Audit Findings for {entity_name} ({len(findings)}):"]
    for f in findings:
        amount = float(f.get("amount", 0) or 0)
        lines.append(
            f"  - [{f.get('severity', 'N/A').upper()}] {f.get('type', 'N/A')}: "
            f"{f.get('description', 'N/A')}"
            f"\n    Amount: PHP {amount:,.2f} | Year: {f.get('year', 'N/A')}"
            f" | Status: {f.get('recommendation_status', 'N/A')}"
        )
    return "\n".join(lines)


def _format_path_context(
    path: dict[str, Any],
    name1: str,
    name2: str,
) -> str:
    nodes = path["nodes"]
    edges = path["edges"]
    length = path["length"]

    lines = [f"Path from {name1} to {name2} ({length} hops):"]
    for i, node in enumerate(nodes):
        prefix = "  " + ("-> " if i > 0 else "   ")
        lines.append(f"{prefix}{node.label} ({node.type.value})")
        if i < len(edges):
            lines.append(f"     --[{edges[i].type.value}]-->")

    return "\n".join(lines)


def _format_saln_timeline(records: list[dict], entity_name: str) -> str:
    """Format SALN records for LLM context."""
    if not records:
        return ""
    lines = [
        f"SALN (Statement of Assets, Liabilities and Net Worth) for {entity_name}:"
    ]
    for r in records:
        nw = float(r.get("net_worth", 0) or 0)
        rp = float(r.get("real_property", 0) or 0)
        pp = float(r.get("personal_property", 0) or 0)
        lines.append(
            f"  - Year {r.get('year', 'N/A')}: Net worth PHP {nw:,.2f}"
            f" (Real property: PHP {rp:,.2f}, Personal: PHP {pp:,.2f})"
        )
    if len(records) >= 2:
        first_nw = float(records[0].get("net_worth", 0) or 0)
        last_nw = float(records[-1].get("net_worth", 0) or 0)
        if first_nw > 0:
            growth = ((last_nw - first_nw) / first_nw) * 100
            years = int(records[-1].get("year", 0)) - int(records[0].get("year", 0))
            lines.append(f"  Net worth change: {growth:+.1f}% over {years} years")
    return "\n".join(lines)


def _format_campaign_donations(donations: list[dict], entity_name: str) -> str:
    """Format campaign donation data for LLM context."""
    if not donations:
        return ""
    lines = [f"Campaign donations received by {entity_name}:"]
    total = 0.0
    for d in donations:
        amt = float(d.get("amount", 0) or 0)
        total += amt
        lines.append(
            f"  - {d.get('donor', 'Unknown')}: PHP {amt:,.2f} ({d.get('year', 'N/A')} election)"
        )
    lines.append(f"  Total campaign donations from contractors: PHP {total:,.2f}")
    return "\n".join(lines)


def _serialize_graph_data(data: Any) -> Any:
    """Convert graph data to JSON-safe format."""
    if data is None:
        return None
    if hasattr(data, "model_dump"):
        return data.model_dump(mode="json")
    if isinstance(data, dict):
        return {k: _serialize_graph_data(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_serialize_graph_data(item) for item in data]
    return data
