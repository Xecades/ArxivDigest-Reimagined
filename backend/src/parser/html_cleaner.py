"""Clean and extract text from arXiv HTML papers."""

import copy
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

        # Tags to remove completely
        self.tags_to_remove = [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
        ]

        # Classes/IDs to remove (arXiv specific)
        self.classes_to_remove = [
            "ltx_bibliography",  # References
            "ltx_page_navbar",  # Navigation bar
            "ltx_TOC",  # Table of contents
            "ltx_authors",  # Author list (already have from metadata)
            "ltx_dates",  # Dates
            "ltx_note",  # Footnotes
        ]

        # Inline tags that should preserve their text content
        self.inline_tags = ["span", "em", "strong", "i", "b", "code"]

        # Block-level tags that should trigger recursion
        self.block_tags = ["section", "div", "article"]

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

        # Try to extract main content (arXiv uses ltx_page_content or article)
        main_content = soup.find("article") or soup.find("div", class_="ltx_page_content") or soup

        # Process the content
        text = self._extract_text_recursive(main_content)

        # Clean up whitespace
        text = self._normalize_whitespace(text)

        # Apply max_chars limit if specified
        if self.max_chars and len(text) > self.max_chars:
            text = text[: self.max_chars]
            logger.debug(f"Truncated text to {self.max_chars} characters")

        logger.debug(f"Extracted {len(text)} characters from HTML")
        return text

    def _extract_text_recursive(self, element: Tag) -> str:
        """
        Recursively extract text from an element, preserving structure.

        Args:
            element: BeautifulSoup element

        Returns:
            Extracted text with proper formatting
        """
        if not element:
            return ""

        result = []

        # Handle different element types
        for child in element.children:
            if isinstance(child, NavigableString):
                # Text node - add as is
                text = str(child).strip()
                if text:
                    result.append(text)
            elif isinstance(child, Tag):
                # Dispatch to specialized handlers
                text = self._handle_tag(child)
                if text:
                    result.append(text)

        return " ".join(result)

    def _handle_tag(self, tag: Tag) -> str:
        """
        Dispatch tag handling to appropriate method.

        Args:
            tag: BeautifulSoup tag element

        Returns:
            Extracted text
        """
        tag_name = tag.name

        # Header tags
        if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return self._handle_header(tag)

        # Paragraph
        if tag_name == "p":
            return self._handle_paragraph(tag)

        # Block-level elements
        if tag_name in self.block_tags:
            return self._extract_text_recursive(tag)

        # Lists
        if tag_name in ["ul", "ol"]:
            return self._handle_list(tag)

        # Tables - but check if it's an equation table first
        if tag_name == "table":
            # Check if this is a math equation table (arXiv uses tables for equations)
            classes = tag.get("class")
            if (
                classes
                and isinstance(classes, list)
                and any("ltx_equationgroup" in cls or "ltx_eqn" in cls for cls in classes)
            ):
                # This is a math equation, extract it as such
                return self._handle_equation_table(tag)
            else:
                # Regular table
                return self._handle_table(tag)

        # Figures
        if tag_name == "figure":
            return self._handle_figure(tag)

        # Math
        if tag_name == "math":
            return self._handle_math(tag)

        # Citations
        if tag_name == "cite":
            return self._handle_citation(tag)

        # Links
        if tag_name == "a":
            return self._handle_link(tag)

        # Other inline elements
        if tag_name in self.inline_tags:
            return self._extract_text_from_element(tag)

        # Default: recurse
        return self._extract_text_recursive(tag)

    def _handle_header(self, tag: Tag) -> str:
        """Handle header tags (h1-h6)."""
        title_text = self._extract_text_from_element(tag)
        if not title_text:
            return ""

        level = int(tag.name[1])
        if level <= 2:
            return f"\n\n## {title_text}\n"
        else:
            return f"\n\n### {title_text}\n"

    def _handle_paragraph(self, tag: Tag) -> str:
        """Handle paragraph tags."""
        para_text = self._extract_text_from_element(tag)
        return f"\n{para_text}\n" if para_text else ""

    def _handle_list(self, tag: Tag) -> str:
        """Handle list tags (ul/ol)."""
        items = []
        for li in tag.find_all("li", recursive=False):
            text = self._extract_text_from_element(li)
            if text:
                items.append(f"- {text}")
        return f"\n{chr(10).join(items)}\n" if items else ""

    def _handle_table(self, tag: Tag) -> str:
        """Handle table tags."""
        table_text = self._extract_table(tag)
        return f"\n{table_text}\n" if table_text else ""

    def _handle_equation_table(self, tag: Tag) -> str:
        """Handle equation tables (arXiv uses tables to layout equations)."""
        # Extract all math content from the equation table
        equation_parts = []

        # Find equation number if present
        eq_number = ""
        eq_number_tag = tag.find("span", class_=re.compile(r"ltx_tag_equation"))
        if eq_number_tag:
            eq_number = eq_number_tag.get_text(strip=True)

        # Extract all math tags in order
        for cell in tag.find_all("td"):
            # Skip empty padding cells
            classes = cell.get("class")
            if isinstance(classes, list) and "ltx_eqn_center_padleft" in classes:
                continue
            if isinstance(classes, list) and "ltx_eqn_center_padright" in classes:
                continue

            # Extract math or text content
            math_tags = cell.find_all("math")
            if math_tags:
                for math_tag in math_tags:
                    latex_text = self._extract_math(math_tag)
                    if latex_text:
                        equation_parts.append(latex_text)
            else:
                # Check if this is the equation number cell
                if eq_number_tag and eq_number_tag in cell.descendants:
                    continue
                # Otherwise get text
                text = cell.get_text(strip=True)
                if text and text not in ["", eq_number]:
                    equation_parts.append(text)

        # Format the equation
        if equation_parts:
            equation = " ".join(equation_parts)
            if eq_number:
                return f"\n{equation} {eq_number}\n"
            else:
                return f"\n{equation}\n"
        return ""

    def _handle_figure(self, tag: Tag) -> str:
        """Handle figure tags."""
        caption = tag.find("figcaption")
        if caption:
            caption_text = self._extract_text_from_element(caption)
            if caption_text:
                # Check if caption already starts with "Figure" or "Table"
                if caption_text.startswith(("Figure", "Table")):
                    return f"\n[{caption_text}]\n"
                else:
                    return f"\n[Figure: {caption_text}]\n"
        return ""

    def _handle_math(self, tag: Tag) -> str:
        """Handle math tags."""
        latex_text = self._extract_math(tag)
        return f" {latex_text} " if latex_text else ""

    def _handle_citation(self, tag: Tag) -> str:
        """Handle citation tags."""
        cite_text = self._extract_citation_text(tag)
        return f"[{cite_text}]" if cite_text else ""

    def _handle_link(self, tag: Tag) -> str:
        """Handle link tags."""
        classes = tag.get("class")
        if classes and isinstance(classes, list) and "ltx_ref" in classes:
            # This is a reference link - extract the reference number/text
            ref_text = tag.get_text(strip=True)
            return ref_text if ref_text else ""
        else:
            # Regular link - extract text
            return self._extract_text_from_element(tag)

    def _extract_citation_text(self, cite_element: Tag) -> str:
        """
        Extract citation text from cite tag, keeping author names and years.

        Args:
            cite_element: Citation element

        Returns:
            Citation text without links
        """
        text_parts = []
        for child in cite_element.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    text_parts.append(text)
            elif isinstance(child, Tag):
                classes = child.get("class")
                if (
                    child.name == "a"
                    and classes
                    and isinstance(classes, list)
                    and "ltx_ref" in classes
                ):
                    # Extract year from reference link
                    year = child.get_text(strip=True)
                    if year:
                        text_parts.append(year)
                else:
                    # For other tags, extract text recursively
                    text = child.get_text(strip=True)
                    if text:
                        text_parts.append(text)

        return " ".join(text_parts)

    def _extract_text_from_element(self, element: Tag) -> str:
        """
        Extract all text from an element, handling special content.

        Args:
            element: BeautifulSoup element

        Returns:
            Extracted text
        """
        # Clone element to avoid modifying original
        element = copy.copy(element)

        # Handle math elements specially
        for math_tag in element.find_all("math"):
            latex_text = self._extract_math(math_tag)
            if latex_text:
                math_tag.replace_with(NavigableString(latex_text))

        # Handle citations - keep citation text but remove reference links
        for cite_tag in element.find_all("cite"):
            cite_text = self._extract_citation_text(cite_tag)
            if cite_text:
                cite_tag.replace_with(NavigableString(f"[{cite_text}]"))
            else:
                cite_tag.decompose()

        # Keep reference links but extract their text (e.g., "6.1" in "Sec. 6.1")
        for ref_tag in element.find_all("a", class_=re.compile(r"ltx_ref")):
            ref_text = ref_tag.get_text(strip=True)
            if ref_text:
                ref_tag.replace_with(NavigableString(ref_text))
            else:
                ref_tag.decompose()

        # Get text
        return element.get_text(separator=" ", strip=True)

    def _extract_math(self, math_tag: Tag) -> str:
        """
        Extract LaTeX from math tag.

        Args:
            math_tag: Math element

        Returns:
            LaTeX string with $ delimiters
        """
        # Try to find LaTeX annotation
        latex_annotation = math_tag.find("annotation", {"encoding": "application/x-tex"})
        if latex_annotation:
            latex_code = latex_annotation.get_text(strip=True)
            return f"${latex_code}$"
        return ""

    def _extract_table(self, table_element: Tag) -> str:
        """
        Extract text from table in a readable format.

        Args:
            table_element: Table element

        Returns:
            Formatted table text
        """
        # Try to find caption first
        caption_elem = table_element.find(["caption", "figcaption"])
        caption = ""
        if caption_elem:
            caption = self._extract_text_from_element(caption_elem)

        rows = []
        for tr in table_element.find_all("tr"):
            cells = []
            for cell in tr.find_all(["td", "th"]):
                text = self._extract_text_from_element(cell)
                if text:
                    cells.append(text)
            if cells:
                rows.append(" | ".join(cells))

        if not rows:
            return ""

        # Format table with caption if available
        if caption:
            # Check if caption already starts with "Table" or "Figure"
            if caption.startswith(("Table", "Figure")):
                return f"[{caption}]\n" + "\n".join(rows)
            else:
                return f"[Table: {caption}]\n" + "\n".join(rows)
        else:
            return "[Table]\n" + "\n".join(rows)

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

        # Replace multiple newlines with double newline (max)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Clean up lines
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            # Fix spacing in headers (e.g., "## 1Introduction" -> "## 1 Introduction")
            if line.startswith("#"):
                # Match header markdown syntax followed by optional number
                line = re.sub(r"^(#{1,6})\s*(\d+)([A-Z])", r"\1 \2 \3", line)
            lines.append(line)

        text = "\n".join(lines)

        return text.strip()
