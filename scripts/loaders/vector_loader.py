"""Load embeddings into Neo4j vector index."""

import asyncio
import json
from pathlib import Path
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver
from config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    NEO4J_BATCH_SIZE,
    EMBEDDING_DIM,
    PROCESSED_DATA_DIR,
    setup_logging,
)

logger = setup_logging("vector_loader")


class VectorLoader:
    """Loads embeddings into Neo4j vector index."""

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
        logger.info("Neo4j connection established")

    async def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    async def create_vector_index(self, index_name: str = "entity_embeddings") -> None:
        """
        Create Neo4j vector index for embeddings.

        Uses HNSW algorithm with cosine similarity.
        """
        logger.info(f"Creating vector index: {index_name}")

        # Check if index exists
        check_query = (
            "SHOW INDEXES YIELD name WHERE name = $index_name RETURN count(*) as count"
        )

        async with self.driver.session(database=self.database) as session:
            result = await session.run(check_query, index_name=index_name)
            record = await result.single()
            exists = record["count"] > 0

            if exists:
                logger.info(f"Vector index {index_name} already exists")
                return

            # Create index
            # Note: Syntax varies by Neo4j version. This is for Neo4j 5.11+
            create_query = f"""
            CREATE VECTOR INDEX {index_name} IF NOT EXISTS
            FOR (n:EntitySummary)
            ON n.embedding
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {EMBEDDING_DIM},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """

            try:
                await session.run(create_query)
                logger.info(f"Created vector index: {index_name}")
            except Exception as e:
                logger.error(f"Failed to create vector index: {e}")
                logger.info("Attempting alternative syntax...")

                # Alternative syntax for older Neo4j versions
                alt_query = f"""
                CALL db.index.vector.createNodeIndex(
                    '{index_name}',
                    'EntitySummary',
                    'embedding',
                    {EMBEDDING_DIM},
                    'cosine'
                )
                """

                try:
                    await session.run(alt_query)
                    logger.info("Created vector index with alternative syntax")
                except Exception as e2:
                    logger.error(f"Vector index creation failed: {e2}")

    async def load_embeddings(
        self, entity_type: str, embeddings: list[dict[str, Any]]
    ) -> None:
        """
        Load embeddings as EntitySummary nodes.

        Args:
            entity_type: Type of entity (e.g., "Contractor", "Contract")
            embeddings: List of dicts with keys: entity_id, description, embedding
        """
        if not embeddings:
            logger.warning(f"No embeddings to load for {entity_type}")
            return

        logger.info(f"Loading {len(embeddings)} {entity_type} embeddings")

        query = """
        UNWIND $records AS record
        MERGE (s:EntitySummary {entity_id: record.entity_id})
        SET s.entity_type = record.entity_type,
            s.description = record.description,
            s.embedding = record.embedding
        """

        # Prepare records
        records = [
            {
                "entity_id": emb.get("entity_id"),
                "entity_type": entity_type,
                "description": emb.get("description", ""),
                "embedding": emb.get("embedding", []),
            }
            for emb in embeddings
            if emb.get("entity_id") and emb.get("embedding")
        ]

        loaded = 0
        batch_size = min(NEO4J_BATCH_SIZE, 100)  # Smaller batches for embeddings

        async with self.driver.session(database=self.database) as session:
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]

                try:
                    result = await session.run(query, records=batch)
                    await result.consume()
                    loaded += len(batch)

                    if loaded % 1000 == 0:
                        logger.info(f"Loaded {loaded}/{len(records)} embeddings")

                except Exception as e:
                    logger.error(f"Batch embedding load error: {e}")

        logger.info(f"Completed loading {loaded} {entity_type} embeddings")

    async def load_from_files(self, data_dir: Path | None = None) -> None:
        """Load embeddings from processed JSONL files."""
        if data_dir is None:
            data_dir = PROCESSED_DATA_DIR

        logger.info(f"Loading embeddings from {data_dir}")

        # Look for embedding files (would be generated by transform step)
        embedding_files = list(data_dir.rglob("*_embeddings_*.jsonl"))

        if not embedding_files:
            logger.warning("No embedding files found")
            return

        for filepath in embedding_files:
            logger.info(f"Loading embeddings from {filepath.name}")

            # Extract entity type from filename
            # Expected format: <entity_type>_embeddings_<timestamp>.jsonl
            entity_type = filepath.stem.split("_embeddings_")[0].capitalize()

            # Load records
            embeddings = []
            with open(filepath, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        embeddings.append(json.loads(line))

            await self.load_embeddings(entity_type, embeddings)


async def main():
    """Entry point for vector loader."""
    loader = VectorLoader()

    try:
        await loader.connect()
        await loader.create_vector_index()
        await loader.load_from_files()
    finally:
        await loader.close()


if __name__ == "__main__":
    asyncio.run(main())
