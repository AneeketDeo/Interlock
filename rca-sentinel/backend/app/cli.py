"""CLI entry point for RCA-Sentinel management commands.

Usage:
    python -m app.cli seed     # Bootstrap ontology + synthetic data
    python -m app.cli replay   # Replay the golden scenario
    python -m app.cli bootstrap # Apply constraints + ontology only
"""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


async def cmd_seed() -> None:
    """Full seed: bootstrap graph, load ontology, generate + ingest synthetic data."""
    from app.core.database import close_timescale_client, init_timescale_client
    from app.core.redis import close_redis_client, init_redis_client
    from app.graph.bootstrap import bootstrap_graph
    from app.graph.client import close_neo4j_client, init_neo4j_client
    from app.ontology.loader import OntologyLoader

    settings = get_settings()
    logger.info("seed_starting", env=settings.app_env)

    # Initialize clients
    neo4j_client = await init_neo4j_client(settings)
    await init_redis_client(settings)
    await init_timescale_client(settings)

    try:
        # 1. Bootstrap constraints and indexes
        logger.info("step_1_bootstrap_graph")
        counts = await bootstrap_graph(neo4j_client)
        logger.info("bootstrap_complete", **counts)

        # 2. Load ontology
        logger.info("step_2_load_ontology")
        loader = OntologyLoader(neo4j_client)
        ont_counts = await loader.load()
        logger.info("ontology_loaded", **ont_counts)

        # 3. Generate and ingest synthetic data
        logger.info("step_3_generate_synthetic_data")
        from app.simulator.generator import SyntheticDataGenerator

        generator = SyntheticDataGenerator(settings)
        data = generator.generate()
        logger.info(
            "synthetic_data_generated",
            plants=len(data.get("plants", [])),
            lines=len(data.get("lines", [])),
            machines=len(data.get("machines", [])),
            sensors=len(data.get("sensors", [])),
            suppliers=len(data.get("suppliers", [])),
            material_lots=len(data.get("material_lots", [])),
        )

        # 4. Ingest into graph and TimescaleDB
        logger.info("step_4_ingest_data")
        from app.ingestion.pipeline import IngestionPipeline

        pipeline = IngestionPipeline()
        result = await pipeline.ingest_synthetic_data(data)
        logger.info("ingestion_complete", **result)

        logger.info("seed_complete")

    finally:
        await close_neo4j_client()
        await close_redis_client()
        await close_timescale_client()


async def cmd_bootstrap() -> None:
    """Bootstrap only: apply constraints, indexes, and load ontology."""
    from app.graph.bootstrap import bootstrap_graph
    from app.graph.client import close_neo4j_client, init_neo4j_client
    from app.ontology.loader import OntologyLoader

    settings = get_settings()
    neo4j_client = await init_neo4j_client(settings)

    try:
        counts = await bootstrap_graph(neo4j_client)
        logger.info("bootstrap_complete", **counts)

        loader = OntologyLoader(neo4j_client)
        ont_counts = await loader.load()
        logger.info("ontology_loaded", **ont_counts)
    finally:
        await close_neo4j_client()


async def cmd_replay() -> None:
    """Replay the golden scenario to trigger detection."""
    logger.info("replay_starting")
    # Will be implemented in Phase 3
    logger.info("replay_not_yet_implemented")


def main() -> None:
    """CLI dispatcher."""
    setup_logging()

    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <command>")
        print("Commands: seed, bootstrap, replay")
        sys.exit(1)

    command = sys.argv[1]
    commands = {
        "seed": cmd_seed,
        "bootstrap": cmd_bootstrap,
        "replay": cmd_replay,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands)}")
        sys.exit(1)

    asyncio.run(commands[command]())


if __name__ == "__main__":
    main()
