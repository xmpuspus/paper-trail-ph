"""Bulk load data into Neo4j graph database."""

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator

from neo4j import AsyncGraphDatabase, AsyncDriver
from config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    NEO4J_BATCH_SIZE,
    CYPHER_DIR,
    PROCESSED_DATA_DIR,
    setup_logging,
)

logger = setup_logging("neo4j_loader")


def chunked(iterable: list, size: int) -> AsyncIterator[list]:
    """Yield successive chunks from iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


class Neo4jLoader:
    """Loads data into Neo4j graph database."""

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

        # Test connection
        await self.driver.verify_connectivity()
        logger.info("Neo4j connection established")

    async def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    async def load_schema(self) -> None:
        """Load schema (constraints and indexes) from cypher/schema.cypher."""
        schema_file = CYPHER_DIR / "schema.cypher"

        if not schema_file.exists():
            logger.warning(f"Schema file not found: {schema_file}")
            return

        logger.info("Loading schema")

        with open(schema_file) as f:
            schema_cypher = f.read()

        # Split by semicolon and execute each statement
        statements = [s.strip() for s in schema_cypher.split(";") if s.strip()]

        async with self.driver.session(database=self.database) as session:
            for statement in statements:
                try:
                    await session.run(statement)
                    logger.debug(f"Executed: {statement[:100]}...")
                except Exception as e:
                    logger.warning(f"Schema statement error: {e}")

        logger.info(f"Schema loaded: {len(statements)} statements")

    async def load_seed(self) -> None:
        """Load initial graph data from cypher/seed.cypher."""
        seed_file = CYPHER_DIR / "seed.cypher"

        if not seed_file.exists():
            logger.warning(f"Cypher file not found: {seed_file}")
            return

        logger.info("Loading graph data from seed.cypher")

        with open(seed_file) as f:
            seed_cypher = f.read()

        statements = [s.strip() for s in seed_cypher.split(";") if s.strip()]

        async with self.driver.session(database=self.database) as session:
            for i, statement in enumerate(statements):
                try:
                    await session.run(statement)
                    if (i + 1) % 10 == 0:
                        logger.info(f"Executed {i + 1}/{len(statements)} statements")
                except Exception as e:
                    logger.error(f"Statement error: {e}")
                    logger.debug(f"Failed: {statement[:200]}")

        logger.info(f"Graph data loaded: {len(statements)} statements")

    async def load_nodes(
        self, node_type: str, records: list[dict[str, Any]], unique_key: str
    ) -> None:
        """
        Batch load nodes using MERGE.

        Args:
            node_type: Node label (e.g., "Contractor")
            records: List of node property dicts
            unique_key: Property to use for MERGE (e.g., "reference_number")
        """
        if not records:
            logger.warning(f"No records to load for {node_type}")
            return

        logger.info(f"Loading {len(records)} {node_type} nodes")

        # Build MERGE query
        query = f"""
        UNWIND $records AS record
        MERGE (n:{node_type} {{{unique_key}: record.{unique_key}}})
        SET n += record
        """

        loaded = 0
        errors = 0

        async with self.driver.session(database=self.database) as session:
            for batch in chunked(records, NEO4J_BATCH_SIZE):
                try:
                    result = await session.run(query, records=batch)
                    await result.consume()
                    loaded += len(batch)

                    if loaded % 10000 == 0:
                        logger.info(f"Loaded {loaded}/{len(records)} {node_type} nodes")

                except Exception as e:
                    logger.error(f"Batch load error: {e}")
                    errors += len(batch)

        logger.info(f"Completed {node_type} nodes: {loaded} loaded, {errors} errors")

    async def load_edges(
        self,
        edge_type: str,
        records: list[dict[str, Any]],
        from_label: str,
        to_label: str,
        from_key: str,
        to_key: str,
        from_field: str,
        to_field: str,
    ) -> None:
        """
        Batch load edges using MERGE.

        Args:
            edge_type: Relationship type (e.g., "AWARDED_TO")
            records: List of edge property dicts
            from_label: Source node label
            to_label: Target node label
            from_key: Source node unique property name
            to_key: Target node unique property name
            from_field: Field in record containing source identifier
            to_field: Field in record containing target identifier
        """
        if not records:
            logger.warning(f"No records to load for {edge_type}")
            return

        logger.info(f"Loading {len(records)} {edge_type} edges")

        # Build MERGE query
        query = f"""
        UNWIND $records AS record
        MATCH (from:{from_label} {{{from_key}: record.{from_field}}})
        MATCH (to:{to_label} {{{to_key}: record.{to_field}}})
        MERGE (from)-[r:{edge_type}]->(to)
        SET r += record
        """

        loaded = 0
        errors = 0

        async with self.driver.session(database=self.database) as session:
            for batch in chunked(records, NEO4J_BATCH_SIZE):
                try:
                    result = await session.run(query, records=batch)
                    await result.consume()
                    loaded += len(batch)

                    if loaded % 10000 == 0:
                        logger.info(f"Loaded {loaded}/{len(records)} {edge_type} edges")

                except Exception as e:
                    logger.error(f"Batch edge load error: {e}")
                    errors += len(batch)

        logger.info(f"Completed {edge_type} edges: {loaded} loaded, {errors} errors")

    def _load_jsonl(self, filepath: Path) -> list[dict[str, Any]]:
        """Load records from JSONL file."""
        records = []

        with open(filepath, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        return records

    async def _load_dpwh_data(self, dpwh_dir: Path) -> None:
        """Load DPWH transparency data into graph."""
        # Load pre-extracted agencies
        agency_files = sorted(dpwh_dir.glob("agencies_*.jsonl"))
        if agency_files:
            agencies = self._load_jsonl(agency_files[-1])
            await self.load_nodes("Agency", agencies, "name")

        # Load pre-extracted contractors
        contractor_files = sorted(dpwh_dir.glob("contractors_*.jsonl"))
        if contractor_files:
            contractors = self._load_jsonl(contractor_files[-1])
            await self.load_nodes("Contractor", contractors, "name")

        # Load contracts and edges
        contract_files = sorted(dpwh_dir.glob("contracts_*.jsonl"))
        if contract_files:
            contracts = self._load_jsonl(contract_files[-1])
            await self.load_nodes("Contract", contracts, "reference_number")

            # PROCURED edges (Agency -> Contract)
            procured_edges = [
                {
                    "agency_name": c.get("procuring_entity"),
                    "contract_ref": c.get("reference_number"),
                }
                for c in contracts
                if c.get("procuring_entity") and c.get("reference_number")
            ]
            await self.load_edges(
                "PROCURED", procured_edges,
                "Agency", "Contract",
                "name", "reference_number",
                "agency_name", "contract_ref",
            )

            # AWARDED_TO edges (Contract -> Contractor)
            awarded_edges = [
                {
                    "contract_ref": c.get("reference_number"),
                    "contractor_name": c.get("contractor_name"),
                    "amount": c.get("amount"),
                    "start_date": c.get("start_date"),
                }
                for c in contracts
                if c.get("reference_number") and c.get("contractor_name")
            ]
            await self.load_edges(
                "AWARDED_TO", awarded_edges,
                "Contract", "Contractor",
                "reference_number", "name",
                "contract_ref", "contractor_name",
            )

            logger.info(f"DPWH data loaded: {len(contracts)} contracts")
        else:
            logger.warning("No DPWH contract data found. Run 'pipeline.py collect --source dpwh' first.")

    async def _load_philgeps_data(self, philgeps_dir: Path) -> None:
        """Load PhilGEPS procurement data into graph."""
        contract_files = sorted(philgeps_dir.glob("contracts_*.jsonl"))
        if not contract_files:
            return

        contracts = self._load_jsonl(contract_files[-1])

        # Extract unique agencies
        agencies = {}
        for contract in contracts:
            agency_name = contract.get("procuring_entity")
            if agency_name and agency_name not in agencies:
                agencies[agency_name] = {"name": agency_name, "type": "unknown"}

        await self.load_nodes("Agency", list(agencies.values()), "name")

        # Extract unique contractors
        contractors = {}
        for contract in contracts:
            contractor_name = contract.get("contractor_name")
            if contractor_name and contractor_name not in contractors:
                contractors[contractor_name] = {
                    "contractor_name": contractor_name,
                    "name": contractor_name,
                }

        await self.load_nodes("Contractor", list(contractors.values()), "name")
        await self.load_nodes("Contract", contracts, "reference_number")

        # PROCURED edges
        procured_edges = [
            {
                "agency_name": c.get("procuring_entity"),
                "contract_ref": c.get("reference_number"),
            }
            for c in contracts
            if c.get("procuring_entity") and c.get("reference_number")
        ]
        await self.load_edges(
            "PROCURED", procured_edges,
            "Agency", "Contract",
            "name", "reference_number",
            "agency_name", "contract_ref",
        )

        # AWARDED_TO edges
        awarded_edges = [
            {
                "contract_ref": c.get("reference_number"),
                "contractor_name": c.get("contractor_name"),
                "amount": c.get("amount"),
                "award_date": c.get("award_date"),
            }
            for c in contracts
            if c.get("reference_number") and c.get("contractor_name")
        ]
        await self.load_edges(
            "AWARDED_TO", awarded_edges,
            "Contract", "Contractor",
            "reference_number", "name",
            "contract_ref", "contractor_name",
        )

        logger.info(f"PhilGEPS data loaded: {len(contracts)} contracts")

    async def load_full_dataset(self, data_dir: Path | None = None) -> None:
        """
        Orchestrate full dataset load from processed JSON files.

        Load order:
        1. Municipalities (for geographic references)
        2. Agencies
        3. Contractors
        4. Contracts
        5. Politicians
        6. Political families
        7. Edges
        """
        if data_dir is None:
            data_dir = PROCESSED_DATA_DIR

        logger.info(f"Loading full dataset from {data_dir}")

        # Load municipalities
        muni_files = sorted((data_dir / "psgc").glob("municipalities_*.jsonl"))
        if muni_files:
            municipalities = self._load_jsonl(muni_files[-1])
            await self.load_nodes("Municipality", municipalities, "psgc_code")

        # Load DPWH data (primary source - real transparency data)
        dpwh_dir = data_dir / "dpwh"
        if dpwh_dir.exists():
            await self._load_dpwh_data(dpwh_dir)

        # Load PhilGEPS data (supplementary procurement data)
        philgeps_dir = data_dir / "philgeps"
        if philgeps_dir.exists():
            await self._load_philgeps_data(philgeps_dir)

        # Load politicians
        member_files = sorted((data_dir / "congress").glob("members_*.jsonl"))
        if member_files:
            politicians = self._load_jsonl(member_files[-1])
            await self.load_nodes("Politician", politicians, "name")

        # Load political families
        dynasty_files = sorted((data_dir / "dynasties").glob("dynasties_*.jsonl"))
        if dynasty_files:
            dynasties = self._load_jsonl(dynasty_files[-1])
            await self.load_nodes("PoliticalFamily", dynasties, "dynasty_id")

        logger.info("Full dataset load complete")


async def main(mode: str = "seed"):
    """Entry point for Neo4j loader."""
    loader = Neo4jLoader()

    try:
        await loader.connect()

        if mode == "seed":
            await loader.load_schema()
            await loader.load_seed()
        elif mode == "full":
            await loader.load_schema()
            await loader.load_full_dataset()
        else:
            logger.error(f"Unknown mode: {mode}")

    finally:
        await loader.close()


if __name__ == "__main__":
    asyncio.run(main())
