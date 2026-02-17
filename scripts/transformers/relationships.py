"""Derive implicit relationships from data."""

from collections import defaultdict
from datetime import datetime
from typing import Any

from config import setup_logging

logger = setup_logging("relationships")


def derive_co_bidding(contracts: list[dict[str, Any]]) -> list[dict[str, str]]:
    """
    Derive CO_BID_WITH relationships from contractors bidding on same contracts.

    Returns list of edge records: {from_contractor, to_contractor, contract_count, pattern}
    """
    logger.info("Deriving co-bidding relationships")

    # Group contractors by contract
    contract_bidders = defaultdict(set)

    for contract in contracts:
        contract_ref = contract.get("reference_number")
        contractor = contract.get("contractor_name")

        if contract_ref and contractor:
            contract_bidders[contract_ref].add(contractor)

    # Find contractor pairs that co-bid
    co_bidding_pairs = defaultdict(int)

    for contract_ref, bidders in contract_bidders.items():
        if len(bidders) < 2:
            continue

        # All pairs of bidders on this contract
        bidders_list = list(bidders)
        for i in range(len(bidders_list)):
            for j in range(i + 1, len(bidders_list)):
                pair = tuple(sorted([bidders_list[i], bidders_list[j]]))
                co_bidding_pairs[pair] += 1

    # Convert to edge records
    edges = []
    for (contractor1, contractor2), count in co_bidding_pairs.items():
        if count >= 2:  # At least 2 shared contracts
            edges.append(
                {
                    "from_contractor": contractor1,
                    "to_contractor": contractor2,
                    "contract_count": count,
                    "pattern": "frequent" if count >= 5 else "occasional",
                }
            )

    logger.info(f"Derived {len(edges)} co-bidding relationships")

    return edges


