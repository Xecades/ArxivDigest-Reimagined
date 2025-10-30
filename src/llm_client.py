"""LLM client using instructor for structured outputs."""

import os

import instructor
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, Field

from src.utils import is_debug_mode


class PaperRelevancy(BaseModel):
    """Relevancy assessment for a single paper."""

    relevancy_score: int = Field(
        ge=1,
        le=10,
        description="Relevancy score from 1-10, where higher indicates greater relevance",
    )
    reasons_for_match: str = Field(
        description="1-2 sentence explanation of why this paper is relevant to the research interests"
    )


class PapersRelevancyBatch(BaseModel):
    """Batch of paper relevancy assessments."""

    papers: list[PaperRelevancy] = Field(
        description="List of relevancy assessments, one per paper in the same order as input"
    )


def get_llm_client(
    model: str = "deepseek-chat", base_url: str | None = None
) -> instructor.Instructor:
    """
    Create an instructor-patched OpenAI client for structured outputs.

    Args:
        model: Model name (default: deepseek-chat)
        base_url: Optional base URL for API

    Returns:
        Instructor-patched client
    """
    # Determine API key and base URL
    if "deepseek" in model.lower():
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        if base_url is None:
            base_url = "https://api.deepseek.com"
    else:
        api_key = os.getenv("OPENAI_API_KEY")

    # Create OpenAI client
    if base_url:
        openai_client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        openai_client = OpenAI(api_key=api_key)

    # Patch with instructor
    return instructor.from_openai(openai_client, mode=instructor.Mode.JSON)


def assess_papers_relevancy(
    papers: list[dict],
    standard: str,
    model: str = "deepseek-chat",
    temperature: float = 0.4,
    max_retries: int = 3,
) -> tuple[list[dict], bool]:
    """
    Assess relevancy of papers using structured outputs via instructor.

    Args:
        papers: List of paper dicts with 'title', 'authors', 'abstract'
        standard: Criteria for filtering papers
        model: Model name to use (e.g., "deepseek-chat", "gpt-4", "gpt-4-turbo")
        temperature: Sampling temperature
        max_retries: Number of retries on failure

    Returns:
        Tuple of (papers_with_scores, hallucination_detected)
    """
    # Get instructor client
    client = get_llm_client(model=model)

    # Build prompt
    prompt = _build_prompt(papers, standard)

    # Debug output
    if is_debug_mode():
        logger.debug(f"Model: {model}")
        logger.debug(f"Temperature: {temperature}")
        logger.debug(f"Max Retries: {max_retries}")
        logger.debug(f"Number of papers: {len(papers)}")
        logger.debug("System Message: You are a helpful research assistant.")
        logger.debug(f"User Prompt:\n{prompt}")

    try:
        # Make API call with structured output using instructor
        response = client.chat.completions.create(
            model=model,
            response_model=PapersRelevancyBatch,
            messages=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_retries=max_retries,
        )

        # Debug output for response
        if is_debug_mode():
            logger.debug(f"Number of responses: {len(response.papers)}")
            for i, paper_resp in enumerate(response.papers, 1):
                logger.debug(f"{i}. Score: {paper_resp.relevancy_score}/10")
                logger.debug(f"   Reason: {paper_resp.reasons_for_match}")

        # Check for hallucination (wrong number of papers)
        hallucination = len(response.papers) != len(papers)

        if hallucination:
            logger.warning(
                f"Hallucination detected! Expected {len(papers)} papers, got {len(response.papers)}"
            )

        # Merge scores back into paper dicts
        result_papers = []
        for i, paper in enumerate(papers):
            if i < len(response.papers):
                paper_copy = paper.copy()
                paper_copy["Relevancy score"] = response.papers[i].relevancy_score
                paper_copy["Reasons for match"] = response.papers[i].reasons_for_match
                result_papers.append(paper_copy)

        return result_papers, hallucination

    except Exception as e:
        logger.error(f"Error in LLM call: {e}")
        raise


def _build_prompt(papers: list[dict], standard: str) -> str:
    """Build the prompt for paper relevancy assessment."""
    prompt = f"""You are asked to read a list of arxiv papers, each with title, authors and abstract.
Based on specific filtering criteria, provide a relevancy score out of 10 for each paper, with a higher score indicating greater relevance. A relevance score more than 7 will need person's attention for details.
Additionally, generate 1-2 sentence summary for each paper explaining why it's relevant to the filtering criteria.

Please keep the paper order the same as in the input list.

Filtering criteria:
{standard}

"""

    for idx, paper in enumerate(papers, 1):
        prompt += f"""###
{idx}. Title: {paper["title"]}
{idx}. Authors: {paper["authors"]}
{idx}. Abstract: {paper["abstract"]}
"""

    return prompt
