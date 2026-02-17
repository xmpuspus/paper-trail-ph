#!/usr/bin/env python3
"""
Paper Trail PH Data Pipeline

CLI for collecting, transforming, and loading Philippine government data.
"""

import asyncio
import sys
from pathlib import Path

import click

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import ensure_data_dirs, setup_logging
from collectors.philgeps import PhilGEPSCollector
from collectors.open_congress import OpenCongressCollector
from collectors.psgc import PSGCCollector
from collectors.dynasties import DynastyDetector
from loaders.neo4j_loader import Neo4jLoader
from loaders.vector_loader import VectorLoader
from quality.validate import DataValidator
from quality.stats import StatsReporter
from analysis.concentration import ConcentrationAnalyzer
from analysis.networks import NetworkAnalyzer
from analysis.dynasties import DynastyAnalyzer
from analysis.red_flags import RedFlagAnalyzer

logger = setup_logging("pipeline")


@click.group()
def cli():
    """Paper Trail PH Data Pipeline."""
    ensure_data_dirs()


@cli.command()
@click.option(
    "--source",
    required=True,
    type=click.Choice(["philgeps", "congress", "psgc", "dynasties", "all"]),
)
@click.option("--since", default=2020, type=int, help="Start year for data collection")
def collect(source: str, since: int):
    """Collect data from government sources."""
    logger.info(f"Starting data collection: {source}")

    async def run_collection():
        if source == "philgeps" or source == "all":
            collector = PhilGEPSCollector()
            await collector.collect(since_year=since)

        if source == "congress" or source == "all":
            collector = OpenCongressCollector()
            await collector.collect_all()

        if source == "psgc" or source == "all":
            collector = PSGCCollector()
            await collector.collect()

        if source == "dynasties" or source == "all":
            detector = DynastyDetector()
            await detector.collect()

    asyncio.run(run_collection())
    logger.info("Collection complete")


