"""Condition (route) functions for the md_converter graph."""

from casts.md_converter.modules.state import State


def route_by_format(state: State) -> str:
    """Route to the appropriate extractor node based on detected file format.

    Args:
        state: Current graph state containing `file_format`.

    Returns:
        Node name string: one of pdf | docx | html | pptx | image | text.
    """
    return state.get("file_format", "text")
