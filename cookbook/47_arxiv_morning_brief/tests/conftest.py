"""Shared fixtures for arXiv Morning Brief (SPL 2.0) tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the recipe directory importable as a plain module so test files can do
#   import tools as ambt
RECIPE_DIR = Path(__file__).parent.parent
if str(RECIPE_DIR) not in sys.path:
    sys.path.insert(0, str(RECIPE_DIR))


@pytest.fixture(scope="session")
def sample_pdf(tmp_path_factory) -> Path:
    """Create a minimal 2-page PDF for testing.

    Text extraction returns empty string from blank pages, so tests that need
    real text should mock PDFExtractor.from_file directly.
    """
    try:
        from pypdf import PdfWriter
    except ImportError:
        pytest.skip("pypdf not installed")

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)

    pdf_path = tmp_path_factory.mktemp("fixtures") / "sample.pdf"
    with open(pdf_path, "wb") as fh:
        writer.write(fh)
    return pdf_path


@pytest.fixture(scope="session")
def sample_chunks_json() -> str:
    """Known structured chunk output for use in workflow dry-run mocks."""
    chunks = [
        {"title": "ABSTRACT",        "text": "We propose a novel method.",    "page": 1},
        {"title": "1. INTRODUCTION", "text": "This is the introduction.",      "page": 2},
        {"title": "2. METHODS",      "text": "We use the following approach.", "page": 3},
    ]
    return json.dumps(chunks)
