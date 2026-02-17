"""PhilGEPS data collector - downloads and parses procurement data."""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from config import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    setup_logging,
)

logger = setup_logging("philgeps")


class PhilGEPSCollector:
    """Collects and parses PhilGEPS procurement data."""

    def __init__(self):
        self.raw_dir = RAW_DATA_DIR / "philgeps"
        self.processed_dir = PROCESSED_DATA_DIR / "philgeps"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Track last download
        self.state_file = self.processed_dir / "collector_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        """Load collector state from disk."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {"last_download": None, "processed_files": []}

    def _save_state(self) -> None:
        """Save collector state to disk."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    async def download_datasets(self, since_year: int = 2020) -> list[Path]:
        """
        Download PhilGEPS datasets from data.gov.ph.

        Note: This is a simplified implementation. In production, you would need to:
        1. Navigate data.gov.ph to find PhilGEPS dataset URLs
        2. Handle authentication if required
        3. Parse HTML to find download links

        For now, this creates placeholder structure for manual download.
        """
        logger.info(f"PhilGEPS data collection for years >= {since_year}")
        logger.warning(
            "PhilGEPS has no API - Excel files must be manually downloaded from "
            "https://open.philgeps.gov.ph/ or https://data.gov.ph/"
        )
        logger.info(f"Place downloaded XLSX files in: {self.raw_dir}")

        # List any existing XLSX files
        xlsx_files = list(self.raw_dir.glob("*.xlsx"))
        if xlsx_files:
            logger.info(f"Found {len(xlsx_files)} XLSX files to process")
            return xlsx_files
        else:
            logger.warning("No XLSX files found in raw data directory")
            return []

    def _normalize_date(self, date_val: Any) -> str | None:
        """Parse dates in multiple formats."""
        if pd.isna(date_val):
            return None

        # If already datetime
        if isinstance(date_val, datetime):
            return date_val.strftime("%Y-%m-%d")

        date_str = str(date_val).strip()

        # Try multiple date formats
        formats = [
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%d-%b-%y",
            "%d-%b-%Y",
            "%B %d, %Y",
            "%d %B %Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_val}")
        return None

    def _normalize_amount(self, amount_val: Any) -> float | None:
        """Clean and parse monetary amounts."""
        if pd.isna(amount_val):
            return None

        amount_str = str(amount_val).strip()

        # Remove currency symbols, commas, whitespace
        amount_str = re.sub(r"[₱$,\s]", "", amount_str)

        # Handle ranges (take first value)
        if "-" in amount_str:
            amount_str = amount_str.split("-")[0]

        try:
            return float(amount_str)
        except (ValueError, TypeError):
            logger.warning(f"Could not parse amount: {amount_val}")
            return None

    def _normalize_procurement_method(self, method: str) -> str:
        """Normalize procurement method to standard values."""
        if pd.isna(method):
            return "unknown"

        method_lower = str(method).lower().strip()

        mappings = {
            "public_bidding": ["public bidding", "competitive bidding", "public bid"],
            "shopping": ["shopping", "small value procurement"],
            "negotiated": [
                "negotiated procurement",
                "negotiated",
                "direct contracting",
            ],
            "limited_source": ["limited source bidding"],
            "direct_retail": ["direct retail purchase"],
            "repeat_order": ["repeat order"],
            "emergency": ["emergency purchase", "emergency"],
        }

        for standard, variants in mappings.items():
            if any(variant in method_lower for variant in variants):
                return standard

        return "other"

    def _detect_columns(self, df: pd.DataFrame) -> dict[str, str]:
        """
        Detect column names dynamically.
        PhilGEPS column names vary across datasets.
        """
        column_map = {}
        columns_lower = {col.lower(): col for col in df.columns}

        # Reference number
        for variant in [
            "reference number",
            "reference no",
            "ref no",
            "refno",
            "reference_number",
        ]:
            if variant in columns_lower:
                column_map["reference_number"] = columns_lower[variant]
                break

        # Title
        for variant in ["title", "project title", "procurement title", "description"]:
            if variant in columns_lower:
                column_map["title"] = columns_lower[variant]
                break

        # Procuring entity
        for variant in ["procuring entity", "agency", "pe", "procuring_entity"]:
            if variant in columns_lower:
                column_map["procuring_entity"] = columns_lower[variant]
                break

        # Contractor/awardee
        for variant in [
            "contractor",
            "awardee",
            "winning bidder",
            "supplier",
            "awarded_to",
        ]:
            if variant in columns_lower:
                column_map["contractor_name"] = columns_lower[variant]
                break

        # Amount
        for variant in [
            "amount",
            "contract amount",
            "approved budget",
            "abc",
            "bid amount",
        ]:
            if variant in columns_lower:
                column_map["amount"] = columns_lower[variant]
                break

        # Procurement method
        for variant in [
            "procurement method",
            "method",
            "procurement_method",
            "mode of procurement",
        ]:
            if variant in columns_lower:
                column_map["procurement_method"] = columns_lower[variant]
                break

        # Award date
        for variant in ["award date", "date awarded", "award_date", "date of award"]:
            if variant in columns_lower:
                column_map["award_date"] = columns_lower[variant]
                break

        # Status
        for variant in ["status", "procurement status", "award status"]:
            if variant in columns_lower:
                column_map["status"] = columns_lower[variant]
                break

        return column_map

    def parse_xlsx(self, filepath: Path) -> list[dict[str, Any]]:
        """Parse PhilGEPS XLSX file into normalized records."""
        logger.info(f"Parsing {filepath.name}")

        try:
            df = pd.read_excel(filepath, engine="openpyxl")
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return []

        # Detect columns
        col_map = self._detect_columns(df)
        logger.info(f"Detected columns: {list(col_map.keys())}")

        if not col_map:
            logger.error(f"Could not detect standard columns in {filepath}")
            return []

        records = []
        skipped = 0

        for idx, row in df.iterrows():
            try:
                record = {
                    "reference_number": str(
                        row.get(col_map.get("reference_number", ""), "")
                    ).strip(),
                    "title": str(row.get(col_map.get("title", ""), "")).strip(),
                    "procuring_entity": str(
                        row.get(col_map.get("procuring_entity", ""), "")
                    ).strip(),
                    "contractor_name": str(
                        row.get(col_map.get("contractor_name", ""), "")
                    ).strip(),
                    "amount": self._normalize_amount(
                        row.get(col_map.get("amount", ""))
                    ),
                    "procurement_method": self._normalize_procurement_method(
                        row.get(col_map.get("procurement_method", ""))
                    ),
                    "award_date": self._normalize_date(
                        row.get(col_map.get("award_date", ""))
                    ),
                    "status": str(row.get(col_map.get("status", ""), "active"))
                    .strip()
                    .lower(),
                    "source_file": filepath.name,
                }

                # Skip if missing critical fields
                if not record["reference_number"] or not record["procuring_entity"]:
                    skipped += 1
                    continue

                records.append(record)

            except Exception as e:
                logger.warning(f"Error parsing row {idx}: {e}")
                skipped += 1
                continue

        logger.info(f"Parsed {len(records)} records, skipped {skipped}")
        return records

    def deduplicate_by_reference(
        self, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Deduplicate records by reference number."""
        seen = set()
        unique = []

        for record in records:
            ref = record["reference_number"]
            if ref not in seen:
                seen.add(ref)
                unique.append(record)

        logger.info(f"Deduplicated: {len(records)} -> {len(unique)} records")
        return unique

    def save_processed(self, records: list[dict[str, Any]], output_name: str) -> None:
        """Save processed records as JSON lines."""
        output_path = self.processed_dir / f"{output_name}.jsonl"

        with open(output_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(records)} records to {output_path}")

    async def collect(self, since_year: int = 2020) -> None:
        """Main collection workflow."""
        logger.info("Starting PhilGEPS data collection")

        # Download/list datasets
        xlsx_files = await self.download_datasets(since_year)

        if not xlsx_files:
            logger.warning("No datasets to process. Download XLSX files manually.")
            return

        all_records = []

        # Parse each file
        for filepath in xlsx_files:
            if filepath.name in self.state["processed_files"]:
                logger.info(f"Skipping already processed: {filepath.name}")
                continue

            records = self.parse_xlsx(filepath)
            all_records.extend(records)

            # Mark as processed
            self.state["processed_files"].append(filepath.name)

        if not all_records:
            logger.info("No new records to process")
            return

        # Deduplicate
        unique_records = self.deduplicate_by_reference(all_records)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_processed(unique_records, f"contracts_{timestamp}")

        # Update state
        self.state["last_download"] = datetime.now().isoformat()
        self._save_state()

        logger.info(f"PhilGEPS collection complete: {len(unique_records)} contracts")


async def main(since_year: int = 2020):
    """Entry point for PhilGEPS collection."""
    collector = PhilGEPSCollector()
    await collector.collect(since_year)


if __name__ == "__main__":
    asyncio.run(main())
