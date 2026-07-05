# Data Pipeline

ETL pipeline and graph analysis for Philippine government procurement data.

## Quick Start

```bash
pip3 install -r ../backend/requirements.txt

# Load graph data into Neo4j
python3 pipeline.py bootstrap

# Run analysis
python3 pipeline.py analyze

# Full pipeline from raw sources
python3 pipeline.py collect --source all --since 2020
python3 pipeline.py transform --deduplicate --derive-edges
python3 pipeline.py load --target all
python3 pipeline.py validate --report
```

## Commands

### collect

Download and parse data from government sources.

```bash
python3 pipeline.py collect --source philgeps --since 2020
python3 pipeline.py collect --source congress
python3 pipeline.py collect --source psgc
python3 pipeline.py collect --source dynasties
python3 pipeline.py collect --source all --since 2020
```

PhilGEPS and PSGC require manual XLSX downloads — no API available. Place files in:
- `data/raw/philgeps/` — award notices, bid notices, contractor registry
- `data/raw/psgc/` — PSA geographic codes

### transform

Normalize entities and derive implicit relationships.

```bash
python3 pipeline.py transform --deduplicate         # Jaro-Winkler fuzzy matching
python3 pipeline.py transform --derive-edges         # Co-bidding, split contracts
python3 pipeline.py transform --deduplicate --derive-edges
```

### load

Load processed data into Neo4j and vector indexes.

```bash
python3 pipeline.py load --target neo4j
python3 pipeline.py load --target vectors
python3 pipeline.py load --target all
```

### analyze

Run graph analysis modules against Neo4j.

```bash
python3 pipeline.py analyze                          # All modules
python3 pipeline.py analyze --module concentration   # HHI, monopoly, single-bidder
python3 pipeline.py analyze --module networks        # Co-bidding rings, loops
python3 pipeline.py analyze --module dynasties       # Political family connections
python3 pipeline.py analyze --module red-flags       # Splitting, round amounts, rigging
python3 pipeline.py analyze --json-output            # Machine-readable output
```

Each module is also runnable standalone:

```bash
python3 -m analysis.concentration
python3 -m analysis.networks
python3 -m analysis.dynasties
python3 -m analysis.red_flags
```

### validate

```bash
python3 pipeline.py validate --report    # Full quality report
python3 pipeline.py validate             # Basic checks only
```

### Other

```bash
python3 pipeline.py stats       # Coverage statistics
python3 pipeline.py status      # Data inventory
python3 pipeline.py bootstrap   # Load graph from cypher/seed.cypher
```

## Directory Structure

```
scripts/
├── pipeline.py            # CLI entrypoint
├── config.py              # Shared config (Neo4j, paths, thresholds)
├── collectors/            # Data source collectors
│   ├── philgeps.py       # PhilGEPS procurement (XLSX parsing)
│   ├── open_congress.py  # Open Congress API
│   ├── psgc.py           # PSA geographic codes
│   └── dynasties.py      # Dynasty detection from official records
├── transformers/          # Data transformation
│   ├── normalize.py      # Entity resolution (Jaro-Winkler)
│   ├── relationships.py  # Co-bidding, split contracts, surname matching
│   └── embeddings.py     # Text embeddings for vector search
├── loaders/               # Data loading
│   ├── neo4j_loader.py   # Neo4j graph loading
│   └── vector_loader.py  # Vector index loading
├── quality/               # Data quality
│   ├── validate.py       # Completeness, integrity, outliers
│   └── stats.py          # Coverage and freshness reporting
└── analysis/              # Graph analysis
    ├── concentration.py  # Agency market concentration (HHI)
    ├── networks.py       # Bidding networks and collusion patterns
    ├── dynasties.py      # Political family connections
    └── red_flags.py      # Procurement red flags
```

## Configuration

Environment variables (set in `.env`):

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Optional
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Data Flow

```
COLLECT → data/raw/{source}/
    ↓
TRANSFORM → data/processed/{source}/
    ↓
LOAD → Neo4j graph database
    ↓
ANALYZE → Formatted reports / JSON
```

## Manual Downloads

### PhilGEPS

1. Go to https://data.gov.ph
2. Search "PhilGEPS"
3. Download award notices, bid notices, contractor registry (XLSX)
4. Place in `data/raw/philgeps/`

### PSGC

1. Go to https://psa.gov.ph/classification/psgc
2. Download latest publication (XLSX or CSV)
3. Place in `data/raw/psgc/`

## Data Sources

All data used in this project comes from Philippine government public records and open data portals.

| Source | URL | Data | Access Method | License |
|--------|-----|------|---------------|---------|
| DPWH Transparency Portal | https://transparency.dpwh.gov.ph | Infrastructure projects, budgets, contractors, GPS | HuggingFace pre-scraped dataset | CC0 1.0 |
| PhilGEPS | https://notices.philgeps.gov.ph | Procurement notices, awards, contracts | Excel download (manual) | Public record |
| Open Congress PH | https://open-congress-api.bettergov.ph | Legislators, bills, committees | REST API | Open data |
| PSA PSGC | https://psa.gov.ph/classification/psgc | Geographic codes, provinces, municipalities | Excel download | Public record |
| COMELEC | https://comelec.gov.ph | Election results, candidates | Scanned PDFs | Public record |
| COA | https://coa.gov.ph/reports/annual-audit-reports | Audit findings, recommendations | PDF reports | Public record |

### Source Details

**DPWH Transparency Portal** — The DPWH API is behind Cloudflare protection, so we use a CC0-licensed pre-scraped Parquet dataset maintained by BetterGov.PH on HuggingFace: https://huggingface.co/datasets/bettergovph/dpwh-transparency-data. Contains 248K+ infrastructure contracts (2016-2026) with budgets, contractors, GPS coordinates, and completion status. Original scraper by @csiiiv.

**PhilGEPS** — The Philippine Government Electronic Procurement System has no public API. Data must be manually downloaded as XLSX files from https://open.philgeps.gov.ph or https://data.gov.ph. Includes award notices, bid notices, and contractor registry.

**Open Congress PH** — REST API maintained by BetterGov.PH volunteers at https://open-congress-api.bettergov.ph/api/v1 (docs: /api/scalar). Coverage: Congresses 8-20, 165K+ bills, 1.1K+ legislators, 200 committees. Data is manually encoded — may contain inaccuracies per maintainer. Rate-limited to 2 req/s.

**PSA PSGC** — The Philippine Standard Geographic Code is published by the Philippine Statistics Authority as Excel files. Provides the canonical geographic hierarchy (region > province > municipality > barangay) with 10-digit codes. Also available via https://openstat.psa.gov.ph.

**COMELEC** — Election results published by the Commission on Elections. Primarily scanned PDFs, requiring OCR for extraction. Used for dynasty detection via surname + province matching.

**COA** — Commission on Audit annual audit reports. Unstructured PDF reports covering government agency spending, findings, and recommendations. Phase 2 data source (pilot with 10-20 reports).
