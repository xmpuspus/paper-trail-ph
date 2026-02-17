"""Generate text embeddings for GraphRAG."""

import asyncio
from typing import Any

from config import (
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    EMBEDDING_BATCH_SIZE,
    OPENAI_API_KEY,
    setup_logging,
)

logger = setup_logging("embeddings")


def generate_entity_descriptions(
    nodes: list[dict[str, Any]], node_type: str
) -> list[str]:
    """
    Generate natural language descriptions for entities.

    These descriptions will be embedded for GraphRAG semantic search.
    """
    logger.info(f"Generating descriptions for {len(nodes)} {node_type} nodes")

    descriptions = []

    for node in nodes:
        if node_type == "Contractor":
            desc = _describe_contractor(node)
        elif node_type == "Agency":
            desc = _describe_agency(node)
        elif node_type == "Contract":
            desc = _describe_contract(node)
        elif node_type == "Politician":
            desc = _describe_politician(node)
        elif node_type == "Municipality":
            desc = _describe_municipality(node)
        elif node_type == "PoliticalFamily":
            desc = _describe_political_family(node)
        else:
            # Generic description
            desc = f"{node_type}: " + ", ".join(
                f"{k}={v}" for k, v in node.items() if k not in ["id", "embedding"]
            )

        descriptions.append(desc)

    return descriptions


def _describe_contractor(node: dict[str, Any]) -> str:
    """Generate description for Contractor node."""
    name = node.get("contractor_name", node.get("name", ""))
    classification = node.get("classification", "")
    address = node.get("address", "")
    total_contracts = node.get("total_contracts", 0)
    total_value = node.get("total_value", 0)

    parts = [f"{name} is a contractor"]

    if classification:
        parts.append(f"classified as {classification}")

    if address:
        parts.append(f"based in {address}")

    if total_contracts:
        parts.append(f"with {total_contracts} contracts")

    if total_value:
        parts.append(f"worth PHP {total_value:,.2f}")

    return " ".join(parts) + "."


def _describe_agency(node: dict[str, Any]) -> str:
    """Generate description for Agency node."""
    name = node.get("name", "")
    agency_type = node.get("type", "")
    department = node.get("department", "")
    budget = node.get("annual_budget", 0)

    parts = [f"{name}"]

    if agency_type:
        parts.append(f"is a {agency_type} agency")

    if department:
        parts.append(f"under {department}")

    if budget:
        parts.append(f"with annual budget of PHP {budget:,.2f}")

    return " ".join(parts) + "."


def _describe_contract(node: dict[str, Any]) -> str:
    """Generate description for Contract node."""
    ref = node.get("reference_number", "")
    title = node.get("title", "")
    amount = node.get("amount", 0)
    method = node.get("procurement_method", "")
    date = node.get("award_date", "")

    parts = [f"Contract {ref}"]

    if title:
        parts.append(f"for {title}")

    if amount:
        parts.append(f"worth PHP {amount:,.2f}")

    if method:
        parts.append(f"via {method}")

    if date:
        parts.append(f"awarded on {date}")

    return " ".join(parts) + "."


def _describe_politician(node: dict[str, Any]) -> str:
    """Generate description for Politician node."""
    name = node.get("name", "")
    position = node.get("position", "")
    province = node.get("province", "")
    party = node.get("party", "")
    term = node.get("term", "")

    parts = [f"{name}"]

    if position:
        parts.append(f"serves as {position}")

    if province:
        parts.append(f"representing {province}")

    if party:
        parts.append(f"of {party}")

    if term:
        parts.append(f"during {term}")

    return " ".join(parts) + "."


def _describe_municipality(node: dict[str, Any]) -> str:
    """Generate description for Municipality node."""
    name = node.get("name", "")
    province = node.get("province", "")
    region = node.get("region", "")
    population = node.get("population", 0)

    parts = [f"{name}"]

    if province:
        parts.append(f"in {province}")

    if region:
        parts.append(f", {region}")

    if population:
        parts.append(f"with population of {population:,}")

    return " ".join(parts) + "."


