"""DPWH Transparency Portal collector - real infrastructure project data.

Data source: https://transparency.dpwh.gov.ph/
Bulk dataset: https://huggingface.co/datasets/bettergovph/dpwh-transparency-data
License: CC0 1.0 Universal (public domain)
"""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from config import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    setup_logging,
)

logger = setup_logging("dpwh")

# HuggingFace dataset URLs (CC0 licensed, public domain)
HF_BASE_URL = "https://huggingface.co/datasets/bettergovph/dpwh-transparency-data/resolve/main"
HF_PARQUET_BASE = f"{HF_BASE_URL}/dpwh_transparency_data.parquet"
HF_PARQUET_DETAILED = f"{HF_BASE_URL}/dpwh_transparency_data_all_details.parquet"


class DPWHCollector:
    """Collects DPWH infrastructure project data from the pre-scraped HuggingFace dataset.

    The DPWH Transparency API (api.transparency.dpwh.gov.ph) is behind Cloudflare
    protection, so we use the CC0-licensed pre-scraped Parquet dataset maintained
    by bettergovph on HuggingFace.

    Original scraper: https://github.com/csiiiv/dpwh-transparency-data-api-scraper
    """

    def __init__(self):
        self.raw_dir = RAW_DATA_DIR / "dpwh"
        self.processed_dir = PROCESSED_DATA_DIR / "dpwh"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.processed_dir / "collector_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {"last_download": None, "record_count": 0}

    def _save_state(self) -> None:
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def _download_file(self, url: str, dest: Path) -> bool:
        """Download file using curl (macOS-safe HTTP)."""
        logger.info(f"Downloading {dest.name} from HuggingFace...")
        try:
            result = subprocess.run(
                [
                    "curl", "-L", "-f", "-o", str(dest),
                    "--progress-bar",
                    "--max-time", "600",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=660,
            )
            if result.returncode != 0:
                logger.error(f"Download failed: {result.stderr}")
                return False

            size_mb = dest.stat().st_size / (1024 * 1024)
            logger.info(f"Downloaded {dest.name}: {size_mb:.1f} MB")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Download timed out after 10 minutes")
            return False

    async def download_dataset(self, detailed: bool = False) -> Path | None:
        """Download DPWH Parquet dataset from HuggingFace.

        Args:
            detailed: If True, download the full 115MB detailed dataset.
                     If False, download the 24MB base dataset.
        """
        if detailed:
            url = HF_PARQUET_DETAILED
            filename = "dpwh_transparency_data_all_details.parquet"
        else:
            url = HF_PARQUET_BASE
            filename = "dpwh_transparency_data.parquet"

        dest = self.raw_dir / filename

        # Re-download if older than 7 days or missing
        if dest.exists():
            age_days = (datetime.now().timestamp() - dest.stat().st_mtime) / 86400
            if age_days < 7:
                logger.info(f"Using cached {filename} ({age_days:.1f} days old)")
                return dest
            logger.info(f"Dataset is {age_days:.0f} days old, re-downloading")

        success = self._download_file(url, dest)
        return dest if success else None

    def _extract_location(self, row: pd.Series) -> dict[str, str | None]:
        """Extract province and region from the location field."""
        location = row.get("location")

        province = None
        region = None

        if isinstance(location, dict):
            province = location.get("province")
            region = location.get("region")
        elif isinstance(location, str):
            try:
                loc_dict = json.loads(location)
                province = loc_dict.get("province")
                region = loc_dict.get("region")
            except (json.JSONDecodeError, TypeError):
                pass

        # Fallback: some datasets have flat columns
        if not province:
            province = row.get("location.province", row.get("province"))
        if not region:
            region = row.get("location.region", row.get("region"))

        return {"province": province, "region": region}

    def _normalize_status(self, status: Any) -> str:
        if pd.isna(status):
            return "unknown"

        status_str = str(status).strip().lower()
        mappings = {
            "completed": ["completed", "complete", "done"],
            "on-going": ["on-going", "ongoing", "in progress", "in-progress"],
            "not yet started": ["not yet started", "not started", "pending"],
            "terminated": ["terminated", "cancelled", "canceled"],
            "suspended": ["suspended"],
        }
        for standard, variants in mappings.items():
            if status_str in variants:
                return standard

        return status_str

    def _safe_float(self, val: Any) -> float | None:
        if pd.isna(val):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, val: Any) -> int | None:
        if pd.isna(val):
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    def _safe_date(self, val: Any) -> str | None:
        if pd.isna(val):
            return None
        if isinstance(val, (datetime, pd.Timestamp)):
            return val.strftime("%Y-%m-%d")
        date_str = str(val).strip()
        if not date_str or date_str == "NaT":
            return None
        return date_str[:10]  # YYYY-MM-DD

    def _safe_str(self, val: Any) -> str | None:
        if pd.isna(val):
            return None
        s = str(val).strip()
        return s if s else None

    def parse_parquet(self, filepath: Path) -> list[dict[str, Any]]:
        """Parse DPWH Parquet file into normalized contract records."""
        logger.info(f"Parsing {filepath.name}")

        try:
            df = pd.read_parquet(filepath)
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return []

        logger.info(f"Loaded {len(df)} rows, columns: {list(df.columns)}")

        records = []
        skipped = 0

        for idx, row in df.iterrows():
            try:
                contract_id = self._safe_str(row.get("contractId"))
                if not contract_id:
                    skipped += 1
                    continue

                location = self._extract_location(row)

                record = {
                    "reference_number": contract_id,
                    "title": self._safe_str(row.get("description")),
                    "category": self._safe_str(row.get("category")),
                    "component_categories": self._safe_str(row.get("componentCategories")),
                    "status": self._normalize_status(row.get("status")),
                    "amount": self._safe_float(row.get("budget")),
                    "amount_paid": self._safe_float(row.get("amountPaid")),
                    "progress": self._safe_float(row.get("progress")),
                    "contractor_name": self._safe_str(row.get("contractor")),
                    "start_date": self._safe_date(row.get("startDate")),
                    "completion_date": self._safe_date(row.get("completionDate")),
                    "infra_year": self._safe_str(row.get("infraYear")),
                    "program_name": self._safe_str(row.get("programName")),
                    "source_of_funds": self._safe_str(row.get("sourceOfFunds")),
                    "province": self._safe_str(location.get("province")),
                    "region": self._safe_str(location.get("region")),
                    "latitude": self._safe_float(row.get("latitude")),
                    "longitude": self._safe_float(row.get("longitude")),
                    "has_satellite_image": bool(row.get("hasSatelliteImage")),
                    "report_count": self._safe_int(row.get("reportCount")),
                    "is_live": bool(row.get("isLive")),
                    # Source attribution
                    "data_source": "dpwh_transparency_portal",
                    "data_license": "CC0-1.0",
                }

                # Derive procuring entity from province DEO pattern
                # DPWH data uses "{Province} DEO" or "{Province} 1st DEO" etc.
                if record["province"]:
                    record["procuring_entity"] = f"DPWH - {record['province']}"
                else:
                    record["procuring_entity"] = "DPWH"

                records.append(record)

            except Exception as e:
                logger.warning(f"Error parsing row {idx}: {e}")
                skipped += 1

        logger.info(f"Parsed {len(records)} contracts, skipped {skipped}")
        return records

    def extract_contractors(self, contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract unique contractors from contract records."""
        contractors: dict[str, dict[str, Any]] = {}

        for contract in contracts:
            name = contract.get("contractor_name")
            if not name:
                continue

            if name not in contractors:
                contractors[name] = {
                    "name": name,
                    "total_contracts": 0,
                    "total_value": 0.0,
                    "regions": set(),
                    "provinces": set(),
                    "categories": set(),
                }

            c = contractors[name]
            c["total_contracts"] += 1

            amount = contract.get("amount")
            if amount:
                c["total_value"] += amount

            region = contract.get("region")
            if region:
                c["regions"].add(region)

            province = contract.get("province")
            if province:
                c["provinces"].add(province)

            category = contract.get("category")
            if category:
                c["categories"].add(category)

        # Convert sets to lists for JSON serialization
        result = []
        for name, data in contractors.items():
            data["regions"] = sorted(data["regions"])
            data["provinces"] = sorted(data["provinces"])
            data["categories"] = sorted(data["categories"])
            data["total_value"] = round(data["total_value"], 2)
            result.append(data)

        result.sort(key=lambda c: c["total_value"], reverse=True)
        logger.info(f"Extracted {len(result)} unique contractors")
        return result

    def extract_agencies(self, contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract unique procuring entities from contract records."""
        agencies: dict[str, dict[str, Any]] = {}

        for contract in contracts:
            name = contract.get("procuring_entity")
            if not name:
                continue

            if name not in agencies:
                agencies[name] = {
                    "name": name,
                    "department": "DPWH",
                    "type": "district_engineering_office",
                    "total_contracts": 0,
                    "total_value": 0.0,
                }

            a = agencies[name]
            a["total_contracts"] += 1
            amount = contract.get("amount")
            if amount:
                a["total_value"] += amount

        result = []
        for name, data in agencies.items():
            data["total_value"] = round(data["total_value"], 2)
            result.append(data)

        result.sort(key=lambda a: a["total_value"], reverse=True)
        logger.info(f"Extracted {len(result)} unique agencies")
        return result

    def save_jsonl(self, records: list[dict[str, Any]], name: str) -> Path:
        """Save records as JSON lines."""
        output_path = self.processed_dir / f"{name}.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        logger.info(f"Saved {len(records)} records to {output_path}")
        return output_path

    async def collect(self, detailed: bool = False) -> None:
        """Main collection workflow.

        Args:
            detailed: Download the full 115MB detailed dataset instead of 24MB base.
        """
        logger.info("Starting DPWH data collection from HuggingFace dataset")
        logger.info("Source: bettergovph/dpwh-transparency-data (CC0 license)")

        # Download
        filepath = await self.download_dataset(detailed=detailed)
        if not filepath:
            logger.error("Failed to download DPWH dataset")
            return

        # Parse
        contracts = self.parse_parquet(filepath)
        if not contracts:
            logger.error("No contracts parsed from dataset")
            return

        # Extract entities
        contractors = self.extract_contractors(contracts)
        agencies = self.extract_agencies(contracts)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_jsonl(contracts, f"contracts_{timestamp}")
        self.save_jsonl(contractors, f"contractors_{timestamp}")
        self.save_jsonl(agencies, f"agencies_{timestamp}")

        # Update state
        self.state["last_download"] = datetime.now().isoformat()
        self.state["record_count"] = len(contracts)
        self.state["contractor_count"] = len(contractors)
        self.state["agency_count"] = len(agencies)
        self._save_state()

        # Summary
        total_value = sum(c.get("amount") or 0 for c in contracts)
        completed = sum(1 for c in contracts if c.get("status") == "completed")
        ongoing = sum(1 for c in contracts if c.get("status") == "on-going")

        logger.info("=" * 60)
        logger.info("DPWH Collection Summary")
        logger.info("=" * 60)
        logger.info(f"Contracts:   {len(contracts):,}")
        logger.info(f"Contractors: {len(contractors):,}")
        logger.info(f"Agencies:    {len(agencies):,}")
        logger.info(f"Total value: PHP {total_value:,.2f}")
        logger.info(f"Completed:   {completed:,}")
        logger.info(f"On-going:    {ongoing:,}")

        regions = set()
        for c in contracts:
            r = c.get("region")
            if r:
                regions.add(r)
        logger.info(f"Regions:     {len(regions)}")
        logger.info("=" * 60)


async def main(detailed: bool = False):
    """Entry point for DPWH collection."""
    collector = DPWHCollector()
    await collector.collect(detailed=detailed)


if __name__ == "__main__":
    asyncio.run(main())
