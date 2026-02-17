"""Political dynasty and contractor connection analysis.

Traces ownership chains from contractors back to political families,
measures dynasty concentration scores, and checks whether dynasty-linked
contractors are geographically locked to their patron's territory.
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

logger = setup_logging("dynasties")


class DynastyAnalyzer:
    """Political family and contractor relationship analysis."""

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

    async def politician_contractor_links(self) -> list[dict[str, Any]]:
        """Direct ownership chains: politician -> family -> company."""
        query = """
        MATCH (pol:Person)-[:FAMILY_OF]-(person:Person)-[:OWNED_BY]-(co:Contractor)
        WHERE pol.role = 'politician' OR EXISTS((pol)-[:MEMBER_OF]->(:PoliticalFamily))
        OPTIONAL MATCH (pol)-[:GOVERNS]->(muni:Municipality)
        OPTIONAL MATCH (co)-[:LOCATED_IN]->(co_muni:Municipality)
        RETURN pol.name AS politician, pol.position AS position,
               person.name AS intermediary, person.relationship AS relationship,
               co.name AS contractor,
               muni.name AS governs_city, co_muni.name AS contractor_city,
               person.ownership_pct AS ownership_pct
        ORDER BY pol.name
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def geographic_lock_in(self) -> list[dict[str, Any]]:
        """Dynasty-linked contractors located in their patron's territory.

        When a contractor is physically based in the municipality governed
        by the politician they're connected to, it's a strong indicator
        of patronage.
        """
        query = """
        MATCH (pol:Person)-[:FAMILY_OF]-(person:Person)-[:OWNED_BY]-(co:Contractor)
        MATCH (pol)-[:GOVERNS]->(muni:Municipality)
        MATCH (co)-[:LOCATED_IN]->(co_muni:Municipality)
        RETURN pol.name AS politician, muni.name AS territory,
               co.name AS contractor, co_muni.name AS contractor_location,
               muni.name = co_muni.name AS same_territory
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def dynasty_scores(self) -> list[dict[str, Any]]:
        """Political family dynasty scores and member counts."""
        query = """
        MATCH (pf:PoliticalFamily)
        OPTIONAL MATCH (pf)<-[:MEMBER_OF]-(pol:Person)
        WITH pf, COLLECT(pol.name) AS members, COUNT(pol) AS member_count
        RETURN pf.name AS family, pf.province AS province,
               pf.dynasty_score AS score, pf.dynasty_type AS type,
               member_count, members
        ORDER BY pf.dynasty_score DESC
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def dynasty_vs_independent(self) -> dict[str, Any]:
        """Compare procurement captured by dynasty-linked vs independent firms."""
        query = """
        MATCH (co:Contractor)<-[:AWARDED_TO]-(c:Contract)<-[:PROCURED]-(a:Agency)
        WHERE c.amount IS NOT NULL
        WITH co, SUM(c.amount) AS total
        OPTIONAL MATCH (co)-[:OWNED_BY]-(:Person)-[:FAMILY_OF]-(:Person)-[:MEMBER_OF]->(:PoliticalFamily)
        WITH co, total,
             CASE WHEN COUNT(*) > 0 THEN true ELSE false END AS dynasty_linked
        WITH dynasty_linked,
             COUNT(co) AS contractors,
             SUM(total) AS total_value
        RETURN dynasty_linked, contractors, total_value
        ORDER BY dynasty_linked DESC
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            rows = await result.data()

        linked = next((r for r in rows if r["dynasty_linked"]), {})
        independent = next((r for r in rows if not r["dynasty_linked"]), {})
        grand_total = (linked.get("total_value", 0) or 0) + (
            independent.get("total_value", 0) or 0
        )

        return {
            "dynasty_contractors": linked.get("contractors", 0),
            "dynasty_value": linked.get("total_value", 0) or 0,
            "independent_contractors": independent.get("contractors", 0),
            "independent_value": independent.get("total_value", 0) or 0,
            "dynasty_share_pct": (
                (linked.get("total_value", 0) or 0) / grand_total * 100
                if grand_total
                else 0
            ),
        }

    async def longest_chains(self, limit: int = 10) -> list[dict[str, Any]]:
        """Longest relationship chains from politicians into the graph.

        Longer chains are harder to detect manually. A 6-hop chain
        means you'd need to cross-reference 6 different records
        to see the connection.
        """
        query = """
        MATCH path = (pol:Person)-[*1..6]-(end)
        WHERE (pol.role = 'politician' OR EXISTS((pol)-[:MEMBER_OF]->(:PoliticalFamily)))
        AND pol <> end
        WITH pol.name AS politician,
             length(path) AS hops,
             [n IN nodes(path) | n.name] AS chain,
             [r IN relationships(path) | type(r)] AS edge_types
        ORDER BY hops DESC
        LIMIT $limit
        RETURN politician, hops, chain, edge_types
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query, limit=limit)
            return await result.data()

    async def bills_by_dynasty_members(self) -> list[dict[str, Any]]:
        """Bills authored by members of political dynasties."""
        query = """
        MATCH (pol:Person)-[:AUTHORED]->(b:Bill)
        OPTIONAL MATCH (pol)-[:MEMBER_OF]->(pf:PoliticalFamily)
        RETURN pol.name AS author, pf.name AS family,
               pf.dynasty_score AS dynasty_score,
               b.title AS bill, b.description AS description
        ORDER BY pf.dynasty_score DESC
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def saln_net_worth(self) -> list[dict[str, Any]]:
        """Politicians ordered by declared net worth (SALN)."""
        query = """
        MATCH (p:Person)
        WHERE p.saln_net_worth IS NOT NULL
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(pf:PoliticalFamily)
        RETURN p.name AS politician, p.position AS position,
               p.saln_net_worth AS net_worth,
               pf.name AS family, pf.dynasty_score AS dynasty_score
        ORDER BY p.saln_net_worth DESC
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def run_all(self) -> dict[str, Any]:
        logger.info("Running dynasty analysis")
        return {
            "links": await self.politician_contractor_links(),
            "geographic": await self.geographic_lock_in(),
            "scores": await self.dynasty_scores(),
            "dynasty_vs_independent": await self.dynasty_vs_independent(),
            "chains": await self.longest_chains(),
            "bills": await self.bills_by_dynasty_members(),
            "saln": await self.saln_net_worth(),
        }

    def print_report(self, results: dict[str, Any]) -> None:
        print("\n" + "=" * 80)
        print("POLITICAL DYNASTY ANALYSIS")
        print("=" * 80)

        # Direct links
        links = results.get("links", [])
        if links:
            print(f"\nPolitician-Contractor Links ({len(links)}):")
            for link in links:
                ownership = (
                    f" ({link['ownership_pct']}% ownership)"
                    if link.get("ownership_pct")
                    else ""
                )
                print(
                    f"  {link['politician']} ({link.get('position', '?')})"
                    f"  ->  {link.get('intermediary', '?')}"
                    f" [{link.get('relationship', '?')}]"
                    f"  ->  {link['contractor']}{ownership}"
                )

        # Geographic lock-in
        geo = results.get("geographic", [])
        if geo:
            locked = [g for g in geo if g.get("same_territory")]
            print(
                f"\nGeographic Lock-In: {len(locked)}/{len(geo)} in patron's territory"
            )
            for g in geo:
                marker = "[LOCKED]" if g.get("same_territory") else "[OUTSIDE]"
                print(
                    f"  {marker} {g['contractor']} in {g['contractor_location']}"
                    f"  |  {g['politician']} governs {g['territory']}"
                )

        # Dynasty scores
        scores = results.get("scores", [])
        if scores:
            print("\nDynasty Scores:")
            print(
                f"  {'Family':20s}  {'Province':15s}  {'Score':>6s}  {'Type':6s}  Members"
            )
            print(f"  {'-' * 20}  {'-' * 15}  {'-' * 6}  {'-' * 6}  {'-' * 30}")
            for s in scores:
                members = ", ".join(s.get("members", [])[:3])
                if s.get("member_count", 0) > 3:
                    members += f" (+{s['member_count'] - 3} more)"
                print(
                    f"  {s['family']:20s}  {s.get('province', ''):15s}"
                    f"  {s.get('score', 0):>6.2f}  {s.get('type', ''):6s}"
                    f"  {members}"
                )

        # Dynasty vs independent
        dvi = results.get("dynasty_vs_independent", {})
        if dvi:
            print("\nDynasty vs Independent Procurement:")
            print(
                f"  Dynasty-linked:  {dvi['dynasty_contractors']} contractors,"
                f"  PHP {dvi['dynasty_value']:>15,.0f}"
                f"  ({dvi['dynasty_share_pct']:.1f}%)"
            )
            print(
                f"  Independent:     {dvi['independent_contractors']} contractors,"
                f"  PHP {dvi['independent_value']:>15,.0f}"
                f"  ({100 - dvi['dynasty_share_pct']:.1f}%)"
            )

        # Longest chains
        chains = results.get("chains", [])
        if chains:
            print(f"\nLongest Relationship Chains (top {len(chains)}):")
            for c in chains:
                path = " -> ".join(c.get("chain", []))
                print(f"  [{c['hops']} hops] {c['politician']}: {path}")

        # SALN
        saln = results.get("saln", [])
        if saln:
            print("\nDeclared Net Worth (SALN):")
            for s in saln:
                family = f" ({s['family']})" if s.get("family") else ""
                print(f"  {s['politician']:30s}  PHP {s['net_worth']:>15,.0f}{family}")

        # Bills
        bills = results.get("bills", [])
        if bills:
            print(f"\nBills Authored by Dynasty Members ({len(bills)}):")
            for b in bills:
                score = (
                    f" [dynasty score: {b['dynasty_score']:.2f}]"
                    if b.get("dynasty_score")
                    else ""
                )
                print(f"  {b['author']}{score}")
                print(f"    {b.get('bill', 'Untitled')}")

        print("\n" + "=" * 80)


async def main():
    analyzer = DynastyAnalyzer()
    try:
        await analyzer.connect()
        results = await analyzer.run_all()
        analyzer.print_report(results)
    finally:
        await analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())
