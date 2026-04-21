"""State definition for the md_converter graph."""

from typing import Any

from typing_extensions import TypedDict


class InputState(TypedDict):
    """Input state for the graph.

    Attributes:
        file_path: Absolute or relative path to the input document.
        output_dir: Directory where the output .md file will be saved.
                    Defaults to the same directory as the input file.
    """

    file_path: str
    output_dir: str


class OutputState(TypedDict):
    """Output state exposed to the caller.

    Attributes:
        markdown_output: Final Markdown string.
        output_path: Absolute path to the saved .md file.
    """

    markdown_output: str
    output_path: str


class State(TypedDict):
    """Full internal graph state.

    Attributes:
        file_path: Input document path.
        output_dir: Target directory for the output file.
        file_format: Detected format: pdf | docx | html | pptx | image | text.
        raw_content: Raw text extracted from the document.
        structured_content: AI-interpreted document structure (headings, tables, etc.).
        markdown_output: Final rendered Markdown string.
        output_path: Path to the saved .md file.
    """

    file_path: str
    output_dir: str
    file_format: str
    raw_content: str
    structured_content: dict[str, Any]
    markdown_output: str
    output_path: str
