"""Agency-level market concentration analysis.

Measures how concentrated procurement spending is within each agency
using the Herfindahl-Hirschman Index (HHI). The US DOJ considers an HHI
above 2500 to indicate a highly concentrated market. Philippine
government agencies routinely exceed this.
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

logger = setup_logging("concentration")

# US DOJ thresholds for market concentration
HHI_MODERATE = 1500
HHI_HIGH = 2500


class ConcentrationAnalyzer:
    """Procurement concentration analysis per agency."""

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

    async def spending_by_agency(self) -> list[dict[str, Any]]:
        """Total procurement spending per agency."""
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(co:Contractor)
        WHERE c.amount IS NOT NULL
        WITH a.name AS agency, a.department AS dept, a.type AS agency_type,
             SUM(c.amount) AS total, COUNT(c) AS contracts
        ORDER BY total DESC
        RETURN agency, dept, agency_type, total, contracts
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def hhi_per_agency(self) -> list[dict[str, Any]]:
        """Herfindahl-Hirschman Index for each agency.

        HHI = sum of squared market shares. A monopoly scores 10,000.
        Anything above 2,500 is "highly concentrated" by DOJ standards.
        """
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(co:Contractor)
        WHERE c.amount IS NOT NULL
        WITH a.name AS agency, co.name AS contractor, SUM(c.amount) AS contractor_total
        WITH agency, contractor, contractor_total,
             SUM(contractor_total) OVER (PARTITION BY agency) AS agency_total
        WITH agency, contractor,
             (contractor_total * 100.0 / agency_total) AS market_share,
             contractor_total, agency_total
        WITH agency, agency_total,
             COLLECT({
                contractor: contractor,
                share: market_share,
                amount: contractor_total
             }) AS shares,
             SUM(market_share * market_share) AS hhi
        ORDER BY hhi DESC
        RETURN agency, agency_total, hhi, shares
        """
        # Window functions may not be available in all Neo4j versions,
        # so fall back to a two-pass approach if needed
        try:
            async with self.driver.session(database=NEO4J_DATABASE) as session:
                result = await session.run(query)
                return await result.data()
        except Exception:
            return await self._hhi_fallback()

    async def _hhi_fallback(self) -> list[dict[str, Any]]:
        """Two-pass HHI calculation for Neo4j versions without window functions."""
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(co:Contractor)
        WHERE c.amount IS NOT NULL
        WITH a.name AS agency, co.name AS contractor, SUM(c.amount) AS contractor_total
        WITH agency, COLLECT({contractor: contractor, amount: contractor_total}) AS contractors,
             SUM(contractor_total) AS agency_total
        UNWIND contractors AS c
        WITH agency, agency_total, c.contractor AS contractor, c.amount AS amount,
             (c.amount * 100.0 / agency_total) AS share
        WITH agency, agency_total,
             COLLECT({contractor: contractor, share: share, amount: amount}) AS shares,
             SUM((c.amount * 100.0 / agency_total) * (c.amount * 100.0 / agency_total)) AS hhi
        ORDER BY hhi DESC
        RETURN agency, agency_total, hhi, shares
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def single_bidder_contracts(self) -> list[dict[str, Any]]:
        """Contracts awarded without competitive bidding."""
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(co:Contractor)
        WHERE c.procurement_mode IN [
            'Direct Contracting', 'negotiated', 'shopping'
        ] OR c.bidders = 1
        RETURN a.name AS agency, co.name AS contractor,
               c.amount AS amount, c.procurement_mode AS mode,
               c.title AS title, c.award_date AS date
        ORDER BY c.amount DESC
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def contractor_reach(self) -> list[dict[str, Any]]:
        """Contractors winning from multiple agencies."""
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(co:Contractor)
        WHERE c.amount IS NOT NULL
        WITH co.name AS contractor,
             COUNT(DISTINCT a) AS agency_count,
             SUM(c.amount) AS total,
             COLLECT(DISTINCT a.name) AS agencies
        WHERE agency_count >= 2
        ORDER BY agency_count DESC, total DESC
        RETURN contractor, agency_count, total, agencies
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def run_all(self) -> dict[str, Any]:
        logger.info("Running concentration analysis")
        return {
            "spending": await self.spending_by_agency(),
            "hhi": await self.hhi_per_agency(),
            "single_bidder": await self.single_bidder_contracts(),
            "contractor_reach": await self.contractor_reach(),
        }

    def print_report(self, results: dict[str, Any]) -> None:
        print("\n" + "=" * 80)
        print("PROCUREMENT CONCENTRATION ANALYSIS")
        print("=" * 80)

        # Spending summary
        spending = results.get("spending", [])
        if spending:
            total = sum(r["total"] for r in spending)
            print(f"\nTotal tracked procurement: PHP {total:,.0f}")
            print(f"Agencies: {len(spending)}")
            print("\nSpending by Agency:")
            for r in spending:
                pct = r["total"] / total * 100
                print(f"  {r['agency']:40s}  PHP {r['total']:>15,.0f}  ({pct:.1f}%)")

        # HHI
        hhi_data = results.get("hhi", [])
        if hhi_data:
            print("\nHerfindahl-Hirschman Index (HHI) per Agency:")
            print(f"  {'Agency':40s}  {'HHI':>8s}  {'Level':12s}  Top Contractor")
            print(f"  {'-' * 40}  {'-' * 8}  {'-' * 12}  {'-' * 30}")
            for r in hhi_data:
                hhi = r["hhi"]
                if hhi >= HHI_HIGH:
                    level = "HIGH"
                elif hhi >= HHI_MODERATE:
                    level = "MODERATE"
                else:
                    level = "LOW"

                top = max(r["shares"], key=lambda s: s["share"])
                print(
                    f"  {r['agency']:40s}  {hhi:>8,.0f}  {level:12s}"
                    f"  {top['contractor']} ({top['share']:.1f}%)"
                )

        # Single-bidder
        single = results.get("single_bidder", [])
        if single:
            total_single = sum(r["amount"] for r in single if r.get("amount"))
            print(f"\nNon-Competitive Contracts: {len(single)}")
            print(f"Total value: PHP {total_single:,.0f}")
            for r in single:
                amt = r["amount"] or 0
                print(
                    f"  {r['contractor']:30s}  PHP {amt:>12,.0f}"
                    f"  [{r['mode']}]  {r['title'] or ''}"
                )

        # Multi-agency contractors
        reach = results.get("contractor_reach", [])
        if reach:
            print("\nContractors Winning Across Multiple Agencies:")
            for r in reach:
                print(
                    f"  {r['contractor']:30s}  {r['agency_count']} agencies"
                    f"  PHP {r['total']:>12,.0f}"
                )
                for a in r["agencies"]:
                    print(f"    - {a}")

        print("\n" + "=" * 80)


async def main():
    analyzer = ConcentrationAnalyzer()
    try:
        await analyzer.connect()
        results = await analyzer.run_all()
        analyzer.print_report(results)
    finally:
        await analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())
