"""Pydantic request/response models for the md_converter API."""

from pydantic import BaseModel, Field


class ConvertByPathRequest(BaseModel):
    """Request body for converting a file by server-side path."""

    file_path: str = Field(
        ...,
        description="Absolute path to the document on the server.",
        examples=["/data/documents/report.pdf"],
    )
    output_dir: str = Field(
        default="",
        description="Directory to save the output .md file. Defaults to the same directory as the input file.",
        examples=["/data/output"],
    )


class ConvertResponse(BaseModel):
    """Response body returned after a successful conversion."""

    output_path: str = Field(
        ...,
        description="Absolute path to the saved .md file.",
    )
    markdown_output: str = Field(
        ...,
        description="Full Markdown content of the converted document.",
    )
    file_format: str = Field(
        default="",
        description="Detected input format (pdf, docx, html, pptx, image, text).",
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
