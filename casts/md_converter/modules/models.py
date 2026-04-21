"""Model factory for the md_converter graph."""

from langchain_openai import ChatOpenAI


def get_structure_analyzer_model() -> ChatOpenAI:
    """Return the model used by StructureAnalyzerAgent.

    Returns:
        ChatOpenAI: Configured model instance.
    """
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)
