"""Entry point for the MdConverter graph."""

from langgraph.graph import END, START, StateGraph

from casts.base_graph import BaseGraph
from casts.md_converter.modules.conditions import route_by_format
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
from casts.md_converter.modules.state import InputState, OutputState, State


class MdConverterGraph(BaseGraph):
    """Graph that converts any document format to Markdown.

    Flow:
        FormatDetectorNode
            → [PdfExtractorNode | DocxExtractorNode | HtmlExtractorNode
               | PptxExtractorNode | OcrExtractorNode | TextExtractorNode]
            → StructureAnalyzerNode
            → MarkdownWriterNode
    """

    def __init__(self) -> None:
        super().__init__()
        self.input = InputState
        self.output = OutputState
        self.state = State

    def build(self):
        builder = StateGraph(
            self.state,
            input_schema=self.input,
            output_schema=self.output,
        )

        # --- Nodes ---
        builder.add_node("FormatDetectorNode", FormatDetectorNode())
        builder.add_node("PdfExtractorNode", PdfExtractorNode())
        builder.add_node("DocxExtractorNode", DocxExtractorNode())
        builder.add_node("HtmlExtractorNode", HtmlExtractorNode())
        builder.add_node("PptxExtractorNode", PptxExtractorNode())
        builder.add_node("OcrExtractorNode", OcrExtractorNode())
        builder.add_node("TextExtractorNode", TextExtractorNode())
        builder.add_node("StructureAnalyzerNode", StructureAnalyzerNode())
        builder.add_node("MarkdownWriterNode", MarkdownWriterNode())

        # --- Entry point ---
        builder.add_edge(START, "FormatDetectorNode")

        # --- Format branching ---
        builder.add_conditional_edges(
            "FormatDetectorNode",
            route_by_format,
            {
                "pdf": "PdfExtractorNode",
                "docx": "DocxExtractorNode",
                "html": "HtmlExtractorNode",
                "pptx": "PptxExtractorNode",
                "image": "OcrExtractorNode",
                "text": "TextExtractorNode",
            },
        )

        # --- All extractors feed into StructureAnalyzerNode ---
        for extractor in (
            "PdfExtractorNode",
            "DocxExtractorNode",
            "HtmlExtractorNode",
            "PptxExtractorNode",
            "OcrExtractorNode",
            "TextExtractorNode",
        ):
            builder.add_edge(extractor, "StructureAnalyzerNode")

        # --- Sequential tail ---
        builder.add_edge("StructureAnalyzerNode", "MarkdownWriterNode")
        builder.add_edge("MarkdownWriterNode", END)

        graph = builder.compile()
        graph.name = self.name
        return graph


md_converter_graph = MdConverterGraph()
