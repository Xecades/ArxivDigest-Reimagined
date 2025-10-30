"""Clean and extract text from arXiv HTML papers."""

import re

from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from loguru import logger


class ArxivHtmlCleaner:
    """Extract clean text from arXiv HTML format papers."""

    def __init__(self, max_chars: int | None = None):
        """
        Initialize the HTML cleaner.

        Args:
            max_chars: Maximum characters to extract (None = no limit)
        """
        self.max_chars = max_chars

        # Sections to keep (in order of importance)
        self.section_priority = [
            "abstract",
            "introduction",
            "method",
            "methodology",
            "approach",
            "conclusion",
            "related work",
            "experiments",
            "results",
        ]

        # Tags to remove completely
        self.tags_to_remove = [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "figure",
            "table",
        ]

        # Classes/IDs to remove (arXiv specific)
        self.classes_to_remove = [
            "ltx_bibliography",  # References
            "ltx_ref",  # Citations
            "ltx_cite",  # Citations
            # "ltx_equation",  # Equations - KEEP to extract LaTeX
            # "ltx_Math",  # Math - KEEP to extract LaTeX
            "ltx_tabular",  # Tables
            "ltx_figure",  # Figures
            "ltx_listing",  # Code listings
            "ltx_authors",  # Author list (already have from metadata)
            "ltx_dates",  # Dates
        ]

    def clean(self, html: str) -> str:
        """
        Extract clean text from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Cleaned text
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove unwanted tags
        for tag_name in self.tags_to_remove:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove unwanted classes
        for class_name in self.classes_to_remove:
            for tag in soup.find_all(class_=class_name):
                tag.decompose()

        # Try to extract main content (arXiv uses ltx_page_content)
        main_content = soup.find("div", class_="ltx_page_content")
        if main_content is None:
            main_content = soup.find("main") or soup.find("article") or soup

        # Extract sections in priority order
        sections = self._extract_sections(main_content)

        # Combine sections
        text_parts = []
        total_chars = 0

        for section_name, section_text in sections:
            if self.max_chars and total_chars >= self.max_chars:
                break

            # Add section header
            if section_name:
                text_parts.append(f"\n## {section_name.upper()}\n")

            # Add section content (truncate if needed)
            if self.max_chars:
                remaining_chars = self.max_chars - total_chars
                section_text = section_text[:remaining_chars]

            text_parts.append(section_text)
            total_chars += len(section_text)

        full_text = "\n".join(text_parts)

        # Clean up whitespace
        full_text = self._normalize_whitespace(full_text)

        logger.debug(f"Extracted {len(full_text)} characters from HTML")
        return full_text

    def _extract_sections(self, soup: Tag) -> list[tuple[str, str]]:
        """
        Extract sections from HTML.

        Returns:
            List of (section_name, section_text) tuples
        """
        sections: list[tuple[str, str]] = []

        # Find all section-like tags
        section_tags = soup.find_all(["section", "div"], class_=re.compile(r"ltx_section"))

        if not section_tags:
            # Fallback: extract all paragraphs
            text = self._extract_text(soup)
            return [("", text)]

        # Extract each section
        for section in section_tags:
            # Get section title
            title_tag = section.find(["h1", "h2", "h3", "h4", "h5", "h6"])
            section_name = title_tag.get_text(strip=True) if title_tag else ""

            # Check if this section is in our priority list
            section_name_lower = section_name.lower()
            is_priority = any(
                priority in section_name_lower for priority in self.section_priority
            )

            if is_priority or not sections:  # Always include first section
                section_text = self._extract_text(section)
                sections.append((section_name, section_text))

        # Sort by priority
        def section_priority_key(item):
            section_name = item[0].lower()
            for i, priority in enumerate(self.section_priority):
                if priority in section_name:
                    return i
            return len(self.section_priority)

        sections.sort(key=section_priority_key)

        return sections

    def _extract_text(self, element: Tag) -> str:
        """
        Extract text from an element, handling math and special content.

        Args:
            element: BeautifulSoup element

        Returns:
            Extracted text
        """
        # Replace math tags with LaTeX code (modify in place)
        for math_tag in element.find_all("math"):
            # Try to find LaTeX annotation
            latex_annotation = math_tag.find("annotation", {"encoding": "application/x-tex"})
            if latex_annotation:
                latex_code = latex_annotation.get_text(strip=True)
                # Replace the entire math tag with inline LaTeX format
                math_tag.replace_with(NavigableString(f" ${latex_code}$ "))
            else:
                # Fallback: just remove the math tag
                math_tag.replace_with(NavigableString(" "))

        # Remove citations
        for cite_tag in element.find_all(["cite", "a"], class_=re.compile(r"cite|ref")):
            cite_tag.decompose()

        # Extract text
        text = element.get_text(separator=" ", strip=True)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)

        # Replace multiple newlines with double newline
        text = re.sub(r"\n\n+", "\n\n", text)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip()


def clean_arxiv_html(
    html: str, max_chars: int | None = None, sections: list[str] | None = None
) -> str:
    """
    Convenience function to clean arXiv HTML.

    Args:
        html: Raw HTML content
        max_chars: Maximum characters to extract (None = no limit)
        sections: Specific sections to extract (None = use defaults)

    Returns:
        Cleaned text
    """
    cleaner = ArxivHtmlCleaner(max_chars=max_chars)

    if sections:
        cleaner.section_priority = sections

    return cleaner.clean(html)
