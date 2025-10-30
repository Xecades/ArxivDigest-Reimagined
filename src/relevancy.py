"""Paper relevancy scoring and filtering."""

import time

from loguru import logger

from src import llm_client


def process_subject_fields(subjects: str) -> list[str]:
    """
    Parse the subjects field from arXiv papers.

    Example input: "Computation and Language (cs.CL); Artificial Intelligence (cs.AI)"
    Example output: ["Computation and Language", "Artificial Intelligence"]
    """
    # Remove any prefix
    subjects = subjects.replace("Subjects:\n", "").replace("Subjects:", "")

    # Split by semicolon
    all_subjects = subjects.split(";")

    # Extract subject name before the parentheses and strip whitespace
    return [s.split("(")[0].strip() for s in all_subjects]


def generate_relevance_score(
    papers: list[dict],
    standard: str,
    model_name: str = "deepseek-chat",
    threshold_score: int = 7,
    num_papers_per_batch: int = 16,
    temperature: float = 0.4,
) -> tuple[list[dict], bool]:
    """
    Generate relevance scores for papers using LLM.

    Args:
        papers: List of paper dictionaries
        standard: Filtering criteria description
        model_name: Model to use (default: deepseek-chat)
        threshold_score: Minimum score to include in results (1-10)
        num_papers_per_batch: Number of papers to process per API call
        temperature: Sampling temperature

    Returns:
        Tuple of (filtered_papers, hallucination_detected)
    """
    filtered_papers = []
    hallucination_detected = False

    total_batches = (len(papers) + num_papers_per_batch - 1) // num_papers_per_batch
    logger.info(f"Processing {len(papers)} papers in {total_batches} batches")

    for batch_idx in range(0, len(papers), num_papers_per_batch):
        batch_papers = papers[batch_idx : batch_idx + num_papers_per_batch]
        batch_num = batch_idx // num_papers_per_batch + 1

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_papers)} papers)")

        start_time = time.time()

        try:
            scored_papers, hallu = llm_client.assess_papers_relevancy(
                papers=batch_papers,
                standard=standard,
                model=model_name,
                temperature=temperature,
            )

            hallucination_detected = hallucination_detected or hallu

            # Filter by threshold
            for paper in scored_papers:
                if paper.get("Relevancy score", 0) >= threshold_score:
                    filtered_papers.append(paper)

            duration = time.time() - start_time
            logger.info(
                f"Batch {batch_num} completed in {duration:.2f}s, "
                f"found {len([p for p in scored_papers if p.get('Relevancy score', 0) >= threshold_score])} relevant papers"
            )

        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {e}")
            continue

    # Sort by relevancy score (highest first)
    filtered_papers.sort(key=lambda x: x.get("Relevancy score", 0), reverse=True)

    logger.info(
        f"Filtering complete: {len(filtered_papers)}/{len(papers)} papers above threshold {threshold_score}"
    )

    return filtered_papers, hallucination_detected
