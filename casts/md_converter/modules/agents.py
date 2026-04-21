"""Agent factory for the md_converter graph."""

from langchain.agents import create_agent

from casts.md_converter.modules.models import get_structure_analyzer_model
from casts.md_converter.modules.prompts import STRUCTURE_ANALYZER_SYSTEM
from casts.md_converter.modules.tools import (
    detect_code_blocks,
    detect_headings,
    detect_lists,
    detect_tables,
)


def set_structure_analyzer_agent():
    """Create and return the StructureAnalyzerAgent.

    Returns:
        CompiledGraph: A create_agent subgraph ready to invoke.
    """
    return create_agent(
        model=get_structure_analyzer_model(),
        tools=[detect_headings, detect_tables, detect_code_blocks, detect_lists],
        system_prompt=STRUCTURE_ANALYZER_SYSTEM,
    )
