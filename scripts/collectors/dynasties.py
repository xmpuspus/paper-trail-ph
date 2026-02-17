"""Dynasty detection from election data."""

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from config import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    setup_logging,
)

logger = setup_logging("dynasties")


class DynastyDetector:
    """Detects political dynasties from election and official data."""

    def __init__(self):
        self.raw_dir = RAW_DATA_DIR / "dynasties"
        self.processed_dir = PROCESSED_DATA_DIR / "dynasties"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    async def download_election_data(self) -> Path | None:
        """
        Download COMELEC election results.

        Note: COMELEC election data is typically published as CSV/Excel files.
        This would need to navigate COMELEC website or use known URLs.
        For now, expects manual download.
        """
        logger.info("Election data collection for dynasty detection")
        logger.warning(
            "COMELEC election results must be manually downloaded from "
            "https://comelec.gov.ph/ or partner sites"
        )
        logger.info(f"Place downloaded files in: {self.raw_dir}")

        # Look for existing files
        csv_files = list(self.raw_dir.glob("*.csv"))
        xlsx_files = list(self.raw_dir.glob("*.xlsx"))

        all_files = csv_files + xlsx_files

        if all_files:
            latest = max(all_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Found election data: {latest.name}")
            return latest
        else:
            logger.warning("No election data files found")
            return None

    def extract_surname(self, full_name: str) -> str:
        """
        Extract surname from Filipino full name.

        Handles common Filipino name patterns:
        - "Lastname, Firstname Middlename"
        - "Firstname Middlename Lastname"
        - "Lastname, Firstname Middlename, Jr."
        """
        if not full_name:
            return ""

        name = full_name.strip()

        # Remove suffixes
        suffixes = [", Jr.", ", Sr.", ", III", ", II", " Jr.", " Sr.", " III", " II"]
        for suffix in suffixes:
            name = name.replace(suffix, "")

        # If comma-separated, surname is first part
        if "," in name:
            surname = name.split(",")[0].strip()
        else:
            # Otherwise, assume last word is surname
            parts = name.split()
            surname = parts[-1] if parts else ""

        # Handle compound surnames with particles
        surname_upper = surname.upper()

        return surname_upper

    def detect_dynasties(self, officials: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Detect political dynasties from official records.

        Detection logic:
        - Same surname in same/adjacent province
        - Overlapping terms or sequential positions
        - Calculate dynasty score based on family size, positions, duration
        """
        logger.info(f"Analyzing {len(officials)} officials for dynasties")

        # Group by surname + province
        surname_province_map = defaultdict(list)

        for official in officials:
            surname = self.extract_surname(official.get("name", ""))
            province = official.get("province", "").upper()

            if surname and province:
                surname_province_map[(surname, province)].append(official)

        dynasties = []
        dynasty_id = 1

        for (surname, province), members in surname_province_map.items():
            if len(members) < 2:
                continue  # Not a dynasty

            # Check for overlapping terms
            positions = set()
            earliest_term = None
            latest_term = None

            for member in members:
                position = member.get("position", "")
                term_start = member.get("term_start")
                term_end = member.get("term_end")

                positions.add(position)

                if term_start:
                    if not earliest_term or term_start < earliest_term:
                        earliest_term = term_start
                if term_end:
                    if not latest_term or term_end > latest_term:
                        latest_term = term_end

            # Calculate dynasty score
            # Factors: number of members, number of distinct positions, duration
            member_count = len(members)
            position_count = len(positions)

            # Duration in years (rough approximation)
            duration_years = 0
            if earliest_term and latest_term:
                try:
                    start = datetime.fromisoformat(earliest_term.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(latest_term.replace("Z", "+00:00"))
                    duration_years = (end - start).days / 365.25
                except Exception:
                    duration_years = 0

            # Score: members * positions * (1 + duration/10)
            dynasty_score = member_count * position_count * (1 + duration_years / 10)

            # Classify dynasty type
            # Fat dynasty: multiple positions simultaneously
            # Thin dynasty: sequential same position
            has_overlap = False
            for i, m1 in enumerate(members):
                for m2 in members[i + 1 :]:
                    # Check if terms overlap
                    start1 = m1.get("term_start")
                    end1 = m1.get("term_end")
                    start2 = m2.get("term_start")
                    end2 = m2.get("term_end")

                    if start1 and end1 and start2 and end2:
                        if start1 <= end2 and start2 <= end1:
                            has_overlap = True
                            break
                if has_overlap:
                    break

            dynasty_type = "fat" if has_overlap else "thin"

            dynasty = {
                "dynasty_id": f"DYN{dynasty_id:05d}",
                "surname": surname,
                "province": province,
                "member_count": member_count,
                "positions": list(positions),
                "dynasty_type": dynasty_type,
                "dynasty_score": round(dynasty_score, 2),
                "earliest_term": earliest_term,
                "latest_term": latest_term,
                "duration_years": round(duration_years, 1),
                "members": [
                    {
                        "name": m.get("name"),
                        "position": m.get("position"),
                        "term_start": m.get("term_start"),
                        "term_end": m.get("term_end"),
                    }
                    for m in members
                ],
            }

            dynasties.append(dynasty)
            dynasty_id += 1

        logger.info(f"Detected {len(dynasties)} political dynasties")

        # Sort by score descending
        dynasties.sort(key=lambda d: d["dynasty_score"], reverse=True)

        return dynasties

    def save_data(self, dynasties: list[dict[str, Any]]) -> None:
        """Save dynasty data as JSON lines."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.processed_dir / f"dynasties_{timestamp}.jsonl"

        with open(output_path, "w", encoding="utf-8") as f:
            for record in dynasties:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(dynasties)} dynasties to {output_path}")

    async def collect(self, officials: list[dict[str, Any]] | None = None) -> None:
        """
        Main dynasty detection workflow.

        Args:
            officials: Optional list of official records. If not provided,
                      will attempt to load from Congress data.
        """
        logger.info("Starting dynasty detection")

        if not officials:
            # Try to load from processed Congress data
            congress_dir = PROCESSED_DATA_DIR / "congress"
            member_files = sorted(congress_dir.glob("members_*.jsonl"))

            if member_files:
                latest = member_files[-1]
                logger.info(f"Loading officials from {latest.name}")

                officials = []
                with open(latest, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            officials.append(json.loads(line))
            else:
                logger.warning(
                    "No official data available. "
                    "Run 'python3 scripts/pipeline.py collect --source congress' first"
                )
                return

        if not officials:
            logger.warning("No officials to analyze")
            return

        # Detect dynasties
        dynasties = self.detect_dynasties(officials)

        if not dynasties:
            logger.info("No dynasties detected")
            return

        # Save
        self.save_data(dynasties)

        logger.info(f"Dynasty detection complete: {len(dynasties)} dynasties")

        # Print top 10
        logger.info("\nTop 10 dynasties by score:")
        for i, dynasty in enumerate(dynasties[:10], 1):
            logger.info(
                f"{i}. {dynasty['surname']} ({dynasty['province']}): "
                f"{dynasty['member_count']} members, "
                f"score {dynasty['dynasty_score']}, "
                f"{dynasty['dynasty_type']} dynasty"
            )


async def main():
    """Entry point for dynasty detection."""
    detector = DynastyDetector()
    await detector.collect()


if __name__ == "__main__":
    asyncio.run(main())
