"""Async LLM client with instructor integration."""

import asyncio
from typing import Any, TypeVar

import instructor
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

from .schemas import Stage1Result, Stage2Result, Stage3Result

T = TypeVar("T", bound=BaseModel)


class AsyncLLMClient:
    """
    Async LLM client with structured output using instructor.

    Supports parallel async calls for batch processing and flexible
    response schemas for different filtering stages.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_retries: int = 3,
        timeout: float = 60.0,
        max_concurrent: int = 10,
    ):
        """
        Initialize the async LLM client.

        Args:
            api_key: OpenAI API key
            base_url: Optional base URL for API (for custom endpoints)
            model: Model name to use
            temperature: Sampling temperature (0.0 for deterministic)
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
            max_concurrent: Maximum number of concurrent requests
        """
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.timeout = timeout

        # Create async OpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Wrap with instructor for structured output
        self.instructor_client = instructor.from_openai(self.client)

        # Semaphore for limiting concurrent requests
        self.semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(
            f"AsyncLLMClient initialized: model={model}, "
            f"max_concurrent={max_concurrent}, timeout={timeout}s"
        )

    async def complete(
        self,
        messages: list[dict[str, str]],
        response_model: type[T],
        **kwargs: Any,
    ) -> T:
        """
        Get structured completion from LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            response_model: Pydantic model for response structure
            **kwargs: Additional arguments to pass to instructor

        Returns:
            Structured response matching response_model
        """
        async with self.semaphore:
            try:
                # Log the conversation for debugging (without truncation)
                logger.debug(f"=== LLM Request ({response_model.__name__}) ===")
                for msg in messages:
                    role = msg["role"]
                    content = msg["content"]
                    logger.debug(f"[{role.upper()}] {content}")

                response = await self.instructor_client.chat.completions.create(  # type: ignore
                    model=self.model,
                    messages=messages,  # type: ignore
                    response_model=response_model,
                    temperature=self.temperature,
                    **kwargs,
                )

                # Log the response
                logger.debug(f"=== LLM Response ({response_model.__name__}) ===")
                logger.debug(f"{response}")
                logger.debug("=" * 60)

                return response  # type: ignore

            except Exception as e:
                logger.error(f"LLM completion failed: {e}")
                raise

    async def complete_batch(
        self,
        batch_messages: list[list[dict[str, str]]],
        response_model: type[T],
        **kwargs: Any,
    ) -> list[T]:
        """
        Get structured completions for multiple requests in parallel.

        Args:
            batch_messages: List of message lists (one per request)
            response_model: Pydantic model for response structure
            **kwargs: Additional arguments to pass to instructor

        Returns:
            List of structured responses
        """
        tasks = [self.complete(messages, response_model, **kwargs) for messages in batch_messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results: list[T] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch request {i} failed: {result}")
            else:
                valid_results.append(result)  # type: ignore[arg-type]

        return valid_results

    def build_stage1_messages(
        self,
        title: str,
        categories: list[str],
        user_prompt: str,
    ) -> list[dict[str, str]]:
        """
        Build messages for Stage 1 filtering (Title + Categories).

        Args:
            title: Paper title
            categories: arXiv categories
            user_prompt: User's filtering criteria

        Returns:
            List of message dicts
        """
        system_message = """You are an expert at quickly screening academic papers for relevance.
Your task is to determine if a paper is potentially relevant based ONLY on its title and categories.
This is a fast preliminary filter - be generous in passing papers that might be relevant.
Respond with a boolean pass_filter and a score (0-1)."""

        user_message = f"""User's interests: {user_prompt}

Paper Information:
- Title: {title}
- Categories: {', '.join(categories)}

Is this paper potentially relevant? Provide a quick assessment."""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    def build_stage2_messages(
        self,
        title: str,
        authors: list[str],
        categories: list[str],
        abstract: str,
        user_prompt: str,
    ) -> list[dict[str, str]]:
        """
        Build messages for Stage 2 filtering (Title + Authors + Categories + Abstract).

        Args:
            title: Paper title
            authors: List of author names
            categories: arXiv categories
            abstract: Paper abstract
            user_prompt: User's filtering criteria

        Returns:
            List of message dicts
        """
        system_message = """You are an expert at evaluating academic paper relevance.