@cli.command()
@click.option("--deduplicate", is_flag=True, help="Run entity deduplication")
@click.option("--derive-edges", is_flag=True, help="Derive implicit relationships")
def transform(deduplicate: bool, derive_edges: bool):
    """Transform and normalize collected data."""
    logger.info("Starting data transformation")

    if deduplicate:
        logger.info("Running entity deduplication")
        from transformers.normalize import fuzzy_match_contractors, merge_entities
        from config import PROCESSED_DATA_DIR
        import json

        # Load contractor data
        philgeps_dir = PROCESSED_DATA_DIR / "philgeps"
        contract_files = sorted(philgeps_dir.glob("contracts_*.jsonl"))

        if contract_files:
            logger.info(f"Loading contracts from {contract_files[-1].name}")

            contracts = []
            with open(contract_files[-1], encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        contracts.append(json.loads(line))

            # Extract unique contractors
            contractors = {}
            for contract in contracts:
                name = contract.get("contractor_name")
                if name and name not in contractors:
                    contractors[name] = {
                        "contractor_name": name,
                        "name": name,
                    }

            contractor_list = list(contractors.values())
            logger.info(f"Found {len(contractor_list)} unique contractors")

            # Find fuzzy matches
            matches = fuzzy_match_contractors(contractor_list)

            # Merge
            merge_results = merge_entities(matches)

            # Save merge results
            merge_file = philgeps_dir / "contractor_merges.json"
            with open(merge_file, "w") as f:
                json.dump(merge_results, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved merge results to {merge_file}")
            logger.info(f"Auto-merged: {len(merge_results['auto_merged'])}")
            logger.info(f"Review required: {len(merge_results['review_required'])}")

        else:
            logger.warning("No contract data found. Run collect first.")

    if derive_edges:
        logger.info("Deriving implicit relationships")
        from transformers.relationships import (
            derive_co_bidding,
            derive_split_contracts,
        )
        from config import PROCESSED_DATA_DIR
        import json

        # Load contract data
        philgeps_dir = PROCESSED_DATA_DIR / "philgeps"
        contract_files = sorted(philgeps_dir.glob("contracts_*.jsonl"))

        if contract_files:
            contracts = []
            with open(contract_files[-1], encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        contracts.append(json.loads(line))

            # Derive co-bidding
            co_bidding = derive_co_bidding(contracts)
            co_bidding_file = philgeps_dir / "co_bidding_edges.jsonl"
            with open(co_bidding_file, "w") as f:
                for edge in co_bidding:
                    f.write(json.dumps(edge, ensure_ascii=False) + "\n")
            logger.info(f"Saved {len(co_bidding)} co-bidding edges")

            # Detect split contracts
            split_contracts = derive_split_contracts(contracts)
            split_file = philgeps_dir / "split_contracts.jsonl"
            with open(split_file, "w") as f:
                for group in split_contracts:
                    f.write(json.dumps(group, ensure_ascii=False) + "\n")
            logger.info(
                f"Detected {len(split_contracts)} potential split contract groups"
            )

        else:
            logger.warning("No contract data found. Run collect first.")

    logger.info("Transformation complete")


@cli.command()
@click.option("--target", required=True, type=click.Choice(["neo4j", "vectors", "all"]))
def load(target: str):
    """Load data into Neo4j and vector indexes."""
    logger.info(f"Starting data load: {target}")

    async def run_load():
        if target == "neo4j" or target == "all":
            loader = Neo4jLoader()
            try:
                await loader.connect()
                await loader.load_schema()
                await loader.load_full_dataset()
            finally:
                await loader.close()

        if target == "vectors" or target == "all":
            loader = VectorLoader()
            try:
                await loader.connect()
                await loader.create_vector_index()
                await loader.load_from_files()
            finally:
                await loader.close()

    asyncio.run(run_load())
    logger.info("Load complete")


@cli.command()
@click.option("--report", is_flag=True, help="Generate validation report")
def validate(report: bool):
    """Run data quality validation checks."""
    logger.info("Starting data validation")

    async def run_validation():
        validator = DataValidator()
        try:
            await validator.connect()

            if report:
                validation_report = await validator.generate_report()
                validator.print_report(validation_report)
            else:
                # Just run basic checks
                completeness = await validator.check_completeness()
                logger.info(f"Completeness checks: {len(completeness)}")

        finally:
            await validator.close()

    asyncio.run(run_validation())


@cli.command()
def stats():
    """Generate coverage and statistics report."""
    logger.info("Generating statistics")

    async def run_stats():
        reporter = StatsReporter()
        try:
            await reporter.connect()
            stats_report = await reporter.generate_stats()
            reporter.print_stats(stats_report)
        finally:
            await reporter.close()

    asyncio.run(run_stats())


@cli.command()
@click.option(
    "--module",
    type=click.Choice(["concentration", "networks", "dynasties", "red-flags", "all"]),
    default="all",
)
@click.option(
    "--json-output", is_flag=True, help="Output raw JSON instead of formatted report"
)
def analyze(module: str, json_output: bool):
    """Run graph analysis to surface procurement patterns and red flags."""
    import json as json_mod

    logger.info(f"Running analysis: {module}")

    analyzers = {
        "concentration": ("Procurement Concentration", ConcentrationAnalyzer),
        "networks": ("Bidding Networks", NetworkAnalyzer),
        "dynasties": ("Dynasty Connections", DynastyAnalyzer),
        "red-flags": ("Red Flags", RedFlagAnalyzer),
    }

    async def run_analysis():
        targets = analyzers if module == "all" else {module: analyzers[module]}

        for key, (label, cls) in targets.items():
            logger.info(f"Running {label} analysis")
            analyzer = cls()
            try:
                await analyzer.connect()
                results = await analyzer.run_all()

                if json_output:
                    print(json_mod.dumps(results, indent=2, default=str))
                else:
                    analyzer.print_report(results)
            finally:
                await analyzer.close()

    asyncio.run(run_analysis())
    logger.info("Analysis complete")


@cli.command()
def bootstrap():
    """Load initial graph data from cypher/seed.cypher."""
    logger.info("Loading graph data")

    async def run_bootstrap():
        loader = Neo4jLoader()
        try:
            await loader.connect()
            await loader.load_schema()
            await loader.load_seed()
        finally:
            await loader.close()

    asyncio.run(run_bootstrap())
    logger.info("Graph data loaded")


@cli.command()
def status():
    """Show pipeline status and data inventory."""
    from config import PROCESSED_DATA_DIR

    print("\n" + "=" * 80)
    print("PIPELINE STATUS")
    print("=" * 80)

    # Check each data source
    sources = {
        "PhilGEPS": PROCESSED_DATA_DIR / "philgeps",
        "Congress": PROCESSED_DATA_DIR / "congress",
        "PSGC": PROCESSED_DATA_DIR / "psgc",
        "Dynasties": PROCESSED_DATA_DIR / "dynasties",
    }

    for source_name, source_dir in sources.items():
        print(f"\n{source_name}:")

        if not source_dir.exists():
            print("  [NOT COLLECTED]")
            continue

        # Count JSONL files and records
        jsonl_files = list(source_dir.glob("*.jsonl"))

        if not jsonl_files:
            print("  [NO DATA]")
            continue

        total_records = 0
        latest_file = None
        latest_mtime = 0

        for filepath in jsonl_files:
            record_count = sum(1 for line in open(filepath) if line.strip())
            total_records += record_count

            mtime = filepath.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_file = filepath

        import datetime

        last_update = datetime.datetime.fromtimestamp(latest_mtime).strftime(
            "%Y-%m-%d %H:%M"
        )

        print(f"  Files: {len(jsonl_files)}")
        print(f"  Total records: {total_records:,}")
        print(f"  Last update: {last_update}")
        print(f"  Latest file: {latest_file.name if latest_file else 'None'}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    cli()
