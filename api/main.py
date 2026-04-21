"""FastAPI application entry point for the md_converter service."""

from fastapi import FastAPI

from api.routes import router

app = FastAPI(
    title="md-bot API",
    description=(
        "Converts any document (PDF, DOCX, HTML, PPTX, image, text/CSV) "
        "into a clean Markdown file using an AI-powered LangGraph pipeline."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(router)