Your task is to determine if a paper is relevant based on its metadata and abstract.
Provide a detailed assessment with a pass/fail decision, relevance score, and category."""

        user_message = f"""User's interests: {user_prompt}

Paper Information:
- Title: {title}
- Authors: {', '.join(authors)}
- Categories: {', '.join(categories)}
- Abstract: {abstract}

Evaluate this paper's relevance to the user's interests."""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    def build_stage3_messages(
        self,
        title: str,
        authors: list[str],
        categories: list[str],
        abstract: str,
        full_text: str,
        user_prompt: str,
        custom_fields: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """
        Build messages for Stage 3 filtering (Full paper analysis).

        Args:
            title: Paper title
            authors: List of author names
            categories: arXiv categories
            abstract: Paper abstract
            full_text: Full paper text (cleaned from HTML)
            user_prompt: User's filtering criteria
            custom_fields: List of custom field names to extract

        Returns:
            List of message dicts
        """
        system_message = """You are an expert at deeply analyzing academic papers.
Your task is to thoroughly evaluate the paper's relevance, novelty, impact, and quality.
Provide multi-dimensional scores and extract specific information as requested."""

        custom_fields_prompt = ""
        if custom_fields:
            custom_fields_prompt = f"\n\nExtract the following custom fields: {', '.join(custom_fields)}"

        user_message = f"""User's interests: {user_prompt}

Paper Information:
- Title: {title}
- Authors: {', '.join(authors)}
- Categories: {', '.join(categories)}
- Abstract: {abstract}

Full Paper Content (first 8000 chars):
{full_text[:8000]}

Provide a comprehensive analysis including:
1. Overall relevance score
2. Novelty score (how original is the work?)
3. Impact score (potential significance?)
4. Quality score (technical soundness?)
5. Detailed reasoning for your assessment{custom_fields_prompt}"""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    async def filter_stage1(
        self,
        title: str,
        categories: list[str],
        user_prompt: str,
    ) -> Stage1Result:
        """
        Execute Stage 1 filtering.

        Args:
            title: Paper title
            categories: arXiv categories
            user_prompt: User's filtering criteria

        Returns:
            Stage1Result with pass/fail and score
        """
        messages = self.build_stage1_messages(title, categories, user_prompt)
        return await self.complete(messages, Stage1Result)

    async def filter_stage2(
        self,
        title: str,
        authors: list[str],
        categories: list[str],
        abstract: str,
        user_prompt: str,
    ) -> Stage2Result:
        """
        Execute Stage 2 filtering.

        Args:
            title: Paper title
            authors: List of author names
            categories: arXiv categories
            abstract: Paper abstract
            user_prompt: User's filtering criteria

        Returns:
            Stage2Result with detailed assessment
        """
        messages = self.build_stage2_messages(title, authors, categories, abstract, user_prompt)
        return await self.complete(messages, Stage2Result)

    async def filter_stage3(
        self,
        title: str,
        authors: list[str],
        categories: list[str],
        abstract: str,
        full_text: str,
        user_prompt: str,
        custom_fields: list[str] | None = None,
    ) -> Stage3Result:
        """
        Execute Stage 3 filtering.

        Args:
            title: Paper title
            authors: List of author names
            categories: arXiv categories
            abstract: Paper abstract
            full_text: Full paper text
            user_prompt: User's filtering criteria
            custom_fields: List of custom field names

        Returns:
            Stage3Result with comprehensive analysis
        """
        messages = self.build_stage3_messages(
            title, authors, categories, abstract, full_text, user_prompt, custom_fields
        )
        return await self.complete(messages, Stage3Result)

    async def close(self) -> None:
        """Close the client connection."""
        await self.client.close()
        logger.debug("AsyncLLMClient closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
