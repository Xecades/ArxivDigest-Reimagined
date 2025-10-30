"""Main entry point for ArXiv Digest generation."""

import argparse
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from loguru import logger

from src.arxiv import get_papers
from src.relevancy import generate_relevance_score, process_subject_fields
from src.utils import is_debug_mode

logger.remove()
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>"
    ),
    level="DEBUG" if is_debug_mode() else "INFO",
)


def generate_digest(
    categories: list[str],
    standard: str,
    threshold: int,
    model: str,
) -> tuple[str, bool]:
    """
    Generate HTML digest of relevant papers.

    Args:
        categories: List of CS categories to filter by
        standard: Filtering criteria description
        threshold: Relevancy score threshold (1-10)
        model: Model name to use

    Returns:
        Tuple of (HTML content, hallucination_detected)
    """
    # Always use CS topic
    logger.info("Fetching papers from Computer Science (cs)")

    papers = get_papers("cs")
    # if is_debug_mode():
    #     papers = papers[:16]

    logger.info(f"Downloaded {len(papers)} papers")

    # Filter by categories if specified
    if categories:
        logger.info(f"Filtering by categories: {categories}")
        papers = [
            paper
            for paper in papers
            if bool(set(process_subject_fields(paper["subjects"])) & set(categories))
        ]
        logger.info(f"After category filtering: {len(papers)} papers")

    # Generate relevance scores if standard specified
    if standard:
        logger.info("Generating relevance scores...")
        relevant_papers, hallucination = generate_relevance_score(
            papers=papers,
            standard=standard,
            model_name=model,
            threshold_score=threshold,
            num_papers_per_batch=16,
            temperature=0.4,
        )

        # Generate HTML
        html_parts = []
        if relevant_papers:
            for paper in relevant_papers:
                html_parts.append(
                    f'<div class="paper">'
                    f'<div class="title"><a href="{paper["main_page"]}" target="_blank">{paper["title"]}</a></div>'
                    f'<div class="authors"><strong>Authors:</strong> {paper["authors"]}</div>'
                    f'<div class="score"><strong>Relevancy Score:</strong> {paper["Relevancy score"]}/10</div>'
                    f'<div class="reason"><strong>Reason:</strong> {paper["Reasons for match"]}</div>'
                    f"</div>"
                )
            html_body = "\n".join(html_parts)
        else:
            html_body = f'<div class="no-papers">No papers found matching your criteria (threshold >= {threshold})</div>'

        if hallucination:
            warning = '<div class="warning">⚠️ Warning: The model hallucinated some papers. Scores may not be accurate.</div>'
            logger.warning("The model hallucinated some papers. Scores may not be accurate.")
            html_body = f"{warning}\n{html_body}"

        return html_body, hallucination
    else:
        # No filtering, just list papers
        logger.info("No standard specified, listing all papers")
        html_parts = []
        for paper in papers:
            html_parts.append(
                f'<div class="paper">'
                f'<div class="title"><a href="{paper["main_page"]}" target="_blank">{paper["title"]}</a></div>'
                f'<div class="authors"><strong>Authors:</strong> {paper["authors"]}</div>'
                f"</div>"
            )
        return "\n".join(html_parts), False


def main() -> None:
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Generate personalized arXiv digest")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract config values
    categories = config.get("categories", [])
    standard = config.get("standard", "")
    threshold = config.get("threshold", 7)
    model = config.get("model", "deepseek-chat")

    logger.info("=== ArXiv Digest Generation Started ===")
    logger.info(f"Categories: {categories if categories else 'All'}")
    logger.info(f"Model: {model}")
    logger.info(f"Threshold: {threshold}")

    # Generate digest
    html_body, _ = generate_digest(
        categories=categories,
        standard=standard,
        threshold=threshold,
        model=model,
    )

    # Save to file
    output_path = Path("digest.html")

    # Create complete HTML document with styling
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ArXiv Digest</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .meta {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .meta p {{
            margin: 5px 0;
        }}
        .paper {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .title a {{
            color: #007bff;
            text-decoration: none;
        }}
        .title a:hover {{
            text-decoration: underline;
        }}
        .authors {{
            color: #666;
            margin-bottom: 8px;
        }}
        .score {{
            color: #28a745;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .reason {{
            color: #555;
            font-style: italic;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .no-papers {{
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            font-size: 1.1em;
        }}
    </style>
</head>
<body>
    <h1>ArXiv Digest</h1>
    <div class="meta">
        <p><strong>Categories:</strong> {categories}</p>
        <p><strong>Model:</strong> {model}</p>
        <p><strong>Threshold:</strong> {threshold}/10</p>
        <p><strong>Generated:</strong> {timestamp}</p>
    </div>
    {content}
</body>
</html>"""

    import datetime

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    categories_str = ", ".join(categories) if categories else "All CS"

    full_html = html_template.format(
        categories=categories_str,
        model=model,
        threshold=threshold,
        timestamp=timestamp,
        content=html_body,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    logger.success(f"Digest saved to {output_path}")
    logger.info("=== ArXiv Digest Generation Complete ===")


if __name__ == "__main__":
    main()
