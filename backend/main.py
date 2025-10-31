"""ArxivDigest-Reimagined main entry point."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from loguru import logger

from src.cache import CacheManager
from src.fetcher import ArxivHTMLCrawler, fetch_arxiv_papers
from src.filter.pipeline import FilterPipeline
from src.llm.async_client import AsyncLLMClient


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_file) as f:
        config: dict[str, Any] = yaml.safe_load(f)

    # Replace environment variables
    if "llm" in config and "api_key" in config["llm"]:
        api_key = config["llm"]["api_key"]
        if isinstance(api_key, str) and api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            config["llm"]["api_key"] = os.getenv(env_var, "")

    return config




async def async_main(config: dict) -> None:
    """Async main function."""
    # Extract configuration
    arxiv_config = config.get("arxiv", {})
    llm_config = config.get("llm", {})
    cache_config = config.get("cache", {})
    crawler_config = config.get("crawler", {})

    user_prompt = config.get("user_prompt", "")
    stage1_config = config.get("stage1", {})
    stage2_config = config.get("stage2", {})
    stage3_config = config.get("stage3", {})

    # Validate API key
    api_key = llm_config.get("api_key", "")
    if not api_key:
        logger.error("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        sys.exit(1)

    # Initialize components
    logger.info("Initializing components...")

    # Cache manager
    cache_manager = CacheManager(
        cache_dir=cache_config.get("dir", ".cache"),
        size_limit=cache_config.get("size_limit_mb", 1024) * 1024 * 1024,
        expire_days=cache_config.get("expire_days", 30),
    )

    # LLM client
    llm_client = AsyncLLMClient(
        api_key=api_key,
        base_url=llm_config.get("base_url"),
        model=llm_config.get("model", "gpt-4o-mini"),
        temperature=llm_config.get("temperature", 0.0),
        max_concurrent=llm_config.get("max_concurrent", 10),
        timeout=llm_config.get("timeout", 60),
    )

    # HTML crawler
    html_crawler = ArxivHTMLCrawler(
        max_concurrent=crawler_config.get("max_concurrent", 5),
        timeout=crawler_config.get("timeout", 30),
        max_retries=crawler_config.get("max_retries", 3),
        retry_delay=crawler_config.get("retry_delay", 1.0),
    )

    # Generate config hash for cache invalidation
    import hashlib
    import json

    config_for_hash = {
        "user_prompt": user_prompt,
        "stage1": stage1_config,
        "stage2": stage2_config,
        "stage3": stage3_config,
        "model": llm_config.get("model"),
    }
    config_hash = hashlib.sha256(json.dumps(config_for_hash, sort_keys=True).encode()).hexdigest()[
        :8
    ]

    # Filter pipeline
    pipeline = FilterPipeline(
        llm_client=llm_client,
        cache_manager=cache_manager,
        html_crawler=html_crawler,
        stage1_threshold=stage1_config.get("threshold", 0.5),
        stage2_threshold=stage2_config.get("threshold", 0.7),
        stage3_threshold=stage3_config.get("threshold", 0.8),
        stage3_max_chars=stage3_config.get("max_text_chars", 8000),
        custom_fields=stage3_config.get("custom_fields", []),
        config_hash=config_hash,
    )

    # Fetch papers from arXiv
    logger.info("Fetching papers from arXiv...")
    papers = fetch_arxiv_papers(
        categories=arxiv_config.get("categories", []),
        max_results=arxiv_config.get("max_results", 0),
    )

    if not papers:
        logger.error("No papers fetched from arXiv")
        sys.exit(1)

    logger.info(f"Fetched {len(papers)} papers from arXiv")

    # Run filtering pipeline
    results = await pipeline.run(papers, user_prompt)

    # Store stats for HTML generation
    config["stage1_passed"] = len(results["stage1_passed"])
    config["stage2_passed"] = len(results["stage2_passed"])
    config["stage3_passed"] = len(results["stage3_passed"])

    # Generate interactive HTML output
    logger.info("Generating HTML output...")
    from src.renderer import HTMLRenderer

    renderer = HTMLRenderer()
    output_path = Path(config["output"].get("file", "digest.html"))
    renderer.render(
        pipeline_results=results,
        output_path=str(output_path),
        title="ArXiv Digest - Reimagined",
    )

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 FINAL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total papers fetched:   {len(papers)}")
    logger.info(f"Stage 1 passed:         {len(results['stage1_passed'])}")
    logger.info(f"Stage 2 passed:         {len(results['stage2_passed'])}")
    logger.info(f"Stage 3 passed:         {len(results['stage3_passed'])}")
    logger.info(f"Output file:            {output_path}")
    logger.info("=" * 60)

    # Cleanup
    await llm_client.close()
    cache_manager.close()


def main() -> None:
    """Main entry point."""
    # Configure logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG",  # Changed to DEBUG to see LLM conversation details
    )

    # Load environment variables
    load_dotenv()

    # Parse arguments
    import argparse

    parser = argparse.ArgumentParser(description="Generate ArXiv digest with three-stage filtering")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    logger.info("=" * 60)
    logger.info("🚀 ArXiv Digest - Three-Stage Filtering Pipeline")
    logger.info("=" * 60)

    # Run async main
    try:
        asyncio.run(async_main(config))
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Error: {e}")
        sys.exit(1)

    logger.success("\n✅ ArXiv Digest generation completed successfully!")


if __name__ == "__main__":
    main()