def _describe_political_family(node: dict[str, Any]) -> str:
    """Generate description for PoliticalFamily node."""
    surname = node.get("surname", node.get("name", ""))
    province = node.get("province", "")
    member_count = node.get("member_count", 0)
    dynasty_score = node.get("dynasty_score", 0)

    parts = [f"The {surname} family"]

    if province:
        parts.append(f"in {province}")

    if member_count:
        parts.append(f"has {member_count} members in public office")

    if dynasty_score:
        parts.append(f"with dynasty score of {dynasty_score}")

    return " ".join(parts) + "."


async def embed_descriptions(
    descriptions: list[str], model: str = EMBEDDING_MODEL
) -> list[list[float]]:
    """
    Generate embeddings for descriptions.

    Supports both local (sentence-transformers) and OpenAI models.
    """
    logger.info(
        f"Generating embeddings for {len(descriptions)} descriptions using {model}"
    )

    if model == "all-MiniLM-L6-v2":
        return await _embed_local(descriptions, model)
    elif model.startswith("text-embedding"):
        return await _embed_openai(descriptions, model)
    else:
        logger.warning(f"Unknown embedding model: {model}, using local")
        return await _embed_local(descriptions, "all-MiniLM-L6-v2")


async def _embed_local(descriptions: list[str], model: str) -> list[list[float]]:
    """Generate embeddings using local sentence-transformers model."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error(
            "sentence-transformers not installed. Run: pip install sentence-transformers"
        )
        return []

    logger.info(f"Loading local model: {model}")
    embedder = SentenceTransformer(model)

    # Batch encode
    embeddings = []

    for i in range(0, len(descriptions), EMBEDDING_BATCH_SIZE):
        batch = descriptions[i : i + EMBEDDING_BATCH_SIZE]
        batch_embeddings = embedder.encode(batch, show_progress_bar=False)
        embeddings.extend(batch_embeddings.tolist())

        if (i // EMBEDDING_BATCH_SIZE + 1) % 10 == 0:
            logger.info(f"Embedded {i + len(batch)}/{len(descriptions)} descriptions")

    logger.info(f"Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

    return embeddings


async def _embed_openai(descriptions: list[str], model: str) -> list[list[float]]:
    """Generate embeddings using OpenAI API."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set")
        return []

    try:
        import openai
    except ImportError:
        logger.error("openai not installed. Run: pip install openai")
        return []

    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

    embeddings = []

    for i in range(0, len(descriptions), EMBEDDING_BATCH_SIZE):
        batch = descriptions[i : i + EMBEDDING_BATCH_SIZE]

        try:
            response = await client.embeddings.create(model=model, input=batch)

            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

            if (i // EMBEDDING_BATCH_SIZE + 1) % 10 == 0:
                logger.info(
                    f"Embedded {i + len(batch)}/{len(descriptions)} descriptions"
                )

        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            # Return zeros for failed batch
            embeddings.extend([[0.0] * EMBEDDING_DIM] * len(batch))

        # Rate limiting
        await asyncio.sleep(0.1)

    logger.info(f"Generated {len(embeddings)} embeddings (dim={EMBEDDING_DIM})")

    return embeddings


async def generate_and_embed(
    nodes: list[dict[str, Any]], node_type: str, model: str = EMBEDDING_MODEL
) -> list[dict[str, Any]]:
    """
    Generate descriptions and embeddings for nodes.

    Returns nodes with added 'description' and 'embedding' fields.
    """
    logger.info(f"Generating descriptions and embeddings for {node_type}")

    # Generate descriptions
    descriptions = generate_entity_descriptions(nodes, node_type)

    # Generate embeddings
    embeddings = await embed_descriptions(descriptions, model)

    # Add to nodes
    for node, desc, emb in zip(nodes, descriptions, embeddings):
        node["description"] = desc
        node["embedding"] = emb

    return nodes