def derive_political_connections(
    contractors: list[dict[str, Any]], politicians: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """
    Find potential contractor->politician connections via surname matching.

    This is a heuristic - same surname in same province suggests possible connection.

    Returns list of edge records: {contractor, politician, connection_type, confidence}
    """
    logger.info("Deriving political connections via surname matching")

    edges = []

    # Extract surnames
    def get_surname(name: str) -> str:
        if not name:
            return ""
        # Simple: last word before comma, or last word
        if "," in name:
            return name.split(",")[0].strip().upper()
        else:
            parts = name.strip().split()
            return parts[-1].upper() if parts else ""

    # Build politician surname index by province
    politician_by_surname = defaultdict(list)

    for politician in politicians:
        surname = get_surname(politician.get("name", ""))
        province = politician.get("province", "").upper()

        if surname and province:
            politician_by_surname[(surname, province)].append(politician)

    # Check contractors
    for contractor in contractors:
        contractor_name = contractor.get("contractor_name", contractor.get("name", ""))
        contractor_surname = get_surname(contractor_name)

        # Try to infer contractor province from address or municipality
        contractor_province = contractor.get("province", "").upper()
        if not contractor_province:
            # Try to extract from address
            contractor.get("address", "")
            # This is very rough - would need PSGC matching
            contractor_province = ""

        if not contractor_surname:
            continue

        # Check for matching politicians
        key = (contractor_surname, contractor_province)
        if key in politician_by_surname:
            for politician in politician_by_surname[key]:
                edges.append(
                    {
                        "contractor": contractor_name,
                        "politician": politician.get("name"),
                        "connection_type": "surname_match",
                        "confidence": "low",  # Surname alone is weak evidence
                        "province": contractor_province,
                    }
                )

    logger.info(f"Derived {len(edges)} potential political connections")

    return edges


def derive_geographic_patterns(
    contractors: list[dict[str, Any]], municipalities: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Flag contractors winning contracts outside their home region.

    Returns list of records: {contractor, home_region, contract_region, contract_count}
    """
    logger.info("Deriving geographic contract patterns")

    # Build municipality->region map
    muni_to_region = {}
    for muni in municipalities:
        muni_name = muni.get("name", "").upper()
        region = muni.get("region", "")
        if muni_name and region:
            muni_to_region[muni_name] = region

    # Track contractor regions
    contractor_regions = defaultdict(lambda: defaultdict(int))

    for contractor in contractors:
        contractor_name = contractor.get("contractor_name", contractor.get("name", ""))

        # Try to get contract location
        # This would need to be joined with contract->agency->municipality data
        # For now, this is a placeholder structure

        region = "UNKNOWN"  # Would need to resolve from contract data

        if contractor_name and region:
            contractor_regions[contractor_name][region] += 1

    # Find contractors operating across regions
    patterns = []

    for contractor, regions in contractor_regions.items():
        if len(regions) > 1:
            # Determine home region (most contracts)
            home_region = max(regions.items(), key=lambda x: x[1])[0]
            total_contracts = sum(regions.values())
            home_contracts = regions[home_region]
            away_contracts = total_contracts - home_contracts

            if away_contracts > 0:
                patterns.append(
                    {
                        "contractor": contractor,
                        "home_region": home_region,
                        "total_contracts": total_contracts,
                        "home_contracts": home_contracts,
                        "away_contracts": away_contracts,
                        "region_diversity": len(regions),
                    }
                )

    logger.info(f"Found {len(patterns)} contractors with multi-region patterns")

    return patterns


def derive_split_contracts(contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Detect potential contract splitting.

    Red flag: similar contracts from same agency, amounts near threshold,
    awarded around same time.

    Returns list of suspected split contract groups.
    """
    logger.info("Detecting potential contract splitting")

    # Common thresholds in Philippine procurement law (in PHP)
    THRESHOLDS = [
        50000,  # Small value
        1000000,  # Shopping
        5000000,  # Public bidding threshold (varies)
    ]

    # Group contracts by agency and time window

    agency_contracts = defaultdict(list)

    for contract in contracts:
        agency = contract.get("procuring_entity", "")
        if agency:
            agency_contracts[agency].append(contract)

    split_groups = []

    for agency, contracts_list in agency_contracts.items():
        # Sort by date
        contracts_list.sort(key=lambda c: c.get("award_date", "9999-12-31"))

        # Look for clusters near thresholds
        for i, contract1 in enumerate(contracts_list):
            amount1 = contract1.get("amount")
            date1_str = contract1.get("award_date")

            if not amount1 or not date1_str:
                continue

            try:
                date1 = datetime.fromisoformat(date1_str)
            except Exception:
                continue

            # Check if near threshold
            near_threshold = False
            for threshold in THRESHOLDS:
                if 0.7 * threshold <= amount1 <= threshold:
                    near_threshold = True
                    break

            if not near_threshold:
                continue

            # Look for similar contracts within 30 days
            cluster = [contract1]

            for contract2 in contracts_list[i + 1 :]:
                amount2 = contract2.get("amount")
                date2_str = contract2.get("award_date")

                if not amount2 or not date2_str:
                    continue

                try:
                    date2 = datetime.fromisoformat(date2_str)
                except Exception:
                    continue

                # Within 30 days?
                if abs((date2 - date1).days) <= 30:
                    # Similar amount?
                    if 0.5 * amount1 <= amount2 <= 2 * amount1:
                        cluster.append(contract2)

            if len(cluster) >= 2:
                total_amount = sum(c.get("amount", 0) for c in cluster)

                split_groups.append(
                    {
                        "agency": agency,
                        "contract_count": len(cluster),
                        "total_amount": total_amount,
                        "contracts": [
                            {
                                "reference_number": c.get("reference_number"),
                                "amount": c.get("amount"),
                                "date": c.get("award_date"),
                            }
                            for c in cluster
                        ],
                    }
                )

    logger.info(f"Detected {len(split_groups)} potential contract splitting patterns")

    return split_groups
