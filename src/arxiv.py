# type: ignore

import datetime
import json
import urllib.request
from pathlib import Path

import pytz
from bs4 import BeautifulSoup as bs
from loguru import logger


def download_papers(field_abbr: str = "cs") -> list[dict]:
    """
    Download new papers from arXiv for the specified field.

    Args:
        field_abbr: Field abbreviation (default: "cs" for Computer Science)

    Returns:
        List of paper dictionaries with metadata
    """
    url = f"https://arxiv.org/list/{field_abbr}/new"
    logger.info(f"Fetching papers from {url}")

    page = urllib.request.urlopen(url)
    soup = bs(page, features="html.parser")
    content = soup.body.find("div", {"id": "content"})

    # Extract date from header
    h3 = content.find("h3").text
    date_str = h3.replace("New submissions for", "").strip()
    logger.info(f"Papers date: {date_str}")

    # Find all paper entries
    dt_list = content.dl.find_all("dt")
    dd_list = content.dl.find_all("dd")

    assert len(dt_list) == len(dd_list), "Mismatch between dt and dd elements"

    arxiv_base = "https://arxiv.org/abs/"
    papers = []

    for dt, dd in zip(dt_list, dd_list, strict=True):
        # Extract paper number from the href attribute
        paper_link = dt.find("a", {"title": "Abstract"})
        if paper_link and "href" in paper_link.attrs:
            paper_number = paper_link["href"].split("/")[-1]
        else:
            logger.warning(f"Could not extract paper number from dt: {dt}")
            continue

        # Extract metadata
        paper = {
            "main_page": arxiv_base + paper_number,
            "pdf": arxiv_base.replace("abs", "pdf") + paper_number,
            "title": dd.find("div", {"class": "list-title mathjax"})
            .text.replace("Title:", "")
            .strip(),
            "authors": dd.find("div", {"class": "list-authors"})
            .text.replace("Authors:", "")
            .replace("\n", " ")
            .strip(),
            "subjects": dd.find("div", {"class": "list-subjects"})
            .text.replace("Subjects:", "")
            .strip(),
            "abstract": dd.find("p", {"class": "mathjax"}).text.replace("\n", " ").strip(),
        }

        papers.append(paper)

    logger.info(f"Downloaded {len(papers)} papers")

    # Save to cache
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    date = datetime.date.fromtimestamp(
        datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp()
    )
    date_str = date.strftime("%a, %d %b %y")
    cache_file = data_dir / f"{field_abbr}_{date_str}.jsonl"

    with open(cache_file, "w") as f:
        for paper in papers:
            f.write(json.dumps(paper) + "\n")

    logger.info(f"Cached papers to {cache_file}")

    return papers


def get_papers(field_abbr: str = "cs") -> list[dict]:
    """
    Get papers from cache or download if not available.

    Args:
        field_abbr: Field abbreviation (default: "cs" for Computer Science)

    Returns:
        List of paper dictionaries
    """
    date = datetime.date.fromtimestamp(
        datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp()
    )
    date_str = date.strftime("%a, %d %b %y")
    cache_file = Path(f"data/{field_abbr}_{date_str}.jsonl")

    # Download if cache doesn't exist
    if not cache_file.exists():
        logger.info(f"Cache not found for {date_str}, downloading...")
        return download_papers(field_abbr)

    # Load from cache
    logger.info(f"Loading papers from cache: {cache_file}")
    papers = []
    with open(cache_file) as f:
        for line in f:
            papers.append(json.loads(line))

    logger.info(f"Loaded {len(papers)} papers from cache")
    return papers
