"""Integration tests for the MdConverterGraph."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from casts.md_converter.graph import MdConverterGraph
from casts.md_converter.modules.conditions import route_by_format


# ---------------------------------------------------------------------------
# Condition (routing) tests
# ---------------------------------------------------------------------------


class TestRouteByFormat:
    @pytest.mark.parametrize(
        "file_format,expected",
        [
            ("pdf", "pdf"),
            ("docx", "docx"),
            ("html", "html"),
            ("pptx", "pptx"),
            ("image", "image"),
            ("text", "text"),
        ],
    )
    def test_routes_to_correct_extractor(self, file_format, expected):
        state = {"file_format": file_format}
        assert route_by_format(state) == expected

    def test_defaults_to_text_when_missing(self):
        assert route_by_format({}) == "text"


# ---------------------------------------------------------------------------
# Graph compilation test
# ---------------------------------------------------------------------------


class TestMdConverterGraph:
    @pytest.fixture
    def graph(self):
        with patch(
            "casts.md_converter.modules.nodes.set_structure_analyzer_agent",
            return_value=MagicMock(),
        ):
            return MdConverterGraph().build()

    def test_compiles(self, graph):
        assert graph is not None
        assert hasattr(graph, "invoke")

    def test_graph_name(self, graph):
        assert graph.name == "MdConverterGraph"


# ---------------------------------------------------------------------------
# End-to-end graph invocation (text file, fully mocked AI)
# ---------------------------------------------------------------------------


class TestMdConverterGraphEndToEnd:
    @pytest.fixture
    def mock_agent(self, structured_content):
        mock_msg = MagicMock()
        mock_msg.content = json.dumps(structured_content)
        agent = MagicMock()
        agent.invoke.return_value = {"messages": [mock_msg]}
        return agent

    def test_text_file_produces_md_output(self, tmp_path, mock_agent, structured_content):
        txt = tmp_path / "sample.txt"
        txt.write_text("# Heading\n\nParagraph.\n")

        with patch(
            "casts.md_converter.modules.nodes.set_structure_analyzer_agent",
            return_value=mock_agent,
        ):
            graph = MdConverterGraph().build()
            result = graph.invoke(
                {"file_path": str(txt), "output_dir": str(tmp_path)}
            )

        assert result["output_path"].endswith("sample.md")
        assert Path(result["output_path"]).exists()
        assert isinstance(result["markdown_output"], str)
        assert len(result["markdown_output"]) > 0

    def test_html_file_produces_md_output(self, tmp_path, mock_agent):
        html = tmp_path / "page.html"
        html.write_text("<h1>Title</h1><p>Body</p>")

        with patch(
            "casts.md_converter.modules.nodes.set_structure_analyzer_agent",
            return_value=mock_agent,
        ):
            graph = MdConverterGraph().build()
            result = graph.invoke(
                {"file_path": str(html), "output_dir": str(tmp_path)}
            )

        assert result["output_path"].endswith("page.md")

    def test_csv_file_routes_to_text_extractor(self, tmp_path, mock_agent):
        csv = tmp_path / "data.csv"
        csv.write_text("Name,Score\nAlice,100\n")

        with patch(
            "casts.md_converter.modules.nodes.set_structure_analyzer_agent",
            return_value=mock_agent,
        ):
            graph = MdConverterGraph().build()
            result = graph.invoke(
                {"file_path": str(csv), "output_dir": str(tmp_path)}
            )

        assert result["output_path"].endswith("data.md")

    def test_pdf_file_routes_to_pdf_extractor(self, tmp_path, mock_agent):
        pdf_path = str(tmp_path / "report.pdf")
        Path(pdf_path).touch()

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF content"
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with (
            patch("pdfplumber.open", return_value=mock_pdf),
            patch(
                "casts.md_converter.modules.nodes.set_structure_analyzer_agent",
                return_value=mock_agent,
            ),
        ):
            graph = MdConverterGraph().build()
            result = graph.invoke(
                {"file_path": pdf_path, "output_dir": str(tmp_path)}
            )

        assert result["output_path"].endswith("report.md")
        mock_agent.invoke.assert_called_once()
        call_content = mock_agent.invoke.call_args[0][0]["messages"][0]["content"]
        assert "PDF content" in call_content
