"""Node implementations for the md_converter graph."""

from __future__ import annotations

import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from casts.base_node import BaseNode
from casts.md_converter.modules.agents import set_structure_analyzer_agent

# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

_EXT_FORMAT: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".html": "html",
    ".htm": "html",
    ".pptx": "pptx",
    ".ppt": "pptx",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".tif": "image",
    ".webp": "image",
    ".txt": "text",
    ".csv": "text",
    ".tsv": "text",
    ".md": "text",
}


class FormatDetectorNode(BaseNode):
    """Detect document format from file extension or MIME type."""

    def __init__(self):
        super().__init__()

    def execute(self, state):
        file_path = state["file_path"]
        ext = Path(file_path).suffix.lower()
        file_format = _EXT_FORMAT.get(ext)

        if not file_format:
            mime, _ = mimetypes.guess_type(file_path)
            if mime:
                if "pdf" in mime:
                    file_format = "pdf"
                elif "word" in mime or "officedocument.wordprocessingml" in mime:
                    file_format = "docx"
                elif "html" in mime:
                    file_format = "html"
                elif "presentation" in mime:
                    file_format = "pptx"
                elif mime.startswith("image/"):
                    file_format = "image"
                else:
                    file_format = "text"
            else:
                file_format = "text"

        return {"file_format": file_format}


# ---------------------------------------------------------------------------
# Format-specific extractors
# ---------------------------------------------------------------------------


class PdfExtractorNode(BaseNode):
    """Extract text and layout from a PDF file using pdfplumber."""

    def __init__(self):
        super().__init__()

    def execute(self, state):
        import pdfplumber

        text_parts: list[str] = []
        with pdfplumber.open(state["file_path"]) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return {"raw_content": "\n\n".join(text_parts)}


class DocxExtractorNode(BaseNode):
    """Extract paragraphs, headings, and tables from a DOCX file."""

    def __init__(self):
        super().__init__()

    def execute(self, state):
        from docx import Document
        from docx.oxml.ns import qn

        doc = Document(state["file_path"])
        parts: list[str] = []

        for block in doc.element.body:
            tag = block.tag.split("}")[-1]
            if tag == "p":
                # Use python-docx paragraph style to prepend heading markers
                para_el = block
                style_name = ""
                style_el = para_el.find(f".//{qn('w:pStyle')}")
                if style_el is not None:
                    style_name = style_el.get(qn("w:val"), "")
                text = "".join(n.text or "" for n in para_el.iter() if hasattr(n, "text"))
                if not text.strip():
                    continue
                if "Heading" in style_name:
                    level = int(style_name[-1]) if style_name[-1].isdigit() else 1
                    parts.append(f"{'#' * level} {text.strip()}")
                else:
                    parts.append(text.strip())
            elif tag == "tbl":
                from docx.table import Table
                tbl = Table(block, doc)
                for row in tbl.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    parts.append(f"| {row_text} |")

        return {"raw_content": "\n\n".join(parts)}


class HtmlExtractorNode(BaseNode):
    """Extract structured content from HTML using BeautifulSoup."""

    def __init__(self):
        super().__init__()

    def execute(self, state):
        from bs4 import BeautifulSoup

        file_path = state["file_path"]
        with open(file_path, encoding="utf-8", errors="replace") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style tags
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        parts: list[str] = []
        for el in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "ul", "ol", "table"]
        ):
            tag_name = el.name
            text = el.get_text(separator=" ").strip()
            if not text:
                continue
            if tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                level = int(tag_name[1])
                parts.append(f"{'#' * level} {text}")
            elif tag_name == "pre":
                parts.append(f"```\n{text}\n```")
            elif tag_name in ("ul", "ol"):
                for li in el.find_all("li", recursive=False):
                    parts.append(f"- {li.get_text(separator=' ').strip()}")
            elif tag_name == "table":
                rows = el.find_all("tr")
                for row in rows:
                    cells = row.find_all(["th", "td"])
                    parts.append("| " + " | ".join(c.get_text().strip() for c in cells) + " |")
            else:
                parts.append(text)

        return {"raw_content": "\n\n".join(parts)}


