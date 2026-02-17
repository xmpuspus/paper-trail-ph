"""Bidding network analysis.

Detects coordinated bidding patterns: co-bidding rings, subcontracting
loops, and contractors sharing registered addresses or officers.
"""

import asyncio
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    setup_logging,
)

logger = setup_logging("networks")


class NetworkAnalyzer:
    """Bidding network and collusion pattern detection."""

    def __init__(self):
        self.driver: AsyncDriver | None = None

    async def connect(self) -> None:
        self.driver = AsyncGraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        await self.driver.verify_connectivity()

    async def close(self) -> None:
        if self.driver:
            await self.driver.close()

    async def co_bidding_pairs(self) -> list[dict[str, Any]]:
        """Contractor pairs that repeatedly bid on the same projects."""
        query = """
        MATCH (co1:Contractor)-[cb:CO_BID_WITH]-(co2:Contractor)
        WHERE id(co1) < id(co2)
        RETURN co1.name AS contractor_a, co2.name AS contractor_b,
               cb.shared_contracts AS shared_contracts,
               cb.pattern AS pattern
        ORDER BY cb.shared_contracts DESC
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def co_bidding_triads(self) -> list[dict[str, Any]]:
        """Three-way co-bidding rings (closed triangles).

        When three contractors all co-bid with each other, it suggests
        coordinated bid rotation rather than coincidence.
        """
        query = """
        MATCH (a:Contractor)-[:CO_BID_WITH]-(b:Contractor)-[:CO_BID_WITH]-(c:Contractor)-[:CO_BID_WITH]-(a)
        WHERE id(a) < id(b) AND id(b) < id(c)
        RETURN a.name AS contractor_a, b.name AS contractor_b, c.name AS contractor_c
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def subcontracting_loops(self) -> list[dict[str, Any]]:
        """Contractors that subcontract to each other (circular money flow)."""
        query = """
        MATCH (a:Contractor)-[:SUBCONTRACTED_TO]->(b:Contractor)-[:SUBCONTRACTED_TO]->(a)
        WHERE id(a) < id(b)
        OPTIONAL MATCH (a)-[:OWNED_BY]->(pa:Person)
        OPTIONAL MATCH (b)-[:OWNED_BY]->(pb:Person)
        RETURN a.name AS contractor_a, b.name AS contractor_b,
               pa.name AS owner_a, pb.name AS owner_b
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def shared_entities(self) -> list[dict[str, Any]]:
        """Contractors sharing addresses or officers.

        Companies that share a physical address or a corporate officer
        while bidding against each other on the same contracts.
        """
        query = """
        MATCH (a:Contractor)-[r:ASSOCIATED_WITH]-(b:Contractor)
        WHERE id(a) < id(b)
        RETURN a.name AS contractor_a, b.name AS contractor_b,
               r.type AS association_type,
               a.address AS address_a, b.address AS address_b,
               r.shared_officer AS shared_officer
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def most_connected(self, limit: int = 20) -> list[dict[str, Any]]:
        """Entities with the most graph connections (degree centrality)."""
        query = """
        MATCH (n)-[r]-(m)
        WITH n, labels(n)[0] AS label, COUNT(DISTINCT m) AS connections
        ORDER BY connections DESC
        LIMIT $limit
        RETURN n.name AS name, label, connections
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query, limit=limit)
            return await result.data()

    async def agency_contractor_clusters(self) -> list[dict[str, Any]]:
        """Agencies dominated by tightly connected contractor groups.

        Finds agencies where the winning contractors are also connected
        to each other through co-bidding or association edges.
        """
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(co:Contractor)
        WHERE c.amount IS NOT NULL
        WITH a, co, SUM(c.amount) AS total
        WITH a, COLLECT({contractor: co.name, amount: total}) AS winners
        WHERE SIZE(winners) >= 2
        UNWIND winners AS w1
        UNWIND winners AS w2
        WITH a, w1, w2, winners
        WHERE w1.contractor < w2.contractor
        OPTIONAL MATCH (c1:Contractor {name: w1.contractor})-[r:CO_BID_WITH|ASSOCIATED_WITH]-(c2:Contractor {name: w2.contractor})
        WITH a, winners, COLLECT(DISTINCT {
            pair: [w1.contractor, w2.contractor],
            linked: r IS NOT NULL,
            rel: type(r)
        }) AS pairs
        WITH a, winners,
             [p IN pairs WHERE p.linked | p] AS linked_pairs
        WHERE SIZE(linked_pairs) > 0
        RETURN a.name AS agency, winners, linked_pairs
        ORDER BY SIZE(linked_pairs) DESC
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def run_all(self) -> dict[str, Any]:
        logger.info("Running network analysis")
        return {
            "co_bidding": await self.co_bidding_pairs(),
            "triads": await self.co_bidding_triads(),
            "loops": await self.subcontracting_loops(),
            "shared_entities": await self.shared_entities(),
            "most_connected": await self.most_connected(),
            "clusters": await self.agency_contractor_clusters(),
        }

    def print_report(self, results: dict[str, Any]) -> None:
        print("\n" + "=" * 80)
        print("BIDDING NETWORK ANALYSIS")
        print("=" * 80)

        # Co-bidding pairs
        pairs = results.get("co_bidding", [])
        if pairs:
            print(f"\nCo-Bidding Pairs ({len(pairs)}):")
            for p in pairs:
                contracts = p.get("shared_contracts", "?")
                pattern = p.get("pattern", "")
                print(
                    f"  {p['contractor_a']}  <->  {p['contractor_b']}"
                    f"  ({contracts} shared contracts, {pattern})"
                )

        # Triads
        triads = results.get("triads", [])
        if triads:
            print(f"\nCo-Bidding Rings ({len(triads)} closed triangles):")
            for t in triads:
                print(
                    f"  {t['contractor_a']}  <->  {t['contractor_b']}"
                    f"  <->  {t['contractor_c']}"
                )

        # Subcontracting loops
        loops = results.get("loops", [])
        if loops:
            print(f"\nSubcontracting Loops ({len(loops)} circular pairs):")
            for loop in loops:
                owner_a = f" (owner: {loop['owner_a']})" if loop.get("owner_a") else ""
                owner_b = f" (owner: {loop['owner_b']})" if loop.get("owner_b") else ""
                print(
                    f"  {loop['contractor_a']}{owner_a}"
                    f"  <->  {loop['contractor_b']}{owner_b}"
                )

        # Shared entities
        shared = results.get("shared_entities", [])
        if shared:
            print(f"\nShared Addresses / Officers ({len(shared)}):")
            for s in shared:
                assoc = s.get("association_type", "unknown")
                officer = s.get("shared_officer")
                detail = f" (officer: {officer})" if officer else ""
                print(
                    f"  {s['contractor_a']}  --  {s['contractor_b']}  [{assoc}]{detail}"
                )

        # Most connected
        connected = results.get("most_connected", [])
        if connected:
            print(f"\nMost Connected Entities (top {len(connected)}):")
            for c in connected:
                print(
                    f"  {c['name']:40s}  [{c['label']}]  {c['connections']} connections"
                )

        print("\n" + "=" * 80)


async def main():
    analyzer = NetworkAnalyzer()
    try:
        await analyzer.connect()
        results = await analyzer.run_all()
        analyzer.print_report(results)
    finally:
        await analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())
