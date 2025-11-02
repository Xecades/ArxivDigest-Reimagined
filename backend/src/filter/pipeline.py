"""Pipeline for orchestrating three-stage progressive filtering."""

from loguru import logger

from src.cache import CacheManager
from src.fetcher import ArxivHTMLCrawler
from src.llm import AsyncLLMClient

from .stage1_filter import Stage1Filter
from .stage2_filter import Stage2Filter
from .stage3_filter import Stage3Filter


class FilterPipeline:
    """
    Three-stage progressive filtering pipeline.

    Stage 1: Quick screening (Title + Categories)
    Stage 2: Refined screening (+ Authors + Abstract)
    Stage 3: Deep analysis (+ Full paper content)
    """

    def __init__(
        self,
        llm_client: AsyncLLMClient,
        cache_manager: CacheManager,
        html_crawler: ArxivHTMLCrawler,
        stage1_threshold: float = 0.5,
        stage1_temperature: float = 0.0,
        stage2_threshold: float = 0.7,
        stage2_temperature: float = 0.1,
        stage3_threshold: float = 0.8,
        stage3_temperature: float = 0.3,
        stage3_max_chars: int = 8000,
        custom_fields: list[dict[str, str]] | None = None,
        config_hash: str | None = None,
    ):
        """
        Initialize the filtering pipeline.

        Args:
            llm_client: Async LLM client
            cache_manager: Cache manager
            html_crawler: HTML crawler
            stage1_threshold: Threshold for Stage 1 (0-1)
            stage1_temperature: Temperature for Stage 1 (0-1)
            stage2_threshold: Threshold for Stage 2 (0-1)
            stage2_temperature: Temperature for Stage 2 (0-1)
            stage3_threshold: Threshold for Stage 3 (0-1)
            stage3_temperature: Temperature for Stage 3 (0-1)
            stage3_max_chars: Max characters for Stage 3 text extraction
            custom_fields: List of custom field dicts with 'name' and 'description'
            config_hash: Configuration hash for cache invalidation
        """
        self.llm_client = llm_client
        self.cache_manager = cache_manager
        self.html_crawler = html_crawler
        self.config_hash = config_hash

        # Initialize stage filters
        self.stage1 = Stage1Filter(
            llm_client=llm_client,
            cache_manager=cache_manager,
            threshold=stage1_threshold,
            temperature=stage1_temperature,
            config_hash=config_hash,
        )

        self.stage2 = Stage2Filter(
            llm_client=llm_client,
            cache_manager=cache_manager,
            threshold=stage2_threshold,
            temperature=stage2_temperature,
            config_hash=config_hash,
        )

        self.stage3 = Stage3Filter(
            llm_client=llm_client,
            cache_manager=cache_manager,
            html_crawler=html_crawler,
            threshold=stage3_threshold,
            temperature=stage3_temperature,
            max_text_chars=stage3_max_chars,
            custom_fields=custom_fields,
            config_hash=config_hash,
        )

        logger.info(
            f"FilterPipeline initialized: "
            f"stage1_threshold={stage1_threshold}, stage1_temperature={stage1_temperature}, "
            f"stage2_threshold={stage2_threshold}, stage2_temperature={stage2_temperature}, "
            f"stage3_threshold={stage3_threshold}, stage3_temperature={stage3_temperature}"
        )

    async def run(
        self,
        papers: list[dict],
        user_prompt: str,
    ) -> dict[str, list]:
        """
        Run the three-stage filtering pipeline.

        Args:
            papers: List of paper dicts with metadata
            user_prompt: User's filtering criteria

        Returns:
            Dictionary with results for each stage:
            {
                "stage1_results": [(paper, result), ...],
                "stage1_passed": [paper, ...],
                "stage2_results": [(paper, result), ...],
                "stage2_passed": [paper, ...],
                "stage3_results": [(paper, result), ...],
                "stage3_passed": [paper, ...],
            }
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Starting 3-stage filtering pipeline for {len(papers)} papers")
        logger.info(f"{'=' * 60}\n")

        # Stage 1: Quick screening
        logger.info("🔍 STAGE 1: Quick Screening (Title + Categories)")
        logger.info("-" * 60)
        stage1_results = await self.stage1.filter_batch(papers, user_prompt)
        stage1_passed = [paper for paper, result in stage1_results if result["pass_filter"]]

        logger.info(f"\n✅ Stage 1 passed: {len(stage1_passed)}/{len(papers)} papers\n")

        # Stage 2: Refined screening (only for papers that passed Stage 1)
        stage2_results = []
        stage2_passed = []

        if stage1_passed:
            logger.info("🔍 STAGE 2: Refined Screening (+ Authors + Abstract)")
            logger.info("-" * 60)
            stage2_results = await self.stage2.filter_batch(stage1_passed, user_prompt)
            stage2_passed = [paper for paper, result in stage2_results if result["pass_filter"]]

            logger.info(f"\n✅ Stage 2 passed: {len(stage2_passed)}/{len(stage1_passed)} papers\n")
        else:
            logger.warning("⚠️  No papers passed Stage 1, skipping Stage 2\n")

        # Stage 3: Deep analysis (only for papers that passed Stage 2)
        stage3_results = []
        stage3_passed = []

        if stage2_passed:
            logger.info("🔍 STAGE 3: Deep Analysis (+ Full Paper Content)")
            logger.info("-" * 60)
            stage3_results = await self.stage3.filter_batch(stage2_passed, user_prompt)
            stage3_passed = [
                paper for paper, result in stage3_results if result and result["pass_filter"]
            ]

            logger.info(f"\n✅ Stage 3 passed: {len(stage3_passed)}/{len(stage2_passed)} papers\n")
        else:
            logger.warning("⚠️  No papers passed Stage 2, skipping Stage 3\n")

        # Summary
        logger.info(f"{'=' * 60}")
        logger.info("📊 PIPELINE SUMMARY")
        logger.info(f"{'=' * 60}")
        logger.info(f"Total input papers:     {len(papers)}")
        logger.info(
            f"Stage 1 passed:         {len(stage1_passed)} ({len(stage1_passed) / len(papers) * 100:.1f}%)"
        )
        if stage1_passed:
            logger.info(
                f"Stage 2 passed:         {len(stage2_passed)} ({len(stage2_passed) / len(stage1_passed) * 100:.1f}%)"
            )
        if stage2_passed:
            logger.info(
                f"Stage 3 passed:         {len(stage3_passed)} ({len(stage3_passed) / len(stage2_passed) * 100:.1f}%)"
            )
        logger.info(
            f"Final papers selected:  {len(stage3_passed)} ({len(stage3_passed) / len(papers) * 100:.1f}%)"
        )
        logger.info(f"{'=' * 60}\n")

        return {
            "stage1_results": stage1_results,
            "stage1_passed": stage1_passed,
            "stage2_results": stage2_results,
            "stage2_passed": stage2_passed,
            "stage3_results": stage3_results,
            "stage3_passed": stage3_passed,
        }
