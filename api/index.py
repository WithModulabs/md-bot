"""Vercel serverless entry point.

Vercel looks for `app` in this file when processing requests routed via vercel.json.
"""

from api.main import app  # noqa: F401 — re-exported for Vercel runtime
