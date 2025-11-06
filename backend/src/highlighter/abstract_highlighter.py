"""Abstract highlighter using LLM to highlight key points with markdown bold."""

from loguru import logger
from pydantic import BaseModel, Field

from src.cache import CacheManager
from src.llm.async_client import AsyncLLMClient
from src.llm.cost_calculator import CostInfo, UsageInfo


class HighlightResult(BaseModel):
    """Result from abstract highlighting."""

    highlighted_text: str = Field(
        description="The abstract with key points highlighted using **markdown bold**, "
        "and LaTeX math expressions fixed to use proper markdown-it-katex compatible delimiters "
        "($...$ for inline math, $$...$$ for display math)."
    )


class AbstractHighlighter:
    """
    Highlights key points in paper abstracts using LLM.

    Uses markdown bold (**text**) to emphasize important technical terms,
    methods, results, and contributions.
    """

    def __init__(
        self,
        llm_client: AsyncLLMClient,
        cache_manager: CacheManager,
        temperature: float = 0.0,
        config_hash: str | None = None,
    ):
        """
        Initialize the abstract highlighter.

        Args:
            llm_client: Async LLM client for API calls
            cache_manager: Cache manager for storing results
            temperature: LLM temperature for sampling (0-1)
            config_hash: Configuration hash for cache invalidation
        """
        self.llm_client = llm_client
        self.cache_manager = cache_manager
        self.temperature = temperature
        self.config_hash = config_hash
        logger.debug(
            f"AbstractHighlighter initialized: temperature={temperature}, config_hash={config_hash}"
        )

    async def highlight(
        self, abstract: str, user_context: str = ""
    ) -> tuple[str, list[dict[str, str]], UsageInfo | None, CostInfo | None]:
        """
        Highlight key points in an abstract.

        Args:
            abstract: The paper abstract to highlight
            user_context: Optional user prompt context to guide what to highlight

        Returns:
            Tuple of (highlighted_abstract, messages, usage, cost_info)
        """
        if not abstract or not abstract.strip():
            return abstract, [], None, None

        logger.debug(f"Highlighting abstract ({len(abstract)} chars)")

        # Build context-aware system prompt
        system_prompt = self._build_system_prompt(user_context)

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Please highlight the key points in this abstract:\n\n{abstract}",
            },
        ]

        # Call LLM with structured output
        try:
            result, usage, cost_info = await self.llm_client.complete(
                messages=messages,
                response_model=HighlightResult,
                temperature=self.temperature,
            )

            if result and hasattr(result, "highlighted_text"):
                highlighted: str = result.highlighted_text
                logger.debug(f"Highlighted abstract: {len(highlighted)} chars")

                # Add assistant response to messages
                conversation = messages + [
                    {
                        "role": "assistant",
                        "content": result.model_dump_json(indent=2),
                    }
                ]

                return highlighted, conversation, usage, cost_info
            else:
                logger.warning("Invalid highlight result, returning original abstract")
                return abstract, [], None, None

        except Exception as e:
            logger.error(f"Error highlighting abstract: {e}")
            return abstract, [], None, None

    def _build_system_prompt(self, user_context: str) -> str:
        """
        Build system prompt for highlighting.

        Args:
            user_context: User's research interest context

        Returns:
            System prompt string
        """
        base_prompt = """You are a scientific paper analyzer. Your task is to:
1. Highlight the most important parts of a paper abstract using **markdown bold**
2. Fix LaTeX math expressions to ensure proper rendering in markdown

Highlight guidelines:
- Do NOT change the original text content, only add ** around key phrases
- Focus on: novel methods, key techniques, main results, and significant contributions

LaTeX fixing guidelines:
- Use $ or $$ for math delimiters
- Preserve all mathematical content exactly
- If no LaTeX is present, simply return the highlighted text
"""

        # if user_context:
        #     base_prompt += f"\n\nUser's research interest and requirements: {user_context}\nPrioritize highlighting content relevant to this interest."

        return base_prompt

    async def highlight_batch(
        self,
        abstracts: list[tuple[str, str]],
        user_context: str = "",
    ) -> tuple[dict[str, str], dict[str, dict]]:
        """
        Highlight multiple abstracts in parallel with caching.

        Args:
            abstracts: List of (paper_id, abstract) tuples
            user_context: Optional user prompt context

        Returns:
            Tuple of:
                - highlighted_abstracts_map: {paper_id: highlighted_abstract}
                - highlight_info_map: {paper_id: {messages, usage, estimated_cost, estimated_cost_currency}}
        """
        import asyncio

        logger.info(f"Highlighting {len(abstracts)} abstracts...")

        # Separate cached and uncached abstracts
        cached_results: dict[str, str] = {}
        cached_info: dict[str, dict] = {}
        uncached_abstracts: list[tuple[str, str]] = []

        for paper_id, abstract in abstracts:
            cached = self.cache_manager.get("highlight", paper_id, self.config_hash)
            if cached is not None:
                cached_results[paper_id] = cached["highlighted_text"]
                cached_info[paper_id] = {
                    "messages": cached.get("messages", []),
                    "usage": cached.get("usage"),
                    "estimated_cost": cached.get("estimated_cost"),
                    "estimated_cost_currency": cached.get("estimated_cost_currency"),
                }
            else:
                uncached_abstracts.append((paper_id, abstract))

        logger.info(
            f"Highlight: {len(cached_results)} cached, {len(uncached_abstracts)} need processing"
        )

        # Process uncached abstracts
        highlighted_abstracts_map = dict(cached_results)
        highlight_info_map = dict(cached_info)

        if uncached_abstracts:
            tasks = [
                self._highlight_with_id(paper_id, abstract, user_context)
                for paper_id, abstract in uncached_abstracts
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    paper_id, original_abstract = uncached_abstracts[i]
                    logger.error(f"Error highlighting abstract {paper_id}: {result}")
                    # Use original abstract on error
                    highlighted_abstracts_map[paper_id] = original_abstract
                    highlight_info_map[paper_id] = {
                        "messages": [],
                        "usage": None,
                        "estimated_cost": None,
                        "estimated_cost_currency": None,
                    }
                else:
                    paper_id, highlighted, messages, usage, cost_info = result  # type: ignore[misc]
                    highlighted_abstracts_map[paper_id] = highlighted
                    highlight_info_map[paper_id] = {
                        "messages": messages,
                        "usage": usage,
                        "estimated_cost": cost_info.get("estimated_cost") if cost_info else None,
                        "estimated_cost_currency": cost_info.get("currency") if cost_info else None,
                    }

                    # Cache the result
                    cache_data = {
                        "highlighted_text": highlighted,
                        "messages": messages,
                        "usage": usage,
                        "estimated_cost": cost_info.get("estimated_cost") if cost_info else None,
                        "estimated_cost_currency": cost_info.get("currency") if cost_info else None,
                    }
                    self.cache_manager.set("highlight", paper_id, cache_data, self.config_hash)

        logger.info(f"Successfully highlighted {len(highlighted_abstracts_map)} abstracts")
        return highlighted_abstracts_map, highlight_info_map

    async def _highlight_with_id(
        self,
        paper_id: str,
        abstract: str,
        user_context: str,
    ) -> tuple[str, str, list[dict[str, str]], UsageInfo | None, CostInfo | None]:
        """
        Highlight abstract and return with ID.

        Args:
            paper_id: Paper identifier
            abstract: Abstract text
            user_context: User context

        Returns:
            Tuple of (paper_id, highlighted_abstract, messages, usage, cost_info)
        """
        highlighted, messages, usage, cost_info = await self.highlight(abstract, user_context)
        return (paper_id, highlighted, messages, usage, cost_info)
