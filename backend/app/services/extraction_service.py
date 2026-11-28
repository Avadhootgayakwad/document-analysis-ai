import json
from pathlib import Path

import pymupdf
import pandas as pd
from docx import Document as WordDocument


MAX_EXTRACTED_CHARACTERS = 2_000_000


def extract_pdf(path: Path) -> str:

    sections = []

    with pymupdf.open(path) as document:

        if document.needs_pass:
            raise ValueError("Password-protected PDF.")

        for index, page in enumerate(document):

            text = page.get_text().strip()

            if text:
                sections.append(
                    f"[Page {index + 1}]\n{text}"
                )

    return "\n\n".join(sections)


def extract_word(path: Path) -> str:

    document = WordDocument(path)

    sections = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    for index, table in enumerate(document.tables):

        sections.append(f"[Table {index + 1}]")

        for row in table.rows:

            values = [
                cell.text.strip()
                for cell in row.cells
            ]

            sections.append(" | ".join(values))

    return "\n".join(sections)


def extract_excel(path: Path) -> str:

    sections = []

    engine = (
        "xlrd"
        if path.suffix.lower() == ".xls"
        else "openpyxl"
    )

    with pd.ExcelFile(path, engine=engine) as workbook:

        for sheet_name in workbook.sheet_names:

            dataframe = workbook.parse(
                sheet_name,
                nrows=5000
            )

            sections.append(
                f"[Sheet: {sheet_name}]\n"
                f"Columns: {', '.join(map(str, dataframe.columns))}\n"
                f"{dataframe.to_csv(index=False)}"
            )

    return "\n\n".join(sections)


def extract_csv(path: Path) -> str:

    dataframe = pd.read_csv(
        path,
        nrows=10000
    )

    return (
        f"Columns: {', '.join(map(str, dataframe.columns))}\n"
        f"{dataframe.to_csv(index=False)}"
    )


def extract_plain_text(path: Path) -> str:

    for encoding in ["utf-8-sig", "utf-16", "cp1252"]:

        try:
            return path.read_text(encoding=encoding)

        except UnicodeError:
            continue

    raise ValueError("Unable to decode text file.")


def extract_json(path: Path) -> str:

    content = extract_plain_text(path)

    data = json.loads(content)

    return json.dumps(
        data,
        indent=2,
        ensure_ascii=False
    )


def extract_document(path: Path) -> str:

    if not path.is_file():
        raise FileNotFoundError("Document file not found.")

    extension = path.suffix.lower()

    extractors = {
        ".pdf": extract_pdf,
        ".docx": extract_word,
        ".xlsx": extract_excel,
        ".xls": extract_excel,
        ".csv": extract_csv,
        ".txt": extract_plain_text,
        ".md": extract_plain_text,
        ".json": extract_json
    }

    if extension == ".doc":
        raise ValueError(
            "Legacy .doc files must be converted to .docx."
        )

    extractor = extractors.get(extension)

    if extractor is None:
        raise ValueError("Unsupported document format.")

    text = extractor(path).strip()

    if not text:
        raise ValueError(
            "No readable text found. Scanned PDFs may require OCR."
        )

    return text[:MAX_EXTRACTED_CHARACTERS]