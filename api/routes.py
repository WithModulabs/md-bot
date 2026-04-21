"""API routes for the md_converter service."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from api.models import ConvertByPathRequest, ConvertResponse, HealthResponse
from casts.md_converter.graph import md_converter_graph

router = APIRouter()

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(status="ok")


# ---------------------------------------------------------------------------
# POST /convert/upload  — multipart file upload
# ---------------------------------------------------------------------------


@router.post(
    "/convert/upload",
    response_model=ConvertResponse,
    status_code=status.HTTP_200_OK,
    summary="Convert an uploaded file to Markdown",
    tags=["Conversion"],
)
async def convert_upload(file: UploadFile) -> ConvertResponse:
    """Accept a file upload, convert it to Markdown, and return the result.

    The uploaded file is saved to a temporary directory, processed by the
    md_converter graph, and the resulting Markdown is returned in the response
    body together with the path to the saved `.md` file.

    Supported formats: PDF, DOCX, HTML, PPTX, PNG/JPG (OCR), TXT, CSV.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No filename provided.",
        )

    suffix = Path(file.filename).suffix or ".tmp"

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save uploaded bytes to a temp file preserving the original extension
        tmp_input = Path(tmp_dir) / file.filename
        content = await file.read()
        tmp_input.write_bytes(content)

        try:
            result = md_converter_graph.invoke(
                {"file_path": str(tmp_input), "output_dir": tmp_dir}
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Conversion failed: {exc}",
            ) from exc

        return ConvertResponse(
            output_path=result["output_path"],
            markdown_output=result["markdown_output"],
            file_format=result.get("file_format", ""),
        )


# ---------------------------------------------------------------------------
# POST /convert/path  — server-side file path
# ---------------------------------------------------------------------------


@router.post(
    "/convert/path",
    response_model=ConvertResponse,
    status_code=status.HTTP_200_OK,
    summary="Convert a server-side file to Markdown",
    tags=["Conversion"],
)
def convert_by_path(body: ConvertByPathRequest) -> ConvertResponse:
    """Convert a document already present on the server by its absolute path.

    The `output_dir` field is optional — if omitted the `.md` file is saved
    next to the source document.
    """
    file_path = Path(body.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {body.file_path}",
        )
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Path is not a file: {body.file_path}",
        )

    output_dir = body.output_dir or str(file_path.parent)

    try:
        result = md_converter_graph.invoke(
            {"file_path": str(file_path), "output_dir": output_dir}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {exc}",
        ) from exc

    return ConvertResponse(
        output_path=result["output_path"],
        markdown_output=result["markdown_output"],
        file_format=result.get("file_format", ""),
    )


# ---------------------------------------------------------------------------
# GET /convert/download  — download the saved .md file
# ---------------------------------------------------------------------------


@router.get(
    "/convert/download",
    summary="Download a previously converted .md file",
    tags=["Conversion"],
    response_class=FileResponse,
)
def download_md(output_path: str) -> FileResponse:
    """Download a `.md` file by its absolute server path.

    Use the `output_path` value returned by a prior `/convert/*` call.
    """
    md_path = Path(output_path)
    if not md_path.exists() or not md_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {output_path}",
        )
    if md_path.suffix.lower() != ".md":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="output_path must point to a .md file.",
        )
    return FileResponse(
        path=str(md_path),
        media_type="text/markdown",
        filename=md_path.name,
    )
