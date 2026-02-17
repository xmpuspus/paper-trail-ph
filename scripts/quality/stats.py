"""Coverage and statistics reporting."""

import asyncio
from datetime import datetime
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver
from config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    setup_logging,
)

logger = setup_logging("stats")


class StatsReporter:
    """Generate coverage and statistics reports."""

    def __init__(self):
        self.uri = NEO4J_URI
        self.user = NEO4J_USER
        self.password = NEO4J_PASSWORD
        self.database = NEO4J_DATABASE
        self.driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Establish Neo4j connection."""
        self.driver = AsyncGraphDatabase.driver(
            self.uri, auth=(self.user, self.password)
        )
        await self.driver.verify_connectivity()

    async def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()

    async def node_counts(self) -> dict[str, int]:
        """Count nodes by type."""
        logger.info("Counting nodes by type")

        query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        """

        counts = {}

        async with self.driver.session(database=self.database) as session:
            result = await session.run(query)
            records = await result.data()

            for record in records:
                label = record.get("label", "Unknown")
                count = record.get("count", 0)
                counts[label] = count

        return counts

    async def edge_counts(self) -> dict[str, int]:
        """Count edges by type."""
        logger.info("Counting edges by type")

        query = """
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
        """

        counts = {}

        async with self.driver.session(database=self.database) as session:
            result = await session.run(query)
            records = await result.data()

            for record in records:
                rel_type = record.get("rel_type", "Unknown")
                count = record.get("count", 0)
                counts[rel_type] = count

        return counts

    async def coverage_by_year(self) -> dict[str, int]:
        """Count contracts per year."""
        logger.info("Calculating contract coverage by year")

        query = """
        MATCH (c:Contract)
        WHERE c.award_date IS NOT NULL
        WITH substring(c.award_date, 0, 4) as year, count(c) as count
        RETURN year, count
        ORDER BY year
        """

        coverage = {}

        async with self.driver.session(database=self.database) as session:
            try:
                result = await session.run(query)
                records = await result.data()

                for record in records:
                    year = record.get("year", "Unknown")
                    count = record.get("count", 0)
                    coverage[year] = count

            except Exception as e:
                logger.error(f"Coverage by year error: {e}")

        return coverage

    async def coverage_by_region(self) -> dict[str, int]:
        """Count contracts per region."""
        logger.info("Calculating contract coverage by region")

        query = """
        MATCH (c:Contract)<-[:PROCURED]-(a:Agency)-[:HAS_AGENCY]-(m:Municipality)
        WHERE m.region IS NOT NULL
        WITH m.region as region, count(c) as count
        RETURN region, count
        ORDER BY count DESC
        """

        coverage = {}

        async with self.driver.session(database=self.database) as session:
            try:
                result = await session.run(query)
                records = await result.data()

                for record in records:
                    region = record.get("region", "Unknown")
                    count = record.get("count", 0)
                    coverage[region] = count

                if not records:
                    logger.warning(
                        "No regional coverage data (may need HAS_AGENCY edges)"
                    )

            except Exception as e:
                logger.error(f"Coverage by region error: {e}")

        return coverage

    async def data_freshness(self) -> dict[str, str]:
        """Report last update per source."""
        logger.info("Checking data freshness")

        # This would check file modification times or metadata
        # For now, just check latest contract date

        query = """
        MATCH (c:Contract)
        WHERE c.award_date IS NOT NULL
        RETURN max(c.award_date) as latest_date
        """

        freshness = {}

        async with self.driver.session(database=self.database) as session:
            try:
                result = await session.run(query)
                record = await result.single()

                if record:
                    latest = record.get("latest_date")
                    freshness["PhilGEPS"] = latest if latest else "No data"

            except Exception as e:
                logger.error(f"Data freshness error: {e}")

        return freshness

    async def generate_stats(self) -> dict[str, Any]:
        """Generate full statistics report."""
        logger.info("Generating statistics report")

        stats = {
            "node_counts": await self.node_counts(),
            "edge_counts": await self.edge_counts(),
            "coverage_by_year": await self.coverage_by_year(),
            "coverage_by_region": await self.coverage_by_region(),
            "data_freshness": await self.data_freshness(),
            "generated_at": datetime.now().isoformat(),
        }

        return stats

    def print_stats(self, stats: dict[str, Any]) -> None:
        """Print formatted statistics report."""
        print("\n" + "=" * 80)
        print("GRAPH DATABASE STATISTICS")
        print("=" * 80)

        print(f"\nGenerated: {stats.get('generated_at', 'Unknown')}")

        # Node counts
        node_counts = stats.get("node_counts", {})
        if node_counts:
            print("\nNode Counts:")
            total_nodes = sum(node_counts.values())
            for label, count in node_counts.items():
                pct = (count / total_nodes * 100) if total_nodes > 0 else 0
                print(f"  {label:20s} {count:>8,d}  ({pct:>5.1f}%)")
            print(f"  {'TOTAL':20s} {total_nodes:>8,d}")

        # Edge counts
        edge_counts = stats.get("edge_counts", {})
        if edge_counts:
            print("\nEdge Counts:")
            total_edges = sum(edge_counts.values())
            for rel_type, count in edge_counts.items():
                pct = (count / total_edges * 100) if total_edges > 0 else 0
                print(f"  {rel_type:20s} {count:>8,d}  ({pct:>5.1f}%)")
            print(f"  {'TOTAL':20s} {total_edges:>8,d}")

        # Coverage by year
        year_coverage = stats.get("coverage_by_year", {})
        if year_coverage:
            print("\nContract Coverage by Year:")
            for year, count in sorted(year_coverage.items()):
                print(f"  {year}: {count:>8,d}")

        # Coverage by region
        region_coverage = stats.get("coverage_by_region", {})
        if region_coverage:
            print("\nContract Coverage by Region (top 10):")
            for region, count in list(region_coverage.items())[:10]:
                print(f"  {region:30s} {count:>8,d}")

        # Data freshness
        freshness = stats.get("data_freshness", {})
        if freshness:
            print("\nData Freshness:")
            for source, date in freshness.items():
                print(f"  {source}: {date}")

        print("\n" + "=" * 80)


async def main():
    """Entry point for statistics reporting."""
    reporter = StatsReporter()

    try:
        await reporter.connect()
        stats = await reporter.generate_stats()
        reporter.print_stats(stats)

    finally:
        await reporter.close()


if __name__ == "__main__":
    asyncio.run(main())