class PptxExtractorNode(BaseNode):
    """Extract slide titles and body text from a PPTX file."""

    def __init__(self):
        super().__init__()

    def execute(self, state):
        from pptx import Presentation
        from pptx.util import Pt

        prs = Presentation(state["file_path"])
        parts: list[str] = []

        for slide_num, slide in enumerate(prs.slides, start=1):
            title = slide.shapes.title
            title_text = title.text.strip() if title and title.text else f"Slide {slide_num}"
            parts.append(f"## {title_text}")

            for shape in slide.shapes:
                if shape == title or not shape.has_text_frame:
                    continue
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        parts.append(text)

        return {"raw_content": "\n\n".join(parts)}


class OcrExtractorNode(BaseNode):
    """Extract text from image files using pytesseract (OCR)."""

    def __init__(self):
        super().__init__()

    def execute(self, state):
        import pytesseract
        from PIL import Image

        img = Image.open(state["file_path"])
        text = pytesseract.image_to_string(img)
        return {"raw_content": text}


class TextExtractorNode(BaseNode):
    """Read plain text or CSV files directly."""

    def __init__(self):
        super().__init__()

    def execute(self, state):
        file_path = state["file_path"]
        ext = Path(file_path).suffix.lower()

        with open(file_path, encoding="utf-8", errors="replace") as f:
            content = f.read()

        if ext in (".csv", ".tsv"):
            delimiter = "\t" if ext == ".tsv" else ","
            lines = content.splitlines()
            table_lines: list[str] = []
            for line in lines:
                cells = line.split(delimiter)
                table_lines.append("| " + " | ".join(c.strip() for c in cells) + " |")
            content = "\n".join(table_lines)

        return {"raw_content": content}


# ---------------------------------------------------------------------------
# AI structure analysis
# ---------------------------------------------------------------------------


class StructureAnalyzerNode(BaseNode):
    """Invoke the StructureAnalyzerAgent to interpret raw content into a structured dict."""

    def __init__(self):
        super().__init__()
        self.agent = set_structure_analyzer_agent()

    def execute(self, state):
        raw_content = state.get("raw_content", "")
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": raw_content}]}
        )

        # Extract the last AI message content (should be a JSON summary)
        messages = result.get("messages", [])
        structured_content: dict[str, Any] = {}
        for msg in reversed(messages):
            content = getattr(msg, "content", None) or (
                msg.get("content") if isinstance(msg, dict) else None
            )
            if content and isinstance(content, str):
                try:
                    structured_content = json.loads(content)
                    break
                except json.JSONDecodeError:
                    continue

        return {"structured_content": structured_content}


# ---------------------------------------------------------------------------
# Markdown writer
# ---------------------------------------------------------------------------


class MarkdownWriterNode(BaseNode):
    """Render structured_content into a Markdown file and save it."""

    def __init__(self):
        super().__init__()

    def execute(self, state):
        sc: dict[str, Any] = state.get("structured_content", {})
        file_path = state["file_path"]
        output_dir = state.get("output_dir") or str(Path(file_path).parent)

        lines: list[str] = []

        # Merge all elements with their positions for ordering
        elements: list[tuple[int, str]] = []

        for h in sc.get("headings", []):
            marker = "#" * max(1, min(int(h.get("level", 2)), 6))
            elements.append((int(h.get("position", 0)), f"{marker} {h.get('text', '')}"))

        for para in sc.get("paragraphs", []):
            if isinstance(para, dict):
                elements.append((para.get("position", 9999), para.get("text", "")))
            elif isinstance(para, str):
                elements.append((9999, para))

        elements.sort(key=lambda x: x[0])
        for _, text in elements:
            lines.append(text)
            lines.append("")

        for table in sc.get("tables", []):
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            if headers:
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join("---" for _ in headers) + " |")
            for row in rows:
                lines.append("| " + " | ".join(str(c) for c in row) + " |")
            lines.append("")

        for code in sc.get("code_blocks", []):
            lang = code.get("language", "")
            lines.append(f"```{lang}")
            lines.append(code.get("content", ""))
            lines.append("```")
            lines.append("")

        for lst in sc.get("lists", []):
            for i, item in enumerate(lst.get("items", []), start=1):
                prefix = f"{i}." if lst.get("ordered") else "-"
                lines.append(f"{prefix} {item}")
            lines.append("")

        # Fallback: if structured_content was empty, use raw_content directly
        if not lines:
            lines = [state.get("raw_content", "")]

        markdown_output = "\n".join(lines)

        stem = Path(file_path).stem
        output_path = str(Path(output_dir) / f"{stem}.md")
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_output)

        return {"markdown_output": markdown_output, "output_path": output_path}
