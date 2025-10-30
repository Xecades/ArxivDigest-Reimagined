"""Stage 1 filter: Quick screening based on title and categories."""

from loguru import logger

from src.cache import CacheManager
from src.llm import AsyncLLMClient, Stage1Result


class Stage1Filter:
    """
    Stage 1 filter: Quick preliminary screening.

    Filters papers based on title and categories only.
    Uses a low threshold to be inclusive and avoid false negatives.
    """

    def __init__(
        self,
        llm_client: AsyncLLMClient,
        cache_manager: CacheManager,
        threshold: float = 0.5,
        config_hash: str | None = None,
    ):
        """
        Initialize Stage 1 filter.

        Args:
            llm_client: Async LLM client for evaluation
            cache_manager: Cache manager for storing results
            threshold: Score threshold for passing (0-1)
            config_hash: Configuration hash for cache invalidation
        """
        self.llm_client = llm_client
        self.cache_manager = cache_manager
        self.threshold = threshold
        self.config_hash = config_hash

        logger.info(f"Stage1Filter initialized: threshold={threshold}")

    async def filter_paper(
        self,
        paper_id: str,
        title: str,
        categories: list[str],
        user_prompt: str,
    ) -> Stage1Result:
        """
        Filter a single paper through Stage 1.

        Args:
            paper_id: arXiv paper ID
            title: Paper title
            categories: arXiv categories
            user_prompt: User's filtering criteria

        Returns:
            Stage1Result with pass/fail and score
        """
        # Check cache first
        cached_result = self.cache_manager.get(1, paper_id, self.config_hash)
        if cached_result is not None:
            logger.debug(f"Stage 1 cache hit: {paper_id}")
            return Stage1Result(**cached_result)

        # Call LLM for evaluation
        logger.debug(f"Stage 1 evaluating: {paper_id}")
        result = await self.llm_client.filter_stage1(title, categories, user_prompt)

        # Apply threshold
        result.pass_filter = result.score >= self.threshold

        # Cache the result
        self.cache_manager.set(1, paper_id, result.model_dump(), self.config_hash)

        return result

    async def filter_batch(
        self,
        papers: list[dict],
        user_prompt: str,
    ) -> list[tuple[dict, Stage1Result]]:
        """
        Filter multiple papers in parallel.

        Args:
            papers: List of paper dicts with keys: id, title, categories
            user_prompt: User's filtering criteria

        Returns:
            List of (paper, result) tuples
        """
        logger.info(f"Stage 1 filtering {len(papers)} papers...")

        # Separate cached and uncached papers
        cached_results = []
        uncached_papers = []

        for paper in papers:
            paper_id = paper["id"]
            cached = self.cache_manager.get(1, paper_id, self.config_hash)

            if cached is not None:
                cached_results.append((paper, Stage1Result(**cached)))
            else:
                uncached_papers.append(paper)

        logger.info(
            f"Stage 1: {len(cached_results)} cached, {len(uncached_papers)} need evaluation"
        )

        # Evaluate uncached papers in parallel
        if uncached_papers:
            # Build message batches
            batch_messages = [
                self.llm_client.build_stage1_messages(
                    title=paper["title"],
                    categories=paper["categories"],
                    user_prompt=user_prompt,
                )
                for paper in uncached_papers
            ]

            # Call LLM in parallel
            results = await self.llm_client.complete_batch(batch_messages, Stage1Result)

            # Apply threshold and cache results
            evaluated_results = []
            for paper, result in zip(uncached_papers, results, strict=True):
                result.pass_filter = result.score >= self.threshold
                self.cache_manager.set(1, paper["id"], result.model_dump(), self.config_hash)
                evaluated_results.append((paper, result))

            # Combine cached and evaluated results
            all_results = cached_results + evaluated_results
        else:
            all_results = cached_results

        # Log statistics
        passed = sum(1 for _, result in all_results if result.pass_filter)
        logger.info(f"Stage 1 complete: {passed}/{len(papers)} papers passed ({passed/len(papers)*100:.1f}%)")

        return all_results
