"""Fetcher for arXiv paper metadata."""

import urllib.request

from bs4 import BeautifulSoup
from loguru import logger


def _fetch_from_single_field(
    field: str,
    categories: list[str] | None = None,
) -> list[dict]:
    """
    Fetch papers from a single arXiv field.

    Args:
        field: arXiv field abbreviation (e.g., "cs", "math", "physics")
        categories: List of category names to filter

    Returns:
        List of paper dicts with keys: id, title, authors, categories, abstract, url
    """
    url = f"https://arxiv.org/list/{field}/new"
    logger.info(f"Fetching papers from {url}")

    try:
        with urllib.request.urlopen(url) as page:
            soup = BeautifulSoup(page, features="html.parser")
    except Exception as e:
        logger.error(f"Failed to fetch papers from arXiv field '{field}': {e}")
        return []

    if not soup.body:
        logger.error(f"Could not find body in arXiv page for field '{field}'")
        return []

    content = soup.body.find("div", {"id": "content"})
    if not content:
        logger.error(f"Could not find content div in arXiv page for field '{field}'")
        return []

    # Extract date
    h3 = content.find("h3")
    if h3:
        date_str = h3.text.replace("New submissions for", "").strip()
        logger.debug(f"Papers date for field '{field}': {date_str}")

    # Find all paper entries
    dt_list = content.dl.find_all("dt") if content.dl else []
    dd_list = content.dl.find_all("dd") if content.dl else []

    if len(dt_list) != len(dd_list):
        logger.error(f"Mismatch between dt and dd elements for field '{field}'")
        return []

    papers = []

    for dt, dd in zip(dt_list, dd_list, strict=True):
        try:
            # Extract paper ID
            paper_link = dt.find("a", {"title": "Abstract"})
            if not paper_link or "href" not in paper_link.attrs:
                continue
            href = paper_link.get("href")
            if not isinstance(href, str):
                continue
            paper_id = href.split("/")[-1]

            # Extract title
            title_tag = dd.find("div", {"class": "list-title"})
            if not title_tag:
                continue
            title = title_tag.text.replace("Title:", "").strip()

            # Extract authors
            authors_tag = dd.find("div", {"class": "list-authors"})
            authors = []
            if authors_tag:
                author_links = authors_tag.find_all("a")
                authors = [a.text.strip() for a in author_links]

            # Extract categories/subjects
            subjects_tag = dd.find("div", {"class": "list-subjects"})
            paper_categories = []
            if subjects_tag:
                subjects_text = subjects_tag.text.replace("Subjects:", "").strip()
                paper_categories = [s.strip() for s in subjects_text.split(";")]

            # Extract abstract
            abstract_tag = dd.find("p", {"class": "mathjax"})
            abstract = abstract_tag.text.strip() if abstract_tag else ""

            # Filter by categories if specified
            if categories:
                # Check if any of the paper's categories match the filter
                category_match = any(
                    any(filter_cat.lower() in paper_cat.lower() for paper_cat in paper_categories)
                    for filter_cat in categories
                )
                if not category_match:
                    continue

            paper = {
                "id": paper_id,
                "title": title,
                "authors": authors,
                "categories": paper_categories,
                "abstract": abstract,
                "abs_url": f"https://arxiv.org/abs/{paper_id}",
                "pdf_url": f"https://arxiv.org/pdf/{paper_id}.pdf",
            }

            papers.append(paper)

        except Exception as e:
            logger.warning(f"Error parsing paper in field '{field}': {e}")
            continue

    logger.info(f"Fetched {len(papers)} papers from arXiv field '{field}'")
    return papers


def fetch_arxiv_papers(
    categories: list[str] | None = None,
    field: str | list[str] = "cs",
    max_results: int = 0,
) -> list[dict]:
    """
    Fetch new papers from arXiv.

    Args:
        categories: List of category names to filter (e.g., ["Computer Vision and Pattern Recognition"])
        field: arXiv field abbreviation(s). Can be a single string (e.g., "cs") or a list (e.g., ["cs", "math"])
        max_results: Maximum number of papers to return (0 = no limit)

    Returns:
        List of paper dicts with keys: id, title, authors, categories, abstract, url
    """
    # Normalize field to list
    fields = [field] if isinstance(field, str) else field

    logger.info(f"Fetching papers from fields: {fields}")

    # Fetch papers from all fields and deduplicate by paper ID
    papers_dict: dict[str, dict] = {}

    for single_field in fields:
        field_papers = _fetch_from_single_field(single_field, categories)

        for paper in field_papers:
            paper_id = paper["id"]
            # Only add if not already present (first field wins)
            if paper_id not in papers_dict:
                papers_dict[paper_id] = paper

            # Check max_results limit
            if max_results > 0 and len(papers_dict) >= max_results:
                break

        # Early exit if max_results reached
        if max_results > 0 and len(papers_dict) >= max_results:
            break

    papers = list(papers_dict.values())
    logger.info(f"Total unique papers fetched: {len(papers)}")

    return papers
