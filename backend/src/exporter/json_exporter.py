"""JSON exporter for digest data."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger


class JSONExporter:
    """
    Exports pipeline results to JSON format.

    Generates a comprehensive JSON file containing metadata, configuration,
    statistics, and detailed paper information from all filtering stages.
    """

    def __init__(self):
        """Initialize the JSON exporter."""
        logger.debug("JSONExporter initialized")

    def export(
        self,
        pipeline_results: dict,
        highlight_info: dict[str, dict],
        config: dict,
        output_path: str = "frontend/public/digest.json",
        title: str = "ArXiv Digest - Reimagined",
    ) -> None:
        """
        Export pipeline results to JSON file.

        Args:
            pipeline_results: Dictionary with all stage results from FilterPipeline
            highlight_info: Dictionary with highlight conversation info for each paper
            config: Full configuration dictionary
            output_path: Output file path (relative to project root)
            title: Digest title
        """
        # Extract all stage results
        stage1_results = pipeline_results["stage1_results"]
        stage2_results = pipeline_results["stage2_results"]
        stage3_results = pipeline_results["stage3_results"]

        # Count papers at each stage
        stage1_total = len(stage1_results)
        stage1_passed = len([r for _, r in stage1_results if r["pass_filter"]])
        stage2_passed = len([r for _, r in stage2_results if r["pass_filter"]])
        stage3_passed = len([r for _, r in stage3_results if r and r["pass_filter"]])

        logger.info(
            f"Exporting JSON: {stage1_total} total, "
            f"{stage1_passed} stage1, {stage2_passed} stage2, {stage3_passed} stage3"
        )

        # Prepare metadata
        metadata = self._prepare_metadata(
            config=config,
            title=title,
            stage1_total=stage1_total,
            stage1_passed=stage1_passed,
            stage2_passed=stage2_passed,
            stage3_passed=stage3_passed,
        )

        # Prepare papers data
        papers_data = self._prepare_papers_data(pipeline_results, highlight_info)

        # Combine into final structure
        output_data = {
            "metadata": metadata,
            "papers": papers_data,
        }

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.success(f"JSON digest exported to: {output_path}")

    def _prepare_metadata(
        self,
        config: dict,
        title: str,
        stage1_total: int,
        stage1_passed: int,
        stage2_passed: int,
        stage3_passed: int,
    ) -> dict[str, Any]:
        """Prepare metadata section."""
        arxiv_config = config.get("arxiv", {})
        llm_config = config.get("llm", {})
        stage1_config = config.get("stage1", {})
        stage2_config = config.get("stage2", {})
        stage3_config = config.get("stage3", {})
        highlight_config = config.get("highlight", {})

        categories = arxiv_config.get("categories", [])
        if categories is None:
            categories = []

        return {
            "title": title,
            "timestamp": datetime.now(UTC).isoformat(),
            "user_prompt": config.get("user_prompt", ""),
            "arxiv_config": {
                "categories": categories,
                "max_results": arxiv_config.get("max_results", 0),
            },
            "llm_config": {
                "model": llm_config.get("model", "unknown"),
            },
            "stage_config": {
                "stage1": {
                    "threshold": stage1_config.get("threshold", 0.5),
                    "temperature": stage1_config.get("temperature", 0.0),
                },
                "stage2": {
                    "threshold": stage2_config.get("threshold", 0.7),
                    "temperature": stage2_config.get("temperature", 0.1),
                },
                "stage3": {
                    "threshold": stage3_config.get("threshold", 0.8),
                    "temperature": stage3_config.get("temperature", 0.3),
                },
                "highlight": {
                    "temperature": highlight_config.get("temperature", 0.0),
                },
            },
            "custom_fields": stage3_config.get("custom_fields", {}),
            "stats": {
                "total_papers": stage1_total,
                "stage1_passed": stage1_passed,
                "stage2_passed": stage2_passed,
                "stage3_passed": stage3_passed,
            },
        }

    def _prepare_papers_data(
        self, pipeline_results: dict, highlight_info: dict[str, dict]
    ) -> list[dict]:
        """
        Prepare papers data for JSON export.

        Args:
            pipeline_results: Pipeline results dictionary
            highlight_info: Highlight conversation info for each paper

        Returns:
            List of paper data dictionaries
        """
        papers_map: dict[str, dict] = {}

        # Stage 1 results (all papers)
        for paper, result in pipeline_results["stage1_results"]:
            paper_id = paper["id"]
            papers_map[paper_id] = {
                "arxiv_id": paper_id,
                "title": paper["title"],
                "authors": paper["authors"],
                "categories": paper["categories"],
                "abstract": paper.get("abstract", ""),
                "pdf_url": paper.get("pdf_url", ""),
                "abs_url": paper.get("abs_url", ""),
                "published": paper.get("published", ""),
                "stage1": self._format_stage_result(result),
                "stage2": None,
                "stage3": None,
                "highlight": None,  # Will be added for stage3 papers
                "max_stage": 1 if result["pass_filter"] else 0,
            }

        # Stage 2 results
        for paper, result in pipeline_results["stage2_results"]:
            paper_id = paper["id"]
            if paper_id in papers_map:
                papers_map[paper_id]["stage2"] = self._format_stage_result(result)
                if result["pass_filter"]:
                    papers_map[paper_id]["max_stage"] = 2

        # Stage 3 results
        for paper, result in pipeline_results["stage3_results"]:
            if result is None:
                continue
            paper_id = paper["id"]
            if paper_id in papers_map:
                papers_map[paper_id]["stage3"] = self._format_stage_result(result, is_stage3=True)
                if result["pass_filter"]:
                    papers_map[paper_id]["max_stage"] = 3
                    # Add highlight info if available
                    if paper_id in highlight_info:
                        papers_map[paper_id]["highlight"] = highlight_info[paper_id]

        # Convert to list and sort by max_stage (descending) and score
        papers_list = list(papers_map.values())
        papers_list.sort(
            key=lambda p: (
                p["max_stage"],
                p["stage3"]["score"]
                if p["stage3"]
                else p["stage2"]["score"]
                if p["stage2"]
                else p["stage1"]["score"],
            ),
            reverse=True,
        )

        return papers_list

    def _format_stage_result(self, result: dict, is_stage3: bool = False) -> dict:
        """
        Format a stage result for JSON export.

        Args:
            result: Stage result dictionary
            is_stage3: Whether this is a stage 3 result

        Returns:
            Formatted result dictionary
        """
        formatted = {
            "pass": result["pass_filter"],
            "score": result["score"],
            "reasoning": result.get("reasoning", ""),
            "messages": result.get("messages", []),
            "usage": result.get("usage"),
            "estimated_cost": result.get("estimated_cost"),
            "estimated_cost_currency": result.get("estimated_cost_currency"),
        }

        # Add stage3-specific fields
        if is_stage3:
            formatted["novelty_score"] = result.get("novelty_score", 0.0)
            formatted["impact_score"] = result.get("impact_score", 0.0)
            formatted["quality_score"] = result.get("quality_score", 0.0)
            formatted["custom_fields"] = result.get("custom_fields", {})

        return formatted
