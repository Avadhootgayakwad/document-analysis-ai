import pytest
import pymupdf
import pandas as pd
from fastapi import APIRouter

from docx import Document

from app.services.extraction_service import extract_document
from app.services.chunking_service import chunk_text

from app.services.retrieval_service import (
    retrieve_context,
    build_context
)
from app.schemas.intelligence import RetrievalRequest

router = APIRouter(
    prefix="/api/intelligence",
    tags=["Document Intelligence"]
)

def test_txt_extraction(tmp_path):

    path = tmp_path / "sample.txt"

    path.write_text(
        "DocuMind AI document intelligence.",
        encoding="utf-8"
    )

    assert "DocuMind AI" in extract_document(path)


def test_pdf_extraction(tmp_path):

    path = tmp_path / "sample.pdf"

    document = pymupdf.open()

    page = document.new_page()

    page.insert_text(
        (72, 72),
        "Artificial Intelligence Platform"
    )

    document.save(path)
    document.close()

    assert "Artificial Intelligence" in extract_document(path)


def test_word_extraction(tmp_path):

    path = tmp_path / "sample.docx"

    document = Document()

    document.add_paragraph(
        "Business intelligence report."
    )

    document.save(path)

    assert "Business intelligence" in extract_document(path)


def test_excel_extraction(tmp_path):

    path = tmp_path / "sample.xlsx"

    dataframe = pd.DataFrame({
        "Product": ["Laptop", "Mobile"],
        "Sales": [100, 200]
    })

    dataframe.to_excel(path, index=False)

    result = extract_document(path)

    assert "Laptop" in result
    assert "Sales" in result


def test_csv_extraction(tmp_path):

    path = tmp_path / "sample.csv"

    path.write_text(
        "Product,Revenue\nLaptop,50000",
        encoding="utf-8"
    )

    assert "Laptop" in extract_document(path)


def test_json_extraction(tmp_path):

    path = tmp_path / "sample.json"

    path.write_text(
        '{"project": "DocuMind AI"}',
        encoding="utf-8"
    )

    assert "DocuMind AI" in extract_document(path)


def test_empty_document(tmp_path):

    path = tmp_path / "empty.txt"

    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        extract_document(path)


def test_unsupported_document(tmp_path):

    path = tmp_path / "sample.xyz"

    path.write_text("Example", encoding="utf-8")

    with pytest.raises(ValueError):
        extract_document(path)


def test_chunking():

    text = " ".join(
        f"word{i}" for i in range(1000)
    )

    chunks = chunk_text(
        text,
        chunk_size=250,
        overlap=40
    )

    assert len(chunks) > 1

    assert all(
        len(chunk.split()) <= 250
        for chunk in chunks
    )

    assert chunks[0].split()[-40:] == (
        chunks[1].split()[:40]
    )


def test_empty_chunking():

    assert chunk_text("") == []


def test_invalid_overlap():

    with pytest.raises(ValueError):

        chunk_text(
            "Example text",
            chunk_size=10,
            overlap=10
        )


def test_retrieval():

    documents = [
        {
            "id": "1",
            "filename": "finance.txt",
            "text": "Revenue increased by 25 percent."
        },
        {
            "id": "2",
            "filename": "technology.txt",
            "text": "Python is used for artificial intelligence."
        }
    ]

    results = retrieve_context(
        "Revenue growth",
        documents
    )

    assert len(results) > 0
    assert results[0]["document_id"] == "1"


def test_multi_document_retrieval():

    documents = [
        {
            "id": "1",
            "filename": "report1.txt",
            "text": "Annual sales revenue increased."
        },
        {
            "id": "2",
            "filename": "report2.txt",
            "text": "Monthly sales revenue decreased."
        }
    ]

    results = retrieve_context(
        "sales revenue",
        documents
    )

    assert len(results) == 2


def test_no_relevant_context():

    documents = [
        {
            "id": "1",
            "filename": "sample.txt",
            "text": "Python programming language"
        }
    ]

    assert retrieve_context(
        "Agriculture",
        documents
    ) == []


def test_context_builder():

    results = [
        {
            "document_id": "1",
            "filename": "report.txt",
            "chunk_index": 0,
            "content": "Revenue increased.",
            "relevance_score": 0.8
        }
    ]

    context = build_context(results)

    assert "report.txt" in context
    assert "Revenue increased." in context