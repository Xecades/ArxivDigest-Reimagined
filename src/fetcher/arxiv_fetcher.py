"""Fetcher for arXiv paper metadata."""

import urllib.request

from bs4 import BeautifulSoup
from loguru import logger


def fetch_arxiv_papers(
    categories: list[str] | None = None,
    field: str = "cs",
    max_results: int = 0,
) -> list[dict]:
    """
    Fetch new papers from arXiv.

    Args:
        categories: List of category names to filter (e.g., ["Computer Vision and Pattern Recognition"])
        field: arXiv field abbreviation (default: "cs" for Computer Science)
        max_results: Maximum number of papers to return (0 = no limit)

    Returns:
        List of paper dicts with keys: id, title, authors, categories, abstract, url
    """
    url = f"https://arxiv.org/list/{field}/new"
    logger.info(f"Fetching papers from {url}")

    try:
        with urllib.request.urlopen(url) as page:
            soup = BeautifulSoup(page, features="html.parser")
    except Exception as e:
        logger.error(f"Failed to fetch papers from arXiv: {e}")
        return []

    if not soup.body:
        logger.error("Could not find body in arXiv page")
        return []

    content = soup.body.find("div", {"id": "content"})
    if not content:
        logger.error("Could not find content div in arXiv page")
        return []

    # Extract date
    h3 = content.find("h3")
    if h3:
        date_str = h3.text.replace("New submissions for", "").strip()
        logger.info(f"Papers date: {date_str}")

    # Find all paper entries
    dt_list = content.dl.find_all("dt") if content.dl else []
    dd_list = content.dl.find_all("dd") if content.dl else []

    if len(dt_list) != len(dd_list):
        logger.error("Mismatch between dt and dd elements")
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

            # Check max_results limit
            if max_results > 0 and len(papers) >= max_results:
                break

        except Exception as e:
            logger.warning(f"Error parsing paper: {e}")
            continue

    logger.info(f"Fetched {len(papers)} papers from arXiv")
    return papers
