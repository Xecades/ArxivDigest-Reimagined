"""Stage 3 filter: Deep analysis based on full paper content."""

from loguru import logger

from src.cache import CacheManager
from src.fetcher import ArxivHTMLCrawler
from src.llm import AsyncLLMClient, Stage3Result, prepare_result_with_conversation
from src.parser import ArxivHtmlCleaner


class Stage3Filter:
    """
    Stage 3 filter: Deep analysis with full paper content.

    Filters papers based on complete paper text extracted from HTML.
    Provides multi-dimensional scoring and custom field extraction.
    Uses a high threshold for final selection.
    """

    def __init__(
        self,
        llm_client: AsyncLLMClient,
        cache_manager: CacheManager,
        html_crawler: ArxivHTMLCrawler,
        threshold: float = 0.8,
        max_text_chars: int = 8000,
        custom_fields: list[dict[str, str]] | None = None,
        config_hash: str | None = None,
    ):
        """
        Initialize Stage 3 filter.

        Args:
            llm_client: Async LLM client for evaluation
            cache_manager: Cache manager for storing results
            html_crawler: HTML crawler for fetching papers
            threshold: Score threshold for passing (0-1)
            max_text_chars: Maximum characters to extract from paper
            custom_fields: List of custom field dicts with 'name' and 'description'
            config_hash: Configuration hash for cache invalidation
        """
        self.llm_client = llm_client
        self.cache_manager = cache_manager
        self.html_crawler = html_crawler
        self.threshold = threshold
        self.max_text_chars = max_text_chars
        self.custom_fields = custom_fields or []
        self.config_hash = config_hash

        # HTML cleaner for text extraction
        self.html_cleaner = ArxivHtmlCleaner(max_chars=max_text_chars)

        # Extract field names for logging
        field_names = [f.get("name", "") for f in self.custom_fields if f.get("name")]

        logger.info(
            f"Stage3Filter initialized: threshold={threshold}, "
            f"max_chars={max_text_chars}, custom_fields={field_names}"
        )

    async def filter_batch(
        self,
        papers: list[dict],
        user_prompt: str,
    ) -> list[tuple[dict, dict | None]]:
        """
        Filter multiple papers in parallel.

        Args:
            papers: List of paper dicts with keys: id, title, authors, categories, abstract
            user_prompt: User's filtering criteria

        Returns:
            List of (paper, result_dict) tuples (result_dict can be None if HTML fetch failed)
        """
        logger.info(f"Stage 3 filtering {len(papers)} papers...")

        # Separate cached and uncached papers
        cached_results: list[tuple[dict, dict | None]] = []
        uncached_papers = []

        for paper in papers:
            paper_id = paper["id"]
            cached = self.cache_manager.get(3, paper_id, self.config_hash)

            if cached is not None:
                cached_results.append((paper, cached))
            else:
                uncached_papers.append(paper)

        logger.info(
            f"Stage 3: {len(cached_results)} cached, {len(uncached_papers)} need evaluation"
        )

        # Process uncached papers
        if uncached_papers:
            # Fetch HTML for all papers
            paper_ids = [paper["id"] for paper in uncached_papers]
            html_results = await self.html_crawler.fetch_batch(paper_ids)

            # Extract text from HTML
            papers_with_text = []
            for paper in uncached_papers:
                html = html_results.get(paper["id"])
                if html:
                    full_text = self.html_cleaner.clean(html)
                    papers_with_text.append((paper, full_text))
                else:
                    # Add to results with None
                    cached_results.append((paper, None))

            logger.info(
                f"Stage 3: Successfully extracted text from {len(papers_with_text)}/{len(uncached_papers)} papers"
            )

            # Evaluate papers with text
            if papers_with_text:
                # Build message batches
                batch_messages = [
                    self.llm_client.build_stage3_messages(
                        title=paper["title"],
                        authors=paper["authors"],
                        categories=paper["categories"],
                        full_text=full_text,
                        user_prompt=user_prompt,
                        custom_fields=self.custom_fields,
                    )
                    for paper, full_text in papers_with_text
                ]

                # Call LLM in parallel
                results = await self.llm_client.complete_batch(batch_messages, Stage3Result)

                # Convert to dicts with pass_filter, messages and cache results
                evaluated_results = []
                for (paper, _), messages, (result, usage, cost_info) in zip(
                    papers_with_text, batch_messages, results, strict=True
                ):
                    result_dict = prepare_result_with_conversation(
                        result, self.threshold, messages, usage, cost_info
                    )
                    self.cache_manager.set(3, paper["id"], result_dict, self.config_hash)
                    evaluated_results.append((paper, result_dict))

                # Combine all results
                all_results = cached_results + evaluated_results
            else:
                all_results = cached_results
        else:
            all_results = cached_results

        # Log statistics
        passed = sum(1 for _, result in all_results if result and result["pass_filter"])
        total = sum(1 for _, r in all_results if r is not None)
        if total > 0:
            logger.info(
                f"Stage 3 complete: {passed}/{total} papers passed ({passed / total * 100:.1f}%)"
            )
        else:
            logger.warning("Stage 3 complete: No papers could be evaluated")

        return all_results
