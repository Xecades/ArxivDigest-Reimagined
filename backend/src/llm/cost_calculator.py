"""Cost calculation utilities for LLM usage."""

from typing import TypedDict


class UsageInfo(TypedDict, total=False):
    """Token usage information."""

    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


class CostInfo(TypedDict, total=False):
    """Cost information."""

    estimated_cost: float
    currency: str


def calculate_deepseek_cost(usage: UsageInfo | None) -> CostInfo | None:
    """
    Calculate estimated cost for DeepSeek API usage.

    Pricing (CNY):
    - Input (cache miss): 2 CNY per million tokens
    - Output: 3 CNY per million tokens

    Args:
        usage: Usage information with token counts

    Returns:
        Cost information with estimated cost in CNY, or None if usage is None
    """
    if not usage:
        return None

    prompt_tokens = usage.get("prompt_tokens") or 0
    completion_tokens = usage.get("completion_tokens") or 0

    # DeepSeek pricing in CNY per million tokens
    prompt_cost = (prompt_tokens / 1_000_000) * 2.0  # 2 CNY per million input tokens
    completion_cost = (completion_tokens / 1_000_000) * 3.0  # 3 CNY per million output tokens
    total_cost = prompt_cost + completion_cost

    return {
        "estimated_cost": total_cost,
        "currency": "CNY",
    }


def extract_usage_from_response(response: object) -> UsageInfo | None:
    """
    Extract usage information from LLM response.

    Attempts to extract usage from instructor-wrapped OpenAI response.
    Returns None if usage information is not available.

    Args:
        response: Response object from instructor/OpenAI

    Returns:
        Usage information dict or None
    """
    # Try to get raw response from instructor wrapper
    raw = getattr(response, "_raw_response", None)
    if not raw:
        return None

    usage = None
    try:
        # raw may be a dict-like or have a usage attribute
        if isinstance(raw, dict):
            usage = raw.get("usage")
        else:
            usage = getattr(raw, "usage", None)
    except Exception:
        return None

    if not usage:
        return None

    # Normalize to UsageInfo dict
    try:
        # Handle both dict and object (Pydantic model) types
        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            total_tokens = usage.get("total_tokens")
        else:
            # Pydantic object or similar
            prompt_tokens = getattr(usage, "prompt_tokens", None)
            completion_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)

        return {
            "prompt_tokens": int(prompt_tokens) if prompt_tokens is not None else None,
            "completion_tokens": int(completion_tokens) if completion_tokens is not None else None,
            "total_tokens": int(total_tokens) if total_tokens is not None else None,
        }
    except (ValueError, TypeError, AttributeError):
        return None
