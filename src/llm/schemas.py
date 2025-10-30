"""Pydantic schemas for LLM responses."""

from typing import Any

from pydantic import BaseModel, Field


class FilterResult(BaseModel):
    """Base result for paper filtering."""

    pass_filter: bool = Field(description="Whether the paper passes this stage")
    score: float = Field(ge=0.0, le=1.0, description="Overall relevance score (0-1)")
    reasoning: str | None = Field(None, description="Optional reasoning for the decision")


class Stage1Result(FilterResult):
    """Result from Stage 1 filtering (Title + Categories)."""

    # Stage 1 is simple: just pass/fail + score
    pass


class Stage2Result(FilterResult):
    """Result from Stage 2 filtering (Title + Authors + Categories + Abstract)."""

    # Stage 2 adds more detail
    relevance_category: str | None = Field(
        None,
        description="Categorization of relevance (e.g., 'high', 'medium', 'low')",
    )


class Stage3Result(FilterResult):
    """Result from Stage 3 filtering (Full paper content with custom fields)."""

    # Stage 3 has flexible custom fields defined by user
    custom_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="User-defined custom output fields",
    )

    # Common multi-dimensional scores
    relevance_score: float | None = Field(None, ge=0.0, le=1.0, description="Relevance to user interests")
    novelty_score: float | None = Field(None, ge=0.0, le=1.0, description="Novelty of the work")
    impact_score: float | None = Field(None, ge=0.0, le=1.0, description="Potential impact")
    quality_score: float | None = Field(None, ge=0.0, le=1.0, description="Technical quality")
