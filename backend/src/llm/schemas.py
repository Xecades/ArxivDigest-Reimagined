"""Pydantic schemas for LLM responses."""

from pydantic import BaseModel, Field

from .cost_calculator import CostInfo, UsageInfo


class FilterResult(BaseModel):
    """Base result for paper filtering (LLM output only)."""

    score: float = Field(ge=0.0, le=1.0, description="Overall relevance score (0-1)")
    reasoning: str | None = Field(None, description="Optional reasoning for the decision")


class Stage1Result(FilterResult):
    """Result from Stage 1 filtering (Title + Categories)."""

    # Stage 1 is simple: just score + reasoning
    pass


class Stage2Result(FilterResult):
    """Result from Stage 2 filtering (Title + Authors + Categories + Abstract)."""

    # Stage 2 adds abstract-level reasoning
    pass


class Stage3Result(FilterResult):
    """Result from Stage 3 filtering (Full paper content with custom fields)."""

    # Stage 3 has flexible custom fields defined by user
    custom_fields: dict[str, str] = Field(
        default_factory=dict,
        description="User-defined custom output fields",
    )

    # Common multi-dimensional scores
    novelty_score: float = Field(ge=0.0, le=1.0, description="Novelty of the work")
    impact_score: float = Field(ge=0.0, le=1.0, description="Potential impact")
    quality_score: float = Field(ge=0.0, le=1.0, description="Technical quality")


# Helper function to add pass_filter
def add_pass_filter(result: FilterResult, threshold: float) -> dict:
    """
    Add pass_filter to result based on score and threshold.

    Args:
        result: FilterResult from LLM
        threshold: Score threshold

    Returns:
        Dict with pass_filter added
    """
    result_dict = result.model_dump()
    result_dict["pass_filter"] = result.score >= threshold
    return result_dict


def prepare_result_with_conversation(
    result: FilterResult,
    threshold: float,
    messages: list[dict[str, str]],
    usage: UsageInfo | None = None,
    cost_info: CostInfo | None = None,
) -> dict:
    """
    Prepare result dict with pass_filter and conversation history.

    Args:
        result: FilterResult from LLM
        threshold: Score threshold
        messages: Original request messages (system + user)
        usage: Token usage information
        cost_info: Cost information with estimated cost and currency

    Returns:
        Dict with pass_filter and full conversation (including assistant response)
    """
    result_dict = add_pass_filter(result, threshold)

    # Add usage and cost information if available
    if usage is not None:
        result_dict["usage"] = usage
    if cost_info is not None:
        result_dict["estimated_cost"] = cost_info.get("estimated_cost")
        result_dict["estimated_cost_currency"] = cost_info.get("currency")

    # Add conversation history with assistant response
    conversation = messages + [
        {
            "role": "assistant",
            "content": result.model_dump_json(indent=2),
        }
    ]
    result_dict["messages"] = conversation

    return result_dict
