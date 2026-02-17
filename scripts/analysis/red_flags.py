"""Procurement red flag detection.

Automated checks for patterns that indicate irregularities:
contract splitting, suspiciously round amounts, bid rigging indicators,
timeline clustering, and audit findings linked to political families.
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

logger = setup_logging("red_flags")

# RA 9184 (Government Procurement Reform Act) thresholds in PHP
THRESHOLD_PUBLIC_BIDDING = 5_000_000
THRESHOLD_SHOPPING = 1_000_000
THRESHOLD_SMALL_VALUE = 50_000


class RedFlagAnalyzer:
    """Procurement irregularity detection."""

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

    async def contract_splitting(self) -> list[dict[str, Any]]:
        """Contracts from the same agency, same contractor, near thresholds,
        awarded within 30 days of each other.

        RA 9184 requires public bidding above P5M. Splitting a P15M project
        into three P4.9M contracts avoids that requirement.
        """
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c1:Contract)-[:AWARDED_TO]->(co:Contractor),
              (a)-[:PROCURED]->(c2:Contract)-[:AWARDED_TO]->(co)
        WHERE c1 <> c2
        AND c1.amount IS NOT NULL AND c2.amount IS NOT NULL
        AND c1.award_date IS NOT NULL AND c2.award_date IS NOT NULL
        AND c1.amount >= $lower AND c1.amount <= $upper
        AND c2.amount >= $lower AND c2.amount <= $upper
        AND abs(duration.inDays(date(c1.award_date), date(c2.award_date)).days) <= 30
        AND id(c1) < id(c2)
        RETURN a.name AS agency, co.name AS contractor,
               c1.title AS title_1, c1.amount AS amount_1, c1.award_date AS date_1,
               c2.title AS title_2, c2.amount AS amount_2, c2.award_date AS date_2,
               c1.amount + c2.amount AS combined
        ORDER BY combined DESC
        """
        # Check against the P5M public bidding threshold
        lower = THRESHOLD_PUBLIC_BIDDING * 0.7
        upper = THRESHOLD_PUBLIC_BIDDING

        try:
            async with self.driver.session(database=NEO4J_DATABASE) as session:
                result = await session.run(query, lower=lower, upper=upper)
                return await result.data()
        except Exception:
            # date arithmetic varies across Neo4j versions
            return await self._splitting_fallback()

    async def _splitting_fallback(self) -> list[dict[str, Any]]:
        """Simpler splitting detection without date math."""
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(co:Contractor)
        WHERE c.amount IS NOT NULL
        AND c.amount >= $lower AND c.amount <= $upper
        WITH a, co,
             COLLECT({
                title: c.title,
                amount: c.amount,
                date: c.award_date,
                ref: c.reference_number
             }) AS contracts
        WHERE SIZE(contracts) >= 2
        UNWIND contracts AS c
        WITH a, co, contracts, SUM(c.amount) AS combined
        RETURN a.name AS agency, co.name AS contractor,
               contracts, combined
        ORDER BY combined DESC
        """
        lower = THRESHOLD_PUBLIC_BIDDING * 0.7
        upper = THRESHOLD_PUBLIC_BIDDING

        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query, lower=lower, upper=upper)
            return await result.data()

    async def round_amounts(self) -> dict[str, Any]:
        """Contracts with suspiciously round amounts.

        Real engineering estimates produce odd numbers because they're
        based on actual material quantities and labor rates. Exact
        multiples of P500K suggest negotiated rather than estimated prices.
        """
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(co:Contractor)
        WHERE c.amount IS NOT NULL AND c.amount > 1000000
        WITH c, a, co,
             c.amount % 500000 = 0 AS is_round
        WITH COUNT(c) AS total,
             SUM(CASE WHEN is_round THEN 1 ELSE 0 END) AS round_count,
             COLLECT(CASE WHEN is_round THEN {
                agency: a.name, contractor: co.name,
                amount: c.amount, title: c.title
             } END) AS round_contracts
        RETURN total, round_count,
               round_count * 100.0 / total AS round_pct,
               [x IN round_contracts WHERE x IS NOT NULL] AS round_contracts
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            record = await result.single()
            return dict(record) if record else {}

    async def identical_amounts(self) -> list[dict[str, Any]]:
        """Different contractors winning contracts for the exact same amount.

        When multiple unrelated contractors each win a contract for exactly
        P234,000,000 from different agencies, it warrants scrutiny.
        """
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(co:Contractor)
        WHERE c.amount IS NOT NULL AND c.amount > 1000000
        WITH c.amount AS amount, COLLECT({
            agency: a.name, contractor: co.name, title: c.title,
            date: c.award_date
        }) AS contracts
        WHERE SIZE(contracts) >= 2
        RETURN amount, contracts
        ORDER BY amount DESC
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def bid_rigging_indicators(self) -> list[dict[str, Any]]:
        """COA audit findings flagged as bid rigging."""
        query = """
        MATCH (af:AuditFinding)
        WHERE af.type CONTAINS 'bid' OR af.type CONTAINS 'rigging'
           OR af.description CONTAINS 'bid' OR af.severity = 'critical'
        OPTIONAL MATCH (af)<-[:AUDITED]-(a:Agency)
        OPTIONAL MATCH (af)-[:INVOLVES_OFFICIAL]->(pol:Person)
        RETURN af.type AS finding_type, af.severity AS severity,
               af.description AS description, af.amount AS amount,
               a.name AS agency, pol.name AS linked_official
        ORDER BY af.severity
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def audit_findings_with_dynasties(self) -> list[dict[str, Any]]:
        """Audit findings that involve politicians from political dynasties."""
        query = """
        MATCH (af:AuditFinding)-[:INVOLVES_OFFICIAL]->(pol:Person)
        OPTIONAL MATCH (pol)-[:MEMBER_OF]->(pf:PoliticalFamily)
        OPTIONAL MATCH (af)<-[:AUDITED]-(a:Agency)
        RETURN af.type AS finding_type, af.severity AS severity,
               af.description AS description, af.amount AS amount,
               a.name AS agency,
               pol.name AS official, pf.name AS dynasty,
               pf.dynasty_score AS dynasty_score
        ORDER BY af.severity, pf.dynasty_score DESC
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def timeline_clusters(self) -> list[dict[str, Any]]:
        """Contract award date clustering — spending surges.

        Groups contracts by month to identify abnormal award clusters
        that may correlate with budget cycles or political events.
        """
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)
        WHERE c.award_date IS NOT NULL AND c.amount IS NOT NULL
        WITH substring(c.award_date, 0, 7) AS month,
             COUNT(c) AS contracts, SUM(c.amount) AS total
        ORDER BY month
        RETURN month, contracts, total
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def overpricing_flags(self) -> list[dict[str, Any]]:
        """Audit findings related to overpricing."""
        query = """
        MATCH (af:AuditFinding)
        WHERE af.type CONTAINS 'pric' OR af.description CONTAINS 'above market'
           OR af.description CONTAINS 'overpr'
        OPTIONAL MATCH (af)<-[:AUDITED]-(a:Agency)
        RETURN af.description AS description, af.amount AS amount,
               af.severity AS severity, a.name AS agency
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def unliquidated_funds(self) -> list[dict[str, Any]]:
        """Audit findings for unliquidated cash advances or funds."""
        query = """
        MATCH (af:AuditFinding)
        WHERE af.type CONTAINS 'unliq' OR af.description CONTAINS 'unliq'
           OR af.description CONTAINS 'cash advance'
        OPTIONAL MATCH (af)<-[:AUDITED]-(a:Agency)
        RETURN af.description AS description, af.amount AS amount,
               af.severity AS severity, a.name AS agency
        """
        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            return await result.data()

    async def run_all(self) -> dict[str, Any]:
        logger.info("Running red flag analysis")
        return {
            "splitting": await self.contract_splitting(),
            "round_amounts": await self.round_amounts(),
            "identical_amounts": await self.identical_amounts(),
            "bid_rigging": await self.bid_rigging_indicators(),
            "dynasty_audit": await self.audit_findings_with_dynasties(),
            "timeline": await self.timeline_clusters(),
            "overpricing": await self.overpricing_flags(),
            "unliquidated": await self.unliquidated_funds(),
        }

    def print_report(self, results: dict[str, Any]) -> None:
        print("\n" + "=" * 80)
        print("RED FLAG ANALYSIS")
        print("=" * 80)

        # Contract splitting
        splitting = results.get("splitting", [])
        if splitting:
            print(f"\nPotential Contract Splitting ({len(splitting)} pairs):")
            for s in splitting:
                if "contracts" in s:
                    # fallback format
                    print(
                        f"  {s['agency']} -> {s['contractor']}:"
                        f"  {len(s['contracts'])} contracts"
                        f"  combined PHP {s.get('combined', 0):,.0f}"
                    )
                else:
                    print(
                        f"  {s['agency']} -> {s['contractor']}:"
                        f"  PHP {s['amount_1']:,.0f} ({s['date_1']})"
                        f" + PHP {s['amount_2']:,.0f} ({s['date_2']})"
                        f" = PHP {s['combined']:,.0f}"
                    )

        # Round amounts
        rounds = results.get("round_amounts", {})
        if rounds:
            print(
                f"\nRound Amount Analysis:"
                f"  {rounds.get('round_count', 0)}/{rounds.get('total', 0)}"
                f" contracts ({rounds.get('round_pct', 0):.1f}%)"
                f" are exact multiples of PHP 500,000"
            )

        # Identical amounts
        identical = results.get("identical_amounts", [])
        if identical:
            print(f"\nIdentical Contract Amounts ({len(identical)} shared amounts):")
            for i in identical:
                contractors = [c["contractor"] for c in i["contracts"]]
                print(
                    f"  PHP {i['amount']:>15,.0f}  awarded to: {', '.join(contractors)}"
                )

        # Bid rigging
        rigging = results.get("bid_rigging", [])
        if rigging:
            print(f"\nBid Rigging Indicators ({len(rigging)}):")
            for r in rigging:
                official = (
                    f" -> {r['linked_official']}" if r.get("linked_official") else ""
                )
                print(
                    f"  [{r.get('severity', '?').upper()}] {r.get('agency', '?')}{official}"
                )
                print(f"    {r.get('description', '')}")

        # Dynasty audit findings
        dynasty_audit = results.get("dynasty_audit", [])
        if dynasty_audit:
            print(f"\nAudit Findings Linked to Dynasty Members ({len(dynasty_audit)}):")
            for d in dynasty_audit:
                dynasty = f" ({d['dynasty']})" if d.get("dynasty") else ""
                print(
                    f"  [{d.get('severity', '?').upper()}] {d.get('agency', '?')}"
                    f" -> {d['official']}{dynasty}"
                )
                if d.get("description"):
                    print(f"    {d['description']}")

        # Timeline
        timeline = results.get("timeline", [])
        if timeline:
            avg_monthly = sum(t["total"] for t in timeline) / len(timeline)
            print("\nMonthly Contract Awards:")
            for t in timeline:
                bar_len = int(t["total"] / avg_monthly * 20)
                bar = "#" * bar_len
                surge = " [SURGE]" if t["total"] > avg_monthly * 2 else ""
                print(
                    f"  {t['month']}  {t['contracts']:>3} contracts"
                    f"  PHP {t['total']:>13,.0f}  {bar}{surge}"
                )

        # Overpricing
        overpricing = results.get("overpricing", [])
        if overpricing:
            print(f"\nOverpricing Findings ({len(overpricing)}):")
            for o in overpricing:
                print(f"  [{o.get('severity', '?').upper()}] {o.get('agency', '?')}")
                print(f"    {o.get('description', '')}")
                if o.get("amount"):
                    print(f"    Amount: PHP {o['amount']:,.0f}")

        # Unliquidated
        unliq = results.get("unliquidated", [])
        if unliq:
            print(f"\nUnliquidated Funds ({len(unliq)}):")
            for u in unliq:
                print(f"  [{u.get('severity', '?').upper()}] {u.get('agency', '?')}")
                print(f"    {u.get('description', '')}")
                if u.get("amount"):
                    print(f"    Amount: PHP {u['amount']:,.0f}")

        print("\n" + "=" * 80)


async def main():
    analyzer = RedFlagAnalyzer()
    try:
        await analyzer.connect()
        results = await analyzer.run_all()
        analyzer.print_report(results)
    finally:
        await analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())
