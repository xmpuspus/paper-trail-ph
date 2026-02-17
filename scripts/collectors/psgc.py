"""PSGC (Philippine Standard Geographic Code) collector."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from config import (
    PSA_PSGC_URL,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    setup_logging,
)

logger = setup_logging("psgc")


class PSGCCollector:
    """Collects Philippine Standard Geographic Code data from PSA."""

    def __init__(self):
        self.raw_dir = RAW_DATA_DIR / "psgc"
        self.processed_dir = PROCESSED_DATA_DIR / "psgc"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    async def download_psgc(self) -> Path | None:
        """
        Download PSGC publication from PSA.

        Note: PSA PSGC data is published as Excel files on their website.
        This would need to scrape the PSA site or use a known direct download URL.
        For now, this expects manual download.
        """
        logger.info("PSGC data collection")
        logger.warning(f"PSGC data must be manually downloaded from {PSA_PSGC_URL}")
        logger.info(f"Place downloaded PSGC Excel file in: {self.raw_dir}")

        # Look for existing Excel files
        xlsx_files = list(self.raw_dir.glob("*.xlsx"))
        xls_files = list(self.raw_dir.glob("*.xls"))
        csv_files = list(self.raw_dir.glob("*.csv"))

        all_files = xlsx_files + xls_files + csv_files

        if all_files:
            # Use most recent file
            latest = max(all_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Found PSGC file: {latest.name}")
            return latest
        else:
            logger.warning("No PSGC files found")
            return None

    def parse_psgc(self, filepath: Path) -> list[dict[str, Any]]:
        """Parse PSGC file into municipality records."""
        logger.info(f"Parsing {filepath.name}")

        # Read file based on extension
        try:
            if filepath.suffix == ".csv":
                df = pd.read_csv(filepath, encoding="utf-8")
            else:
                df = pd.read_excel(filepath, engine="openpyxl")
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return []

        # PSGC columns (may vary by publication)
        # Expected: 10-digit Code, Name, Geographic Level, etc.
        logger.info(f"Columns: {list(df.columns)}")

        municipalities = []
        provinces = {}
        regions = {}

        for idx, row in df.iterrows():
            try:
                # PSGC code structure:
                # First 2 digits: Region
                # Next 2: Province
                # Next 2: Municipality/City
                # Next 3: Barangay
                code = str(row.get("Code", row.get("10-digit PSGC", ""))).strip()
                name = str(row.get("Name", "")).strip()
                geo_level = str(
                    row.get("Geographic Level", row.get("Geo Level", ""))
                ).lower()

                if not code or not name:
                    continue

                # Parse code
                if len(code) >= 9:
                    region_code = code[:2]
                    province_code = code[:4]
                    code[:6]

                    # Store region
                    if geo_level == "reg" or "region" in geo_level:
                        regions[region_code] = name

                    # Store province
                    elif geo_level == "prov" or "province" in geo_level:
                        provinces[province_code] = {
                            "code": province_code,
                            "name": name,
                            "region_code": region_code,
                        }

                    # Store municipality/city
                    elif geo_level in ["mun", "city", "municipality"]:
                        municipalities.append(
                            {
                                "psgc_code": code[:6],  # 6-digit for municipality
                                "name": name,
                                "province_code": province_code,
                                "region_code": region_code,
                                "type": "city"
                                if "city" in geo_level
                                else "municipality",
                                "income_class": row.get("Income Classification", ""),
                                "population": row.get("Population", None),
                            }
                        )

            except Exception as e:
                logger.warning(f"Error parsing row {idx}: {e}")
                continue

        # Enrich municipalities with province and region names
        for muni in municipalities:
            prov_code = muni["province_code"]
            reg_code = muni["region_code"]

            if prov_code in provinces:
                muni["province"] = provinces[prov_code]["name"]
            else:
                muni["province"] = None

            if reg_code in regions:
                muni["region"] = regions[reg_code]
            else:
                muni["region"] = None

        logger.info(
            f"Parsed {len(municipalities)} municipalities, "
            f"{len(provinces)} provinces, {len(regions)} regions"
        )

        return municipalities

    def save_data(self, municipalities: list[dict[str, Any]]) -> None:
        """Save PSGC data as JSON lines."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.processed_dir / f"municipalities_{timestamp}.jsonl"

        with open(output_path, "w", encoding="utf-8") as f:
            for record in municipalities:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(municipalities)} municipalities to {output_path}")

    async def collect(self) -> None:
        """Main collection workflow."""
        logger.info("Starting PSGC data collection")

        # Download/find file
        filepath = await self.download_psgc()

        if not filepath:
            logger.warning("No PSGC file available. Download manually.")
            return

        # Parse
        municipalities = self.parse_psgc(filepath)

        if not municipalities:
            logger.warning("No municipalities parsed")
            return

        # Save
        self.save_data(municipalities)

        logger.info(f"PSGC collection complete: {len(municipalities)} municipalities")


async def main():
    """Entry point for PSGC collection."""
    collector = PSGCCollector()
    await collector.collect()


if __name__ == "__main__":
    asyncio.run(main())
