"""Shared configuration for paper-trail-ph data pipeline."""

import os
import logging
from pathlib import Path

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CYPHER_DIR = PROJECT_ROOT / "cypher"

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# API endpoints
OPEN_CONGRESS_BASE_URL = "https://open-congress-api.bettergov.ph/api/v1"
PHILGEPS_DATA_PORTAL = "https://data.gov.ph"
PSA_PSGC_URL = "https://psa.gov.ph/classification/psgc"

# Rate limiting
CONGRESS_API_RATE_LIMIT = 2  # requests per second
HTTP_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # exponential backoff multiplier

# Batch processing
NEO4J_BATCH_SIZE = 1000
EMBEDDING_BATCH_SIZE = 32

# Entity resolution
FUZZY_MATCH_THRESHOLD_AUTO = 0.92  # auto-merge above this
FUZZY_MATCH_THRESHOLD_REVIEW = 0.85  # flag for review above this

# LLM and embeddings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "all-MiniLM-L6-v2"
)  # or "text-embedding-3-small"
EMBEDDING_DIM = 384 if EMBEDDING_MODEL == "all-MiniLM-L6-v2" else 1536

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(name: str = "pipeline") -> logging.Logger:
    """Setup logging with consistent format."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(PROJECT_ROOT / "pipeline.log"),
        ],
    )
    return logging.getLogger(name)


def ensure_data_dirs() -> None:
    """Create data directories if they don't exist."""
    directories = [
        RAW_DATA_DIR / "philgeps",
        RAW_DATA_DIR / "congress",
        RAW_DATA_DIR / "psgc",
        RAW_DATA_DIR / "dynasties",
        PROCESSED_DATA_DIR / "philgeps",
        PROCESSED_DATA_DIR / "congress",
        PROCESSED_DATA_DIR / "psgc",
        PROCESSED_DATA_DIR / "dynasties",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
