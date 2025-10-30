"""Async crawler for fetching arXiv paper HTML."""

import asyncio
from typing import Any

import aiohttp
from loguru import logger


class ArxivHTMLCrawler:
    """
    Async crawler for fetching arXiv paper HTML content.

    Supports batch fetching with rate limiting and error handling.
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the HTML crawler.

        Args:
            max_concurrent: Maximum number of concurrent requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Semaphore for limiting concurrent requests
        self.semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(
            f"ArxivHTMLCrawler initialized: max_concurrent={max_concurrent}, "
            f"timeout={timeout}s, max_retries={max_retries}"
        )

    def build_html_url(self, arxiv_id: str) -> str:
        """
        Build arXiv HTML URL from paper ID.

        Args:
            arxiv_id: arXiv paper ID (e.g., "2503.10630v3" or "2503.10630")

        Returns:
            Full URL to HTML version
        """
        # arXiv HTML format: https://arxiv.org/html/YYMM.NNNNNvV
        return f"https://arxiv.org/html/{arxiv_id}"

    async def fetch_html(
        self,
        arxiv_id: str,
        session: aiohttp.ClientSession | None = None,
    ) -> str | None:
        """
        Fetch HTML content for a single paper.

        Args:
            arxiv_id: arXiv paper ID
            session: Optional aiohttp session (creates one if not provided)

        Returns:
            HTML content as string, or None if fetch failed
        """
        url = self.build_html_url(arxiv_id)

        async with self.semaphore:
            for attempt in range(self.max_retries):
                try:
                    # Create session if not provided
                    if session is None:
                        async with aiohttp.ClientSession() as temp_session:
                            return await self._fetch_with_session(temp_session, arxiv_id, url)
                    else:
                        return await self._fetch_with_session(session, arxiv_id, url)

                except TimeoutError:
                    logger.warning(
                        f"Timeout fetching {arxiv_id} (attempt {attempt + 1}/{self.max_retries})"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)

                except aiohttp.ClientError as e:
                    logger.warning(
                        f"Client error fetching {arxiv_id}: {e} "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)

                except Exception as e:
                    logger.error(f"Unexpected error fetching {arxiv_id}: {e}")
                    break

            logger.error(f"Failed to fetch {arxiv_id} after {self.max_retries} attempts")
            return None

    async def _fetch_with_session(
        self,
        session: aiohttp.ClientSession,
        arxiv_id: str,
        url: str,
    ) -> str | None:
        """Internal method to fetch with a given session."""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with session.get(url, timeout=timeout) as response:
            if response.status == 200:
                html = await response.text()
                logger.debug(f"Fetched {arxiv_id}: {len(html)} characters")
                return html
            elif response.status == 404:
                logger.warning(f"Paper {arxiv_id} not found (404) - may not have HTML version")
                return None
            else:
                logger.warning(f"HTTP {response.status} for {arxiv_id}")
                return None

    async def fetch_batch(
        self,
        arxiv_ids: list[str],
    ) -> dict[str, str | None]:
        """
        Fetch HTML content for multiple papers in parallel.

        Args:
            arxiv_ids: List of arXiv paper IDs

        Returns:
            Dictionary mapping arxiv_id to HTML content (or None if failed)
        """
        logger.info(f"Fetching HTML for {len(arxiv_ids)} papers...")

        # Create a single session for all requests
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_html(arxiv_id, session) for arxiv_id in arxiv_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dictionary
        result_dict: dict[str, str | None] = {}
        success_count = 0

        for arxiv_id, result in zip(arxiv_ids, results, strict=True):
            if isinstance(result, Exception):
                logger.error(f"Exception fetching {arxiv_id}: {result}")
                result_dict[arxiv_id] = None
            elif isinstance(result, str):
                result_dict[arxiv_id] = result
                success_count += 1
            else:
                result_dict[arxiv_id] = None

        logger.info(
            f"Fetched {success_count}/{len(arxiv_ids)} papers successfully "
            f"({success_count / len(arxiv_ids) * 100:.1f}%)"
        )

        return result_dict

    async def close(self) -> None:
        """Close any open resources."""
        logger.debug("ArxivHTMLCrawler closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
