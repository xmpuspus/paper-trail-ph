"""Open Congress API collector - Philippine legislative data."""

import asyncio
import json
from datetime import datetime
from typing import Any

import httpx
from config import (
    OPEN_CONGRESS_BASE_URL,
    CONGRESS_API_RATE_LIMIT,
    HTTP_TIMEOUT,
    MAX_RETRIES,
    RETRY_BACKOFF,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    setup_logging,
)

logger = setup_logging("open_congress")


class OpenCongressCollector:
    """Collects Philippine legislative data from Open Congress API."""

    def __init__(self):
        self.base_url = OPEN_CONGRESS_BASE_URL
        self.rate_limit = 1.0 / CONGRESS_API_RATE_LIMIT  # seconds between requests
        self.raw_dir = RAW_DATA_DIR / "congress"
        self.processed_dir = PROCESSED_DATA_DIR / "congress"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    async def _fetch_with_retry(
        self, client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Fetch URL with exponential backoff retry."""
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.get(url, params=params, timeout=HTTP_TIMEOUT)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait_time = RETRY_BACKOFF**attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                elif e.response.status_code >= 500:  # Server error
                    wait_time = RETRY_BACKOFF**attempt
                    logger.warning(f"Server error, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"HTTP error {e.response.status_code}: {url}")
                    return None
            except (httpx.RequestError, httpx.TimeoutException) as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF**attempt)

        logger.error(f"Failed after {MAX_RETRIES} attempts: {url}")
        return None

    async def _paginate_endpoint(
        self, client: httpx.AsyncClient, endpoint: str, per_page: int = 50
    ) -> list[dict[str, Any]]:
        """Paginate through an API endpoint."""
        all_results = []
        page = 1

        while True:
            logger.info(f"Fetching {endpoint} page {page}")

            url = f"{self.base_url}/{endpoint}"
            params = {"page": page, "per_page": per_page}

            data = await self._fetch_with_retry(client, url, params)

            if not data:
                break

            # Handle different response structures
            if isinstance(data, dict):
                results = data.get("data", data.get("results", []))
                if isinstance(results, list):
                    all_results.extend(results)
                else:
                    all_results.append(data)

                # Check if there are more pages
                total_pages = data.get("total_pages", 0)
                if page >= total_pages or not results:
                    break
            elif isinstance(data, list):
                all_results.extend(data)
                if len(data) < per_page:
                    break
            else:
                break

            page += 1

            # Rate limiting
            await asyncio.sleep(self.rate_limit)

        logger.info(f"Collected {len(all_results)} records from {endpoint}")
        return all_results

    async def collect_members(self) -> list[dict[str, Any]]:
        """Collect congress members data."""
        logger.info("Collecting congress members")

        async with httpx.AsyncClient() as client:
            members = await self._paginate_endpoint(client, "congress-members")

        # Normalize member records
        normalized = []
        for member in members:
            normalized.append(
                {
                    "id": member.get("id"),
                    "name": member.get("name", member.get("full_name", "")),
                    "position": member.get("position", member.get("role", "")),
                    "district": member.get("district"),
                    "province": member.get("province"),
                    "party": member.get("party"),
                    "congress": member.get("congress"),
                    "term_start": member.get("term_start"),
                    "term_end": member.get("term_end"),
                    "committee_memberships": member.get("committees", []),
                }
            )

        logger.info(f"Normalized {len(normalized)} congress members")
        return normalized

    async def collect_bills(self) -> list[dict[str, Any]]:
        """Collect bills data."""
        logger.info("Collecting bills")

        async with httpx.AsyncClient() as client:
            bills = await self._paginate_endpoint(client, "bills")

        # Normalize bill records
        normalized = []
        for bill in bills:
            normalized.append(
                {
                    "number": bill.get("number", bill.get("bill_number", "")),
                    "title": bill.get("title", bill.get("long_title", "")),
                    "short_title": bill.get("short_title"),
                    "status": bill.get("status"),
                    "filed_date": bill.get("filed_date", bill.get("date_filed")),
                    "congress": bill.get("congress"),
                    "authors": bill.get("authors", []),
                    "co_authors": bill.get("co_authors", []),
                    "committee": bill.get("committee"),
                    "description": bill.get("description"),
                }
            )

        logger.info(f"Normalized {len(normalized)} bills")
        return normalized

    async def collect_committees(self) -> list[dict[str, Any]]:
        """Collect committee data."""
        logger.info("Collecting committees")

        async with httpx.AsyncClient() as client:
            committees = await self._paginate_endpoint(client, "committees")

        # Normalize committee records
        normalized = []
        for committee in committees:
            normalized.append(
                {
                    "id": committee.get("id"),
                    "name": committee.get("name"),
                    "chamber": committee.get("chamber"),
                    "congress": committee.get("congress"),
                    "chair": committee.get("chair", committee.get("chairman")),
                    "members": committee.get("members", []),
                }
            )

        logger.info(f"Normalized {len(normalized)} committees")
        return normalized

    def save_data(self, data: list[dict[str, Any]], name: str) -> None:
        """Save collected data as JSON lines."""
        output_path = self.processed_dir / f"{name}.jsonl"

        with open(output_path, "w", encoding="utf-8") as f:
            for record in data:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(data)} records to {output_path}")

    async def collect_all(self) -> None:
        """Collect all Open Congress data."""
        logger.info("Starting Open Congress data collection")

        # Collect all datasets
        members = await self.collect_members()
        bills = await self.collect_bills()
        committees = await self.collect_committees()

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_data(members, f"members_{timestamp}")
        self.save_data(bills, f"bills_{timestamp}")
        self.save_data(committees, f"committees_{timestamp}")

        logger.info(
            f"Open Congress collection complete: "
            f"{len(members)} members, {len(bills)} bills, {len(committees)} committees"
        )


async def main():
    """Entry point for Open Congress collection."""
    collector = OpenCongressCollector()
    await collector.collect_all()


if __name__ == "__main__":
    asyncio.run(main())
