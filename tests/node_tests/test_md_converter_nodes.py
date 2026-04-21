"""Unit tests for all md_converter nodes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from casts.md_converter.modules.nodes import (
    DocxExtractorNode,
    FormatDetectorNode,
    HtmlExtractorNode,
    MarkdownWriterNode,
    OcrExtractorNode,
    PdfExtractorNode,
    PptxExtractorNode,
    StructureAnalyzerNode,
    TextExtractorNode,
)


# ---------------------------------------------------------------------------
# FormatDetectorNode
# ---------------------------------------------------------------------------


class TestFormatDetectorNode:
    @pytest.mark.parametrize(
        "filename,expected_format",
        [
            ("doc.pdf", "pdf"),
            ("doc.docx", "docx"),
            ("doc.doc", "docx"),
            ("doc.html", "html"),
            ("doc.htm", "html"),
            ("doc.pptx", "pptx"),
            ("doc.ppt", "pptx"),
            ("photo.png", "image"),
            ("photo.jpg", "image"),
            ("photo.jpeg", "image"),
            ("photo.gif", "image"),
            ("photo.bmp", "image"),
            ("photo.tiff", "image"),
            ("photo.webp", "image"),
            ("data.txt", "text"),
            ("data.csv", "text"),
            ("data.tsv", "text"),
            ("notes.md", "text"),
        ],
    )
    def test_known_extensions(self, tmp_path, filename, expected_format):
        f = tmp_path / filename
        f.touch()
        node = FormatDetectorNode()
        result = node.execute({"file_path": str(f)})
        assert result["file_format"] == expected_format

    def test_unknown_extension_falls_back_to_text(self, tmp_path):
        f = tmp_path / "file.xyz"
        f.touch()
        node = FormatDetectorNode()
        result = node.execute({"file_path": str(f)})
        assert result["file_format"] == "text"


# ---------------------------------------------------------------------------
# TextExtractorNode
# ---------------------------------------------------------------------------


class TestTextExtractorNode:
    def test_plain_text(self, txt_file):
        node = TextExtractorNode()
        result = node.execute({"file_path": str(txt_file)})
        assert "Hello World" in result["raw_content"]

    def test_csv_converted_to_pipe_table(self, csv_file):
        node = TextExtractorNode()
        result = node.execute({"file_path": str(csv_file)})
        content = result["raw_content"]
        assert "|" in content
        assert "Name" in content
        assert "Alice" in content

    def test_tsv(self, tmp_path):
        f = tmp_path / "data.tsv"
        f.write_text("A\tB\n1\t2\n")
        node = TextExtractorNode()
        result = node.execute({"file_path": str(f)})
        assert "|" in result["raw_content"]


# ---------------------------------------------------------------------------
# HtmlExtractorNode
# ---------------------------------------------------------------------------


class TestHtmlExtractorNode:
    def test_extracts_headings(self, html_file):
        node = HtmlExtractorNode()
        result = node.execute({"file_path": str(html_file)})
        content = result["raw_content"]
        assert "# Main Title" in content
        assert "## Subtitle" in content

    def test_extracts_paragraph(self, html_file):
        node = HtmlExtractorNode()
        result = node.execute({"file_path": str(html_file)})
        assert "Some paragraph text." in result["raw_content"]

    def test_extracts_list_items(self, html_file):
        node = HtmlExtractorNode()
        result = node.execute({"file_path": str(html_file)})
        content = result["raw_content"]
        assert "- Item A" in content
        assert "- Item B" in content

    def test_extracts_code_block(self, html_file):
        node = HtmlExtractorNode()
        result = node.execute({"file_path": str(html_file)})
        assert "```" in result["raw_content"]

    def test_extracts_table(self, html_file):
        node = HtmlExtractorNode()
        result = node.execute({"file_path": str(html_file)})
        content = result["raw_content"]
        assert "Col1" in content
        assert "Val1" in content

    def test_script_tags_removed(self, tmp_path):
        f = tmp_path / "page.html"
        f.write_text("<html><body><script>alert('x')</script><p>clean</p></body></html>")
        node = HtmlExtractorNode()
        result = node.execute({"file_path": str(f)})
        assert "alert" not in result["raw_content"]
        assert "clean" in result["raw_content"]


# ---------------------------------------------------------------------------
# PdfExtractorNode (mocked — no real PDF needed)
# ---------------------------------------------------------------------------


class TestPdfExtractorNode:
    def test_extracts_text_from_pages(self, tmp_path):
        fake_path = str(tmp_path / "doc.pdf")

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page one content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page two content"

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page1, mock_page2]

        with patch("pdfplumber.open", return_value=mock_pdf):
            node = PdfExtractorNode()
            result = node.execute({"file_path": fake_path})

        assert "Page one content" in result["raw_content"]
        assert "Page two content" in result["raw_content"]

    def test_skips_empty_pages(self, tmp_path):
        fake_path = str(tmp_path / "doc.pdf")

        mock_page = MagicMock()
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("pdfplumber.open", return_value=mock_pdf):
            node = PdfExtractorNode()
            result = node.execute({"file_path": fake_path})

        assert result["raw_content"] == ""


# ---------------------------------------------------------------------------
# DocxExtractorNode (mocked)
# ---------------------------------------------------------------------------


class TestDocxExtractorNode:
    def _make_para_el(self, text: str, style: str = "Normal"):
        """Build a minimal mock paragraph XML element."""
        from unittest.mock import MagicMock

        style_el = MagicMock()
        style_el.get.return_value = style

        para = MagicMock()
        para.tag = "{ns}p"

        # para.find returns style element for heading check
        def find_side_effect(query):
            if "pStyle" in query:
                return style_el
            return None

        para.find.side_effect = find_side_effect

        # iter yields nodes with .text
        text_node = MagicMock()
        text_node.text = text
        para.iter.return_value = [text_node]
        return para

    def test_extracts_heading(self, tmp_path):
        fake_path = str(tmp_path / "doc.docx")
        para_el = self._make_para_el("Chapter One", style="Heading1")

        mock_body = MagicMock()
        mock_body.__iter__ = MagicMock(return_value=iter([para_el]))

        mock_doc = MagicMock()
        mock_doc.element.body = mock_body

        with patch("docx.Document", return_value=mock_doc):
            node = DocxExtractorNode()
            result = node.execute({"file_path": fake_path})

        assert "# Chapter One" in result["raw_content"]

    def test_extracts_normal_paragraph(self, tmp_path):
        fake_path = str(tmp_path / "doc.docx")
        para_el = self._make_para_el("Normal paragraph text", style="Normal")

        mock_body = MagicMock()
        mock_body.__iter__ = MagicMock(return_value=iter([para_el]))

        mock_doc = MagicMock()
        mock_doc.element.body = mock_body

        with patch("docx.Document", return_value=mock_doc):
            node = DocxExtractorNode()
            result = node.execute({"file_path": fake_path})

        assert "Normal paragraph text" in result["raw_content"]


# ---------------------------------------------------------------------------
# PptxExtractorNode (mocked)
# ---------------------------------------------------------------------------


class TestPptxExtractorNode:
    def _make_slide(self, title_text: str, body_texts: list[str]):
        mock_title = MagicMock()
        mock_title.text = title_text

        body_shapes = []
        for text in body_texts:
            para = MagicMock()
            para.text = text
            tf = MagicMock()
            tf.paragraphs = [para]
            shape = MagicMock()
            shape.has_text_frame = True
            shape.text_frame = tf
            body_shapes.append(shape)

        slide = MagicMock()
        slide.shapes.title = mock_title
        # shapes includes title + body shapes
        slide.shapes.__iter__ = MagicMock(
            return_value=iter([mock_title] + body_shapes)
        )
        return slide

    def test_extracts_slide_title_as_heading(self, tmp_path):
        fake_path = str(tmp_path / "deck.pptx")
        slide = self._make_slide("Slide Title", ["Bullet point"])

        mock_prs = MagicMock()
        mock_prs.slides = [slide]

        with patch("pptx.Presentation", return_value=mock_prs):
            node = PptxExtractorNode()
            result = node.execute({"file_path": fake_path})

        assert "## Slide Title" in result["raw_content"]
        assert "Bullet point" in result["raw_content"]

    def test_uses_slide_number_when_no_title(self, tmp_path):
        fake_path = str(tmp_path / "deck.pptx")
        slide = MagicMock()
        slide.shapes.title = None
        slide.shapes.__iter__ = MagicMock(return_value=iter([]))

        mock_prs = MagicMock()
        mock_prs.slides = [slide]

        with patch("pptx.Presentation", return_value=mock_prs):
            node = PptxExtractorNode()
            result = node.execute({"file_path": fake_path})

        assert "## Slide 1" in result["raw_content"]


# ---------------------------------------------------------------------------
# OcrExtractorNode (mocked)
# ---------------------------------------------------------------------------


class TestOcrExtractorNode:
    def test_returns_ocr_text(self, tmp_path):
        fake_path = str(tmp_path / "scan.png")

        with (
            patch("PIL.Image.open") as mock_open,
            patch("pytesseract.image_to_string", return_value="OCR extracted text"),
        ):
            mock_open.return_value = MagicMock()
            node = OcrExtractorNode()
            result = node.execute({"file_path": fake_path})

        assert result["raw_content"] == "OCR extracted text"


# ---------------------------------------------------------------------------
# StructureAnalyzerNode
# ---------------------------------------------------------------------------


class TestStructureAnalyzerNode:
    def test_parses_json_from_agent(self, state_with_raw, mock_agent_response, structured_content):
        with patch(
            "casts.md_converter.modules.nodes.set_structure_analyzer_agent",
            return_value=mock_agent_response,
        ):
            node = StructureAnalyzerNode()
            result = node.execute(state_with_raw)

        assert result["structured_content"] == structured_content

    def test_returns_empty_dict_on_invalid_json(self, state_with_raw):
        mock_msg = MagicMock()
        mock_msg.content = "not valid json at all"
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [mock_msg]}

        with patch(
            "casts.md_converter.modules.nodes.set_structure_analyzer_agent",
            return_value=mock_agent,
        ):
            node = StructureAnalyzerNode()
            result = node.execute(state_with_raw)

        assert result["structured_content"] == {}

    def test_passes_raw_content_to_agent(self, state_with_raw, mock_agent_response):
        with patch(
            "casts.md_converter.modules.nodes.set_structure_analyzer_agent",
            return_value=mock_agent_response,
        ):
            node = StructureAnalyzerNode()
            node.execute(state_with_raw)

        call_args = mock_agent_response.invoke.call_args[0][0]
        assert state_with_raw["raw_content"] in call_args["messages"][0]["content"]


# ---------------------------------------------------------------------------
# MarkdownWriterNode
# ---------------------------------------------------------------------------


class TestMarkdownWriterNode:
    def test_writes_md_file(self, tmp_path, structured_content):
        file_path = str(tmp_path / "report.pdf")
        Path(file_path).touch()
        state = {
            "file_path": file_path,
            "output_dir": str(tmp_path),
            "structured_content": structured_content,
            "raw_content": "",
        }
        node = MarkdownWriterNode()
        result = node.execute(state)

        assert result["output_path"].endswith("report.md")
        assert Path(result["output_path"]).exists()

    def test_output_contains_headings(self, tmp_path, structured_content):
        file_path = str(tmp_path / "doc.txt")
        Path(file_path).touch()
        state = {
            "file_path": file_path,
            "output_dir": str(tmp_path),
            "structured_content": structured_content,
            "raw_content": "",
        }
        node = MarkdownWriterNode()
        result = node.execute(state)
        assert "# Introduction" in result["markdown_output"]

    def test_output_contains_table(self, tmp_path, structured_content):
        file_path = str(tmp_path / "doc.txt")
        Path(file_path).touch()
        state = {
            "file_path": file_path,
            "output_dir": str(tmp_path),
            "structured_content": structured_content,
            "raw_content": "",
        }
        node = MarkdownWriterNode()
        result = node.execute(state)
        assert "| Name | Value |" in result["markdown_output"]

    def test_output_contains_code_block(self, tmp_path, structured_content):
        file_path = str(tmp_path / "doc.txt")
        Path(file_path).touch()
        state = {
            "file_path": file_path,
            "output_dir": str(tmp_path),
            "structured_content": structured_content,
            "raw_content": "",
        }
        node = MarkdownWriterNode()
        result = node.execute(state)
        assert "```python" in result["markdown_output"]

    def test_output_contains_list(self, tmp_path, structured_content):
        file_path = str(tmp_path / "doc.txt")
        Path(file_path).touch()
        state = {
            "file_path": file_path,
            "output_dir": str(tmp_path),
            "structured_content": structured_content,
            "raw_content": "",
        }
        node = MarkdownWriterNode()
        result = node.execute(state)
        assert "1. First step" in result["markdown_output"]

    def test_fallback_to_raw_content_when_empty_structured(self, tmp_path):
        file_path = str(tmp_path / "doc.txt")
        Path(file_path).touch()
        state = {
            "file_path": file_path,
            "output_dir": str(tmp_path),
            "structured_content": {},
            "raw_content": "Fallback raw text",
        }
        node = MarkdownWriterNode()
        result = node.execute(state)
        assert "Fallback raw text" in result["markdown_output"]

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "output" / "nested"
        file_path = str(tmp_path / "doc.txt")
        Path(file_path).touch()
        state = {
            "file_path": file_path,
            "output_dir": str(new_dir),
            "structured_content": {},
            "raw_content": "content",
        }
        node = MarkdownWriterNode()
        result = node.execute(state)
        assert Path(result["output_path"]).exists()
