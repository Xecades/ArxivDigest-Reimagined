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
from src.highlighter import AbstractHighlighter
from src.llm.async_client import AsyncLLMClient


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_file) as f:
        config: dict[str, Any] = yaml.safe_load(f)

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
    highlight_config = config.get("highlight", {})

    # Get API key from environment variable
    api_key = os.getenv("API_KEY", "")
    if not api_key:
        logger.error(
            "API_KEY environment variable not found. Please set API_KEY in your environment."
        )
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
        "highlight": highlight_config,
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
        stage1_temperature=stage1_config.get("temperature", 0.0),
        stage2_threshold=stage2_config.get("threshold", 0.7),
        stage2_temperature=stage2_config.get("temperature", 0.1),
        stage3_threshold=stage3_config.get("threshold", 0.8),
        stage3_temperature=stage3_config.get("temperature", 0.3),
        stage3_max_chars=stage3_config.get("max_text_chars", 8000),
        custom_fields=stage3_config.get("custom_fields", []),
        config_hash=config_hash,
    )

    # Fetch papers from arXiv
    logger.info("Fetching papers from arXiv...")
    papers = fetch_arxiv_papers(
        categories=arxiv_config.get("categories", []),
        field=arxiv_config.get("field", "cs"),
        max_results=arxiv_config.get("max_results", 0),
    )

    if not papers:
        logger.error("No papers fetched from arXiv")
        sys.exit(1)

    logger.info(f"Fetched {len(papers)} papers from arXiv")

    # Run filtering pipeline
    results = await pipeline.run(papers, user_prompt)

    # Highlight abstracts for papers that passed stage3
    logger.info("Highlighting abstracts for Stage 3 papers...")
    highlighter = AbstractHighlighter(
        llm_client=llm_client,
        cache_manager=cache_manager,
        temperature=highlight_config.get("temperature", 0.0),
        config_hash=config_hash,
    )

    # Collect stage3 passed papers with their abstracts
    stage3_papers_map = {
        paper["id"]: paper
        for paper, result in results["stage3_results"]
        if result and result["pass_filter"]
    }

    highlight_info_map: dict[str, dict] = {}
    if stage3_papers_map:
        abstracts_to_highlight = [
            (paper_id, paper["abstract"]) for paper_id, paper in stage3_papers_map.items()
        ]

        # Highlight in batch and get both highlighted abstracts and conversation info
        highlighted_abstracts_map, highlight_info_map = await highlighter.highlight_batch(
            abstracts_to_highlight,
            user_context=user_prompt,
        )

        # Update papers with highlighted abstracts
        for paper_id, highlighted in highlighted_abstracts_map.items():
            if paper_id in stage3_papers_map:
                stage3_papers_map[paper_id]["abstract"] = highlighted

        logger.info(f"Highlighted {len(highlighted_abstracts_map)} abstracts")
    else:
        logger.info("No Stage 3 papers to highlight")

    # Generate JSON output
    logger.info("Generating JSON output...")
    from src.exporter import JSONExporter

    exporter = JSONExporter()
    output_path = Path("../frontend/public/digest.json")
    exporter.export(
        pipeline_results=results,
        highlight_info=highlight_info_map,
        config=config,
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
