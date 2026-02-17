"""Entity resolution and normalization."""

import re
from typing import Any

import jellyfish
from config import (
    FUZZY_MATCH_THRESHOLD_AUTO,
    setup_logging,
)

logger = setup_logging("normalize")


def normalize_contractor_name(name: str) -> str:
    """
    Normalize contractor name for matching.

    Removes common business suffixes, standardizes spacing, uppercase.
    """
    if not name:
        return ""

    # Uppercase
    normalized = name.upper().strip()

    # Remove common business suffixes
    suffixes = [
        r"\bINC\.?$",
        r"\bCORP\.?$",
        r"\bCORPORATION$",
        r"\bCO\.?$",
        r"\bCOMPANY$",
        r"\bLTD\.?$",
        r"\bLIMITED$",
        r"\bLLC$",
        r"\bPTE\.?$",
        r"\bPVT\.?$",
        r"\b&\s*CO\.?$",
        r"\bAND\s*CO\.?$",
    ]

    for suffix in suffixes:
        normalized = re.sub(suffix, "", normalized)

    # Remove extra punctuation
    normalized = re.sub(r"[.,;:]", "", normalized)

    # Standardize whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def normalize_politician_name(name: str) -> str:
    """
    Normalize Filipino politician name.

    Handles:
    - Filipino name prefixes (De, Dela, Del, Delos, De Los)
    - Suffixes (Jr, Sr, III, etc.)
    - Comma-separated formats
    """
    if not name:
        return ""

    # Uppercase
    normalized = name.upper().strip()

    # Remove suffixes
    suffixes = [
        ", JR.",
        ", SR.",
        ", III",
        ", II",
        ", IV",
        " JR.",
        " SR.",
        " III",
        " II",
        " IV",
    ]
    for suffix in suffixes:
        normalized = normalized.replace(suffix, "")

    # Standardize Filipino name particles
    # "DE LA CRUZ" vs "DELA CRUZ" vs "DELACRUZ"
    particles = [
        (r"\bDE\s+LA\s+", "DELA "),
        (r"\bDE\s+LOS\s+", "DELOS "),
        (r"\bDE\s+LAS\s+", "DELAS "),
        (r"\bDEL\s+", "DEL "),
    ]

    for pattern, replacement in particles:
        normalized = re.sub(pattern, replacement, normalized)

    # Remove extra whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def fuzzy_match_contractors(
    records: list[dict[str, Any]], threshold: float = FUZZY_MATCH_THRESHOLD_AUTO
) -> list[tuple[dict[str, Any], dict[str, Any], float]]:
    """
    Find fuzzy matches among contractor records using Jaro-Winkler similarity.

    Returns list of (record1, record2, similarity_score) tuples.
    """
    logger.info(
        f"Fuzzy matching {len(records)} contractor records (threshold={threshold})"
    )

    matches = []
    normalized_names = []

    # Pre-normalize all names
    for record in records:
        name = record.get("contractor_name", record.get("name", ""))
        normalized_names.append(normalize_contractor_name(name))

    # Compare all pairs
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            name1 = normalized_names[i]
            name2 = normalized_names[j]

            if not name1 or not name2:
                continue

            # Skip if exact match (will be caught by deduplication)
            if name1 == name2:
                continue

            # Calculate Jaro-Winkler similarity
            similarity = jellyfish.jaro_winkler_similarity(name1, name2)

            if similarity >= threshold:
                matches.append((records[i], records[j], similarity))

    logger.info(f"Found {len(matches)} fuzzy matches above threshold")

    # Sort by similarity descending
    matches.sort(key=lambda x: x[2], reverse=True)

    return matches


def merge_entities(
    matches: list[tuple[dict[str, Any], dict[str, Any], float]],
    confidence_threshold: float = FUZZY_MATCH_THRESHOLD_AUTO,
) -> dict[str, Any]:
    """
    Merge matched entities.

    Returns:
        {
            "auto_merged": [...],  # Merged above confidence threshold
            "review_required": [...],  # Flagged for manual review
            "merge_map": {original_name: canonical_name}
        }
    """
    auto_merged = []
    review_required = []
    merge_map = {}

    for record1, record2, similarity in matches:
        name1 = record1.get("contractor_name", record1.get("name", ""))
        name2 = record2.get("contractor_name", record2.get("name", ""))

        match_info = {
            "name1": name1,
            "name2": name2,
            "similarity": similarity,
            "record1": record1,
            "record2": record2,
        }

        if similarity >= confidence_threshold:
            # Auto-merge: use longer name as canonical
            canonical = name1 if len(name1) >= len(name2) else name2
            other = name2 if canonical == name1 else name1

            merge_map[other] = canonical
            auto_merged.append(match_info)

            logger.debug(
                f"Auto-merge: '{other}' -> '{canonical}' (score={similarity:.3f})"
            )
        else:
            # Flag for review
            review_required.append(match_info)
            logger.debug(f"Review: '{name1}' <-> '{name2}' (score={similarity:.3f})")

    logger.info(
        f"Merge results: {len(auto_merged)} auto-merged, "
        f"{len(review_required)} flagged for review"
    )

    return {
        "auto_merged": auto_merged,
        "review_required": review_required,
        "merge_map": merge_map,
    }


def deduplicate_records(
    records: list[dict[str, Any]], key_field: str
) -> list[dict[str, Any]]:
    """
    Remove exact duplicates by key field.

    Returns deduplicated records.
    """
    seen = set()
    unique = []

    for record in records:
        key = record.get(key_field)
        if key and key not in seen:
            seen.add(key)
            unique.append(record)

    logger.info(f"Deduplicated by {key_field}: {len(records)} -> {len(unique)}")

    return unique


def apply_merge_map(
    records: list[dict[str, Any]],
    merge_map: dict[str, str],
    name_field: str = "contractor_name",
) -> list[dict[str, Any]]:
    """
    Apply merge map to replace entity names with canonical versions.

    Modifies records in place and returns them.
    """
    logger.info(f"Applying {len(merge_map)} name normalizations")

    modified_count = 0

    for record in records:
        original_name = record.get(name_field)
        if original_name in merge_map:
            canonical_name = merge_map[original_name]
            record[name_field] = canonical_name
            record["original_name"] = original_name
            modified_count += 1

    logger.info(f"Applied merge map to {modified_count} records")

    return records
