"""Stage 2 filter: Refined screening based on metadata and abstract."""

from loguru import logger

from src.cache import CacheManager
from src.llm import AsyncLLMClient, Stage2Result


class Stage2Filter:
    """
    Stage 2 filter: Refined screening with abstract.

    Filters papers based on title, authors, categories, and abstract.
    Uses a medium threshold for more selective filtering.
    """

    def __init__(
        self,
        llm_client: AsyncLLMClient,
        cache_manager: CacheManager,
        threshold: float = 0.7,
        config_hash: str | None = None,
    ):
        """
        Initialize Stage 2 filter.

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

        logger.info(f"Stage2Filter initialized: threshold={threshold}")

    async def filter_paper(
        self,
        paper_id: str,
        title: str,
        authors: list[str],
        categories: list[str],
        abstract: str,
        user_prompt: str,
    ) -> Stage2Result:
        """
        Filter a single paper through Stage 2.

        Args:
            paper_id: arXiv paper ID
            title: Paper title
            authors: List of author names
            categories: arXiv categories
            abstract: Paper abstract
            user_prompt: User's filtering criteria

        Returns:
            Stage2Result with detailed assessment
        """
        # Check cache first
        cached_result = self.cache_manager.get(2, paper_id, self.config_hash)
        if cached_result is not None:
            logger.debug(f"Stage 2 cache hit: {paper_id}")
            return Stage2Result(**cached_result)

        # Call LLM for evaluation
        logger.debug(f"Stage 2 evaluating: {paper_id}")
        result = await self.llm_client.filter_stage2(
            title, authors, categories, abstract, user_prompt
        )

        # Apply threshold
        result.pass_filter = result.score >= self.threshold

        # Cache the result
        self.cache_manager.set(2, paper_id, result.model_dump(), self.config_hash)

        return result

    async def filter_batch(
        self,
        papers: list[dict],
        user_prompt: str,
    ) -> list[tuple[dict, Stage2Result]]:
        """
        Filter multiple papers in parallel.

        Args:
            papers: List of paper dicts with keys: id, title, authors, categories, abstract
            user_prompt: User's filtering criteria

        Returns:
            List of (paper, result) tuples
        """
        logger.info(f"Stage 2 filtering {len(papers)} papers...")

        # Separate cached and uncached papers
        cached_results = []
        uncached_papers = []

        for paper in papers:
            paper_id = paper["id"]
            cached = self.cache_manager.get(2, paper_id, self.config_hash)

            if cached is not None:
                cached_results.append((paper, Stage2Result(**cached)))
            else:
                uncached_papers.append(paper)

        logger.info(
            f"Stage 2: {len(cached_results)} cached, {len(uncached_papers)} need evaluation"
        )

        # Evaluate uncached papers in parallel
        if uncached_papers:
            # Build message batches
            batch_messages = [
                self.llm_client.build_stage2_messages(
                    title=paper["title"],
                    authors=paper["authors"],
                    categories=paper["categories"],
                    abstract=paper["abstract"],
                    user_prompt=user_prompt,
                )
                for paper in uncached_papers
            ]

            # Call LLM in parallel
            results = await self.llm_client.complete_batch(batch_messages, Stage2Result)

            # Apply threshold and cache results
            evaluated_results = []
            for paper, result in zip(uncached_papers, results, strict=True):
                result.pass_filter = result.score >= self.threshold
                self.cache_manager.set(2, paper["id"], result.model_dump(), self.config_hash)
                evaluated_results.append((paper, result))

            # Combine cached and evaluated results
            all_results = cached_results + evaluated_results
        else:
            all_results = cached_results

        # Log statistics
        passed = sum(1 for _, result in all_results if result.pass_filter)
        logger.info(f"Stage 2 complete: {passed}/{len(papers)} papers passed ({passed/len(papers)*100:.1f}%)")

        return all_results
