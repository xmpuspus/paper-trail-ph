from __future__ import annotations

from datetime import datetime

from neo4j import AsyncDriver

from backend.models.graph_models import RedFlag, Severity


class RedFlagService:
    def __init__(self, driver: AsyncDriver) -> None:
        self.driver = driver

    async def single_bidder_contracts(self, threshold: int = 3) -> list[RedFlag]:
        """Contractors with multiple single-bidder contracts (bid_count = 1)."""
        query = """
        MATCH (c:Contract)-[:AWARDED_TO]->(con:Contractor)
        WHERE c.bid_count = 1
        WITH con, collect(c) as contracts, count(c) as single_bid_count
        WHERE single_bid_count >= $threshold
        RETURN con.name as contractor_name,
               elementId(con) as contractor_id,
               single_bid_count,
               [c IN contracts | {ref: c.reference_number, amount: c.amount, date: toString(c.award_date)}] as contract_details
        ORDER BY single_bid_count DESC
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query, threshold=threshold)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="single_bidder",
                        severity=Severity.MEDIUM,
                        description=(
                            f"{rec['contractor_name']} has {rec['single_bid_count']} "
                            f"single-bidder contracts"
                        ),
                        evidence={
                            "contractor_id": str(rec["contractor_id"]),
                            "contractor_name": rec["contractor_name"],
                            "single_bid_count": rec["single_bid_count"],
                            "contracts": rec["contract_details"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def identical_bid_amounts(self, tolerance: float = 0.001) -> list[RedFlag]:
        """Contracts where multiple bids are suspiciously close in amount."""
        query = """
        MATCH (con1:Contractor)-[b1:BID_ON]->(c:Contract)<-[b2:BID_ON]-(con2:Contractor)
        WHERE elementId(con1) < elementId(con2)
              AND b1.bid_amount > 0 AND b2.bid_amount > 0
              AND abs(b1.bid_amount - b2.bid_amount) / b1.bid_amount < $tolerance
        RETURN c.reference_number as contract_ref,
               c.title as contract_title,
               c.amount as contract_amount,
               elementId(c) as contract_id,
               con1.name as bidder1,
               con2.name as bidder2,
               b1.bid_amount as bid1,
               b2.bid_amount as bid2,
               abs(b1.bid_amount - b2.bid_amount) / b1.bid_amount as deviation
        ORDER BY deviation ASC
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query, tolerance=tolerance)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="identical_bid_amounts",
                        severity=Severity.HIGH,
                        description=(
                            f"Near-identical bids on contract {rec['contract_ref']}: "
                            f"{rec['bidder1']} ({rec['bid1']:,.2f}) vs "
                            f"{rec['bidder2']} ({rec['bid2']:,.2f})"
                        ),
                        evidence={
                            "contract_id": str(rec["contract_id"]),
                            "contract_ref": rec["contract_ref"],
                            "bidder1": rec["bidder1"],
                            "bidder2": rec["bidder2"],
                            "bid1": rec["bid1"],
                            "bid2": rec["bid2"],
                            "deviation": rec["deviation"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def split_contracts(self, threshold: float = 5_000_000) -> list[RedFlag]:
        """Multiple contracts just below threshold from same agency around similar dates."""
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(con:Contractor)
        WHERE c.amount < $threshold AND c.amount > $threshold * 0.7
        WITH a, con, collect(c) as contracts, count(c) as num_contracts,
             sum(c.amount) as total_value
        WHERE num_contracts >= 3
        RETURN a.name as agency_name,
               elementId(a) as agency_id,
               con.name as contractor_name,
               elementId(con) as contractor_id,
               num_contracts,
               total_value,
               [c IN contracts | {
                   ref: c.reference_number,
                   amount: c.amount,
                   date: toString(c.award_date)
               }] as contract_details
        ORDER BY num_contracts DESC
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query, threshold=threshold)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="split_contracts",
                        severity=Severity.HIGH,
                        description=(
                            f"{rec['agency_name']} awarded {rec['num_contracts']} contracts "
                            f"just below PHP {threshold:,.0f} threshold to {rec['contractor_name']} "
                            f"(total: PHP {rec['total_value']:,.2f})"
                        ),
                        evidence={
                            "agency_id": str(rec["agency_id"]),
                            "agency_name": rec["agency_name"],
                            "contractor_id": str(rec["contractor_id"]),
                            "contractor_name": rec["contractor_name"],
                            "num_contracts": rec["num_contracts"],
                            "total_value": rec["total_value"],
                            "threshold": threshold,
                            "contracts": rec["contract_details"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def concentration(self, hhi_threshold: float = 0.25) -> list[RedFlag]:
        """Agencies with HHI above threshold (high contractor concentration)."""
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(con:Contractor)
        WITH a, con, sum(c.amount) as contractor_total
        WITH a,
             collect({name: con.name, value: contractor_total}) as contractors,
             sum(contractor_total) as grand_total
        WHERE grand_total > 0
        UNWIND contractors as contractor
        WITH a, contractor, grand_total,
             (contractor.value / grand_total) as share
        WITH a, grand_total,
             sum(share * share) as hhi,
             collect({name: contractor.name, share: share, value: contractor.value}) as details
        WHERE hhi > $threshold
        RETURN a.name as agency_name,
               elementId(a) as agency_id,
               hhi,
               grand_total as total_value,
               details as top_contractors
        ORDER BY hhi DESC
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query, threshold=hhi_threshold)
            async for record in result:
                rec = dict(record)
                top = sorted(
                    rec["top_contractors"], key=lambda x: x["share"], reverse=True
                )[:5]
                flags.append(
                    RedFlag(
                        type="concentration",
                        severity=Severity.HIGH,
                        description=(
                            f"{rec['agency_name']} has HHI of {rec['hhi']:.3f} "
                            f"(threshold: {hhi_threshold}). Top contractor: {top[0]['name']} "
                            f"({top[0]['share']:.1%} share)"
                        ),
                        evidence={
                            "agency_id": str(rec["agency_id"]),
                            "agency_name": rec["agency_name"],
                            "hhi": rec["hhi"],
                            "total_value": rec["total_value"],
                            "top_contractors": top,
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def rotating_winners(self) -> list[RedFlag]:
        """Groups of contractors that co-bid frequently and take turns winning."""
        query = """
        MATCH (c1:Contractor)-[cb:CO_BID_WITH]-(c2:Contractor)
        WHERE cb.contract_count >= 3
        WITH c1, c2, cb.contract_count as co_bid_count
        OPTIONAL MATCH (con1:Contract)-[:AWARDED_TO]->(c1)
        WHERE EXISTS { MATCH (c2)-[:BID_ON]->(con1) }
        WITH c1, c2, co_bid_count, count(con1) as c1_wins
        OPTIONAL MATCH (con2:Contract)-[:AWARDED_TO]->(c2)
        WHERE EXISTS { MATCH (c1)-[:BID_ON]->(con2) }
        WITH c1, c2, co_bid_count, c1_wins, count(con2) as c2_wins
        WHERE c1_wins > 0 AND c2_wins > 0
        RETURN c1.name as contractor1,
               elementId(c1) as contractor1_id,
               c2.name as contractor2,
               elementId(c2) as contractor2_id,
               co_bid_count,
               c1_wins,
               c2_wins
        ORDER BY co_bid_count DESC
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="rotating_winners",
                        severity=Severity.HIGH,
                        description=(
                            f"{rec['contractor1']} and {rec['contractor2']} co-bid on "
                            f"{rec['co_bid_count']} contracts, alternating wins "
                            f"({rec['c1_wins']} vs {rec['c2_wins']})"
                        ),
                        evidence={
                            "contractor1_id": str(rec["contractor1_id"]),
                            "contractor1": rec["contractor1"],
                            "contractor2_id": str(rec["contractor2_id"]),
                            "contractor2": rec["contractor2"],
                            "co_bid_count": rec["co_bid_count"],
                            "wins": {
                                rec["contractor1"]: rec["c1_wins"],
                                rec["contractor2"]: rec["c2_wins"],
                            },
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def political_connections(self) -> list[RedFlag]:
        """Contractors with short ownership paths to politicians."""
        query = """
        MATCH path = (con:Contractor)-[:OWNED_BY]->(p:Person)-[:FAMILY_OF]->(pol:Politician)
        RETURN con.name as contractor_name,
               elementId(con) as contractor_id,
               p.name as person_name,
               pol.name as politician_name,
               elementId(pol) as politician_id,
               pol.position as position,
               length(path) as path_length
        ORDER BY path_length ASC
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="political_connection",
                        severity=Severity.HIGH,
                        description=(
                            f"{rec['contractor_name']} is owned by {rec['person_name']}, "
                            f"who is a family member of {rec['politician_name']} "
                            f"({rec['position']})"
                        ),
                        evidence={
                            "contractor_id": str(rec["contractor_id"]),
                            "contractor_name": rec["contractor_name"],
                            "person_name": rec["person_name"],
                            "politician_id": str(rec["politician_id"]),
                            "politician_name": rec["politician_name"],
                            "position": rec["position"],
                            "path_length": rec["path_length"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def geographic_anomaly(self) -> list[RedFlag]:
        """Contractors winning bids in regions far from their registered address."""
        query = """
        MATCH (con:Contractor)-[:LOCATED_IN]->(home:Municipality)
        MATCH (c:Contract)-[:AWARDED_TO]->(con)
        MATCH (a:Agency)-[:PROCURED]->(c)
        OPTIONAL MATCH (a)<-[:HAS_AGENCY]-(loc:Municipality)
        WHERE loc IS NOT NULL AND home.region <> loc.region
        WITH con, home, loc,
             count(c) as contracts_outside_region,
             sum(c.amount) as value_outside_region
        WHERE contracts_outside_region >= 3
        RETURN con.name as contractor_name,
               elementId(con) as contractor_id,
               home.name as home_municipality,
               home.region as home_region,
               collect(DISTINCT loc.region) as award_regions,
               contracts_outside_region,
               value_outside_region
        ORDER BY contracts_outside_region DESC
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="geographic_anomaly",
                        severity=Severity.MEDIUM,
                        description=(
                            f"{rec['contractor_name']} (based in {rec['home_municipality']}, "
                            f"{rec['home_region']}) won {rec['contracts_outside_region']} "
                            f"contracts in other regions: {', '.join(rec['award_regions'])}"
                        ),
                        evidence={
                            "contractor_id": str(rec["contractor_id"]),
                            "contractor_name": rec["contractor_name"],
                            "home_municipality": rec["home_municipality"],
                            "home_region": rec["home_region"],
                            "award_regions": rec["award_regions"],
                            "contracts_outside_region": rec["contracts_outside_region"],
                            "value_outside_region": rec["value_outside_region"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def shell_company(self, ratio_threshold: float = 100) -> list[RedFlag]:
        """Contractors with suspiciously low registered capital winning large contracts."""
        query = """
        MATCH (con:Contractor)
        WHERE con.registered_capital IS NOT NULL AND con.registered_capital > 0
        MATCH (c:Contract)-[:AWARDED_TO]->(con)
        WITH con, sum(c.amount) as total_awarded, con.registered_capital as capital
        WHERE total_awarded / capital > $ratio_threshold
        RETURN con.name as contractor_name,
               elementId(con) as contractor_id,
               capital,
               total_awarded,
               total_awarded / capital as ratio
        ORDER BY ratio DESC
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query, ratio_threshold=ratio_threshold)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="shell_company",
                        severity=Severity.HIGH,
                        description=(
                            f"{rec['contractor_name']} has registered capital of "
                            f"PHP {rec['capital']:,.2f} but won contracts worth "
                            f"PHP {rec['total_awarded']:,.2f} ({rec['ratio']:.1f}x capital)"
                        ),
                        evidence={
                            "contractor_id": str(rec["contractor_id"]),
                            "contractor_name": rec["contractor_name"],
                            "capital": rec["capital"],
                            "total_awarded": rec["total_awarded"],
                            "ratio": rec["ratio"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def phoenix_company(self) -> list[RedFlag]:
        """Contractors sharing directors or addresses with blacklisted companies."""
        query = """
        MATCH (old:Contractor)-[:BLACKLISTED]->(bl:BlacklistEntry)
        MATCH (old)-[:SHARES_DIRECTOR_WITH]-(new:Contractor)
        WHERE NOT EXISTS { MATCH (new)-[:BLACKLISTED]->() }
        OPTIONAL MATCH (old)-[:SAME_ADDRESS_AS]-(new)
        RETURN old.name as blacklisted_company,
               elementId(old) as old_id,
               new.name as new_company,
               elementId(new) as new_id,
               bl.offense as offense,
               bl.sanction_date as blacklist_date
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="phoenix_company",
                        severity=Severity.HIGH,
                        description=(
                            f"{rec['new_company']} shares directors with blacklisted company "
                            f"{rec['blacklisted_company']} (offense: {rec['offense']})"
                        ),
                        evidence={
                            "new_contractor_id": str(rec["new_id"]),
                            "new_contractor_name": rec["new_company"],
                            "blacklisted_contractor_id": str(rec["old_id"]),
                            "blacklisted_contractor_name": rec["blacklisted_company"],
                            "offense": rec["offense"],
                            "blacklist_date": (
                                str(rec["blacklist_date"])
                                if rec["blacklist_date"]
                                else None
                            ),
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def campaign_connection(self) -> list[RedFlag]:
        """Contractors who donated to politicians and then won contracts from their jurisdiction."""
        query = """
        MATCH (con:Contractor)-[:DONATED_TO]->(cd:CampaignDonation)-[:DONATED_TO]->(pol:Politician)
        MATCH (pol)-[:GOVERNS]->(m:Municipality)-[:HAS_AGENCY]->(a:Agency)-[:PROCURED]->(c:Contract)-[:AWARDED_TO]->(con)
        WITH con, pol, cd, a, collect(c) as contracts
        RETURN con.name as contractor_name,
               elementId(con) as contractor_id,
               pol.name as politician_name,
               elementId(pol) as politician_id,
               cd.amount as donation,
               reduce(total = 0.0, ct IN contracts | total + coalesce(ct.amount, 0)) as contracts_won,
               size(contracts) as contract_count,
               [ct IN contracts | {ref: ct.reference_number, amount: ct.amount, date: toString(ct.award_date)}] as contract_details
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="campaign_connection",
                        severity=Severity.HIGH,
                        description=(
                            f"{rec['contractor_name']} donated PHP {rec['donation']:,.2f} to "
                            f"{rec['politician_name']}, then won contracts worth "
                            f"PHP {rec['contracts_won']:,.2f} from their jurisdiction"
                        ),
                        evidence={
                            "contractor_id": str(rec["contractor_id"]),
                            "contractor_name": rec["contractor_name"],
                            "politician_id": str(rec["politician_id"]),
                            "politician_name": rec["politician_name"],
                            "donation_amount": rec["donation"],
                            "contracts_won": rec["contracts_won"],
                            "contract_count": rec["contract_count"],
                            "contracts": rec["contract_details"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def circular_flow(self) -> list[RedFlag]:
        """Cycles in subcontracting chains where money flows back to the original contractor."""
        query = """
        MATCH (c1:Contractor)-[:SUBCONTRACTED_TO]->(c2:Contractor)-[:SUBCONTRACTED_TO]->(c3:Contractor)
        WHERE c1 = c3 OR EXISTS { MATCH (c3)-[:SUBCONTRACTED_TO]->(c1) }
        RETURN c1.name as contractor1,
               elementId(c1) as c1_id,
               c2.name as contractor2,
               elementId(c2) as c2_id,
               c3.name as contractor3,
               elementId(c3) as c3_id
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="circular_flow",
                        severity=Severity.CRITICAL,
                        description=(
                            f"Circular subcontracting detected: {rec['contractor1']} → "
                            f"{rec['contractor2']} → {rec['contractor3']}"
                        ),
                        evidence={
                            "contractor1_id": str(rec["c1_id"]),
                            "contractor1": rec["contractor1"],
                            "contractor2_id": str(rec["c2_id"]),
                            "contractor2": rec["contractor2"],
                            "contractor3_id": str(rec["c3_id"]),
                            "contractor3": rec["contractor3"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def timing_cluster(
        self, days_threshold: int = 2, min_contracts: int = 3
    ) -> list[RedFlag]:
        """Multiple contracts awarded to the same contractor within a short time window."""
        query = """
        MATCH (a:Agency)-[:PROCURED]->(c1:Contract)-[:AWARDED_TO]->(con:Contractor),
              (a)-[:PROCURED]->(c2:Contract)-[:AWARDED_TO]->(con)
        WHERE c1 <> c2
          AND abs(duration.between(c1.award_date, c2.award_date).days) <= $days_threshold
        WITH a, con, collect(DISTINCT c1) + collect(DISTINCT c2) as contracts
        WHERE size(contracts) >= $min_contracts
        RETURN a.name as agency_name,
               elementId(a) as agency_id,
               con.name as contractor_name,
               elementId(con) as contractor_id,
               size(contracts) as contract_count,
               [c IN contracts | {ref: c.reference_number, amount: c.amount, date: toString(c.award_date)}] as contract_details
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(
                query, days_threshold=days_threshold, min_contracts=min_contracts
            )
            async for record in result:
                rec = dict(record)
                flags.append(
                    RedFlag(
                        type="timing_cluster",
                        severity=Severity.HIGH,
                        description=(
                            f"{rec['agency_name']} awarded {rec['contract_count']} contracts to "
                            f"{rec['contractor_name']} within {days_threshold} days"
                        ),
                        evidence={
                            "agency_id": str(rec["agency_id"]),
                            "agency_name": rec["agency_name"],
                            "contractor_id": str(rec["contractor_id"]),
                            "contractor_name": rec["contractor_name"],
                            "contract_count": rec["contract_count"],
                            "contracts": rec["contract_details"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def shell_network(self) -> list[RedFlag]:
        """Contractors sharing the same address (structural equivalence)."""
        query = """
        MATCH (c1:Contractor)-[:SAME_ADDRESS_AS]-(c2:Contractor)
        WHERE elementId(c1) < elementId(c2)
        OPTIONAL MATCH (c1)-[sd:SHARES_DIRECTOR_WITH]-(c2)
        RETURN c1.name as contractor1,
               elementId(c1) as c1_id,
               c2.name as contractor2,
               elementId(c2) as c2_id,
               c1.address as address,
               count(sd) as shared_directors
        """
        flags: list[RedFlag] = []
        async with self.driver.session() as session:
            result = await session.run(query)
            async for record in result:
                rec = dict(record)
                description = (
                    f"{rec['contractor1']} and {rec['contractor2']} share the same "
                    f"address: {rec['address']}"
                )
                if rec["shared_directors"] > 0:
                    description += f" and {rec['shared_directors']} director(s)"

                flags.append(
                    RedFlag(
                        type="shell_network",
                        severity=Severity.HIGH,
                        description=description,
                        evidence={
                            "contractor1_id": str(rec["c1_id"]),
                            "contractor1": rec["contractor1"],
                            "contractor2_id": str(rec["c2_id"]),
                            "contractor2": rec["contractor2"],
                            "address": rec["address"],
                            "shared_directors": rec["shared_directors"],
                        },
                        detected_at=datetime.utcnow(),
                    )
                )
        return flags

    async def detect_all(self) -> dict[str, list[RedFlag]]:
        """Run all detectors and return grouped results."""
        return {
            "single_bidder": await self.single_bidder_contracts(),
            "identical_bids": await self.identical_bid_amounts(),
            "split_contracts": await self.split_contracts(),
            "concentration": await self.concentration(),
            "rotating_winners": await self.rotating_winners(),
            "political_connections": await self.political_connections(),
            "geographic_anomaly": await self.geographic_anomaly(),
            "shell_company": await self.shell_company(),
            "phoenix_company": await self.phoenix_company(),
            "campaign_connection": await self.campaign_connection(),
            "circular_flow": await self.circular_flow(),
            "timing_cluster": await self.timing_cluster(),
            "shell_network": await self.shell_network(),
        }
