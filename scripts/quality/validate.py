"""Data quality validation checks."""

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

logger = setup_logging("validate")


class DataValidator:
    """Validates data quality in Neo4j graph."""

    def __init__(self):
        self.uri = NEO4J_URI
        self.user = NEO4J_USER
        self.password = NEO4J_PASSWORD
        self.database = NEO4J_DATABASE
        self.driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Establish Neo4j connection."""
        logger.info(f"Connecting to Neo4j at {self.uri}")
        self.driver = AsyncGraphDatabase.driver(
            self.uri, auth=(self.user, self.password)
        )
        await self.driver.verify_connectivity()

    async def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()

    async def check_completeness(self) -> dict[str, Any]:
        """Verify required fields are present on nodes."""
        logger.info("Checking data completeness")

        checks = {
            "Contract": ["reference_number", "procuring_entity"],
            "Contractor": ["name"],
            "Agency": ["name"],
            "Politician": ["name", "position"],
            "Municipality": ["psgc_code", "name"],
        }

        results = {}

        async with self.driver.session(database=self.database) as session:
            for node_type, required_fields in checks.items():
                for field in required_fields:
                    query = f"""
                    MATCH (n:{node_type})
                    WHERE n.{field} IS NULL OR n.{field} = ''
                    RETURN count(n) as missing_count
                    """

                    try:
                        result = await session.run(query)
                        record = await result.single()
                        missing = record["missing_count"] if record else 0

                        results[f"{node_type}.{field}"] = {
                            "missing": missing,
                            "status": "PASS" if missing == 0 else "FAIL",
                        }

                        if missing > 0:
                            logger.warning(
                                f"{node_type}.{field}: {missing} nodes missing field"
                            )

                    except Exception as e:
                        logger.error(
                            f"Completeness check error for {node_type}.{field}: {e}"
                        )
                        results[f"{node_type}.{field}"] = {"error": str(e)}

        return results

    async def check_referential_integrity(self) -> dict[str, Any]:
        """Verify all edges reference existing nodes."""
        logger.info("Checking referential integrity")

        # Check for dangling edges
        query = """
        MATCH ()-[r]->()
        WHERE startNode(r) IS NULL OR endNode(r) IS NULL
        RETURN type(r) as rel_type, count(r) as dangling_count
        """

        results = {}

        async with self.driver.session(database=self.database) as session:
            try:
                result = await session.run(query)
                records = await result.data()

                for record in records:
                    rel_type = record["rel_type"]
                    count = record["dangling_count"]

                    results[rel_type] = {
                        "dangling": count,
                        "status": "PASS" if count == 0 else "FAIL",
                    }

                    if count > 0:
                        logger.warning(f"{rel_type}: {count} dangling edges")

                if not records:
                    results["all"] = {"status": "PASS", "dangling": 0}

            except Exception as e:
                logger.error(f"Referential integrity check error: {e}")
                results["error"] = str(e)

        return results

    async def check_duplicate_rate(self) -> dict[str, Any]:
        """Report duplicate detection statistics."""
        logger.info("Checking for duplicates")

        results = {}

        # Check for duplicate contractors by normalized name
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (c:Contractor)
            WITH toUpper(c.name) as normalized_name, collect(c) as contractors
            WHERE size(contractors) > 1
            RETURN count(*) as duplicate_groups, sum(size(contractors)) as total_duplicates
            """

            try:
                result = await session.run(query)
                record = await result.single()

                if record:
                    results["Contractor"] = {
                        "duplicate_groups": record["duplicate_groups"],
                        "total_duplicates": record["total_duplicates"],
                        "status": "WARN" if record["duplicate_groups"] > 0 else "PASS",
                    }

                    if record["duplicate_groups"] > 0:
                        logger.warning(
                            f"Found {record['duplicate_groups']} contractor duplicate groups "
                            f"({record['total_duplicates']} total duplicates)"
                        )

            except Exception as e:
                logger.error(f"Duplicate check error: {e}")
                results["Contractor"] = {"error": str(e)}

        return results

    async def check_amount_outliers(self) -> dict[str, Any]:
        """Flag contracts with amounts >3 std dev from mean."""
        logger.info("Checking for amount outliers")

        query = """
        MATCH (c:Contract)
        WHERE c.amount IS NOT NULL AND c.amount > 0
        WITH c.amount as amounts
        WITH avg(amounts) as mean, stDev(amounts) as std
        MATCH (c:Contract)
        WHERE c.amount > mean + 3 * std
        RETURN count(c) as outlier_count, collect(c.reference_number)[..10] as sample_refs
        """

        results = {}

        async with self.driver.session(database=self.database) as session:
            try:
                result = await session.run(query)
                record = await result.single()

                if record:
                    count = record["outlier_count"]
                    samples = record["sample_refs"]

                    results["Contract.amount"] = {
                        "outliers": count,
                        "sample_refs": samples,
                        "status": "WARN" if count > 0 else "PASS",
                    }

                    if count > 0:
                        logger.warning(f"Found {count} contract amount outliers")

            except Exception as e:
                logger.error(f"Outlier check error: {e}")
                results["Contract.amount"] = {"error": str(e)}

        return results

    async def generate_report(self) -> dict[str, Any]:
        """Run all validation checks and generate report."""
        logger.info("Generating validation report")

        report = {
            "completeness": await self.check_completeness(),
            "referential_integrity": await self.check_referential_integrity(),
            "duplicates": await self.check_duplicate_rate(),
            "outliers": await self.check_amount_outliers(),
        }

        # Summary
        all_checks = []
        for category, checks in report.items():
            if isinstance(checks, dict):
                for check_name, result in checks.items():
                    if isinstance(result, dict) and "status" in result:
                        all_checks.append(result["status"])

        passed = all_checks.count("PASS")
        failed = all_checks.count("FAIL")
        warned = all_checks.count("WARN")

        report["summary"] = {
            "total_checks": len(all_checks),
            "passed": passed,
            "failed": failed,
            "warned": warned,
        }

        logger.info(
            f"Validation complete: {passed} passed, {failed} failed, {warned} warnings"
        )

        return report

    def print_report(self, report: dict[str, Any]) -> None:
        """Print validation report to console."""
        print("\n" + "=" * 80)
        print("DATA QUALITY VALIDATION REPORT")
        print("=" * 80)

        summary = report.get("summary", {})
        print("\nSummary:")
        print(f"  Total checks: {summary.get('total_checks', 0)}")
        print(f"  [PASS] {summary.get('passed', 0)}")
        print(f"  [FAIL] {summary.get('failed', 0)}")
        print(f"  [WARN] {summary.get('warned', 0)}")

        for category, checks in report.items():
            if category == "summary":
                continue

            print(f"\n{category.upper()}:")

            if isinstance(checks, dict):
                for check_name, result in checks.items():
                    if isinstance(result, dict):
                        status = result.get("status", "?")
                        status_symbol = {
                            "PASS": "[PASS]",
                            "FAIL": "[FAIL]",
                            "WARN": "[WARN]",
                        }.get(status, "[?]")

                        print(f"  {status_symbol} {check_name}")

                        for key, value in result.items():
                            if key != "status":
                                print(f"      {key}: {value}")

        print("\n" + "=" * 80)


async def main():
    """Entry point for validation."""
    validator = DataValidator()

    try:
        await validator.connect()
        report = await validator.generate_report()
        validator.print_report(report)

    finally:
        await validator.close()


if __name__ == "__main__":
    asyncio.run(main())
