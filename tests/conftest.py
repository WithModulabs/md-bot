"""Shared pytest fixtures for md_converter tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# File fixtures (tmp_path-based)
# ---------------------------------------------------------------------------


@pytest.fixture
def txt_file(tmp_path: Path) -> Path:
    f = tmp_path / "sample.txt"
    f.write_text("Hello World\nThis is a test document.\n- item one\n- item two\n")
    return f


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    f = tmp_path / "data.csv"
    f.write_text("Name,Age,City\nAlice,30,Seoul\nBob,25,Busan\n")
    return f


@pytest.fixture
def html_file(tmp_path: Path) -> Path:
    f = tmp_path / "page.html"
    f.write_text(
        "<html><body>"
        "<h1>Main Title</h1>"
        "<h2>Subtitle</h2>"
        "<p>Some paragraph text.</p>"
        "<ul><li>Item A</li><li>Item B</li></ul>"
        "<pre>code block here</pre>"
        "<table><tr><th>Col1</th><th>Col2</th></tr>"
        "<tr><td>Val1</td><td>Val2</td></tr></table>"
        "</body></html>"
    )
    return f


# ---------------------------------------------------------------------------
# State fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def base_state(txt_file: Path) -> dict[str, Any]:
    return {
        "file_path": str(txt_file),
        "output_dir": str(txt_file.parent),
        "file_format": "",
        "raw_content": "",
        "structured_content": {},
        "markdown_output": "",
        "output_path": "",
    }


@pytest.fixture
def state_with_raw(base_state: dict[str, Any]) -> dict[str, Any]:
    state = dict(base_state)
    state["raw_content"] = (
        "Introduction\n\n"
        "1. First step\n"
        "2. Second step\n\n"
        "| Name | Value |\n"
        "| Alice | 42 |\n\n"
        "```python\nprint('hello')\n```\n"
    )
    state["file_format"] = "text"
    return state


@pytest.fixture
def structured_content() -> dict[str, Any]:
    return {
        "headings": [{"level": 1, "text": "Introduction", "position": 0}],
        "paragraphs": [{"text": "Some paragraph.", "position": 10}],
        "tables": [{"headers": ["Name", "Value"], "rows": [["Alice", "42"]]}],
        "code_blocks": [{"language": "python", "content": "print('hello')"}],
        "lists": [{"ordered": True, "items": ["First step", "Second step"]}],
    }


# ---------------------------------------------------------------------------
# Mock agent fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_agent_response(structured_content: dict[str, Any]):
    """Returns a mock agent that outputs valid structured_content JSON."""
    mock_msg = MagicMock()
    mock_msg.content = json.dumps(structured_content)

    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {"messages": [mock_msg]}
    return mock_agent
