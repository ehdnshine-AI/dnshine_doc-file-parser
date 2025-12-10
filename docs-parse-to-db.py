#!/usr/bin/env python3
"""Parse .docx files and store page-sized Markdown chunks into PostgreSQL."""

from __future__ import annotations

import argparse
import logging
import pathlib
import re
import sys
from typing import Iterable, List, Sequence

from docx import Document as LoadDocx
from docx.document import Document as DocxDocument
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch

from db_config import DB_CONFIG

LOGGER_NAME = "docs-parse-to-db"
W_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_BR = qn("w:br")
W_TYPE = qn("w:type")
W_LAST_RENDERED_PAGE_BREAK = qn("w:lastRenderedPageBreak")
W_SECT_PR = qn("w:sectPr")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def iter_block_items(parent: DocxDocument | _Cell) -> Iterable[Paragraph | Table]:
    """Yield document-level paragraphs and tables in reading order."""

    if isinstance(parent, DocxDocument):
        parent_element = parent.element.body
    elif isinstance(parent, _Cell):  # pragma: no branch - only used when tables nest
        parent_element = parent._tc
    else:  # pragma: no cover - defensive; should not happen in normal flow
        raise TypeError(f"Unsupported parent type: {type(parent)!r}")

    for child in parent_element.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, parent)
        elif child.tag.endswith("}tbl"):
            yield Table(child, parent)


def paragraph_to_markdown_lines(paragraph: Paragraph) -> List[str]:
    text = paragraph.text.strip()
    if not text:
        return []

    lines: List[str] = []
    style_name = getattr(paragraph.style, "name", "") or ""
    if style_name.startswith("Heading"):
        try:
            level = int(style_name.split()[1])
        except (IndexError, ValueError):
            level = 1
        level = max(1, min(level, 6))
        lines.append(f"{'#' * level} {text}")
    else:
        lines.append(text)

    # Emit simple hyperlink references as additional lines (best-effort).
    for run in paragraph.runs:
        hyperlink = getattr(run, "hyperlink", None)
        if not hyperlink:
            continue
        target = getattr(hyperlink, "target", "")
        if not target:
            continue
        link_text = run.text.strip() or target
        lines.append(f"[{link_text}]({target})")

    return lines


def table_to_markdown_lines(table: Table, index: int) -> List[str]:
    lines = [f"### Table {index}"]
    for row in table.rows:
        cells = [" ".join(cell.text.split()) for cell in row.cells]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def _paragraph_breaks_before(paragraph: Paragraph) -> bool:
    return bool(getattr(paragraph.paragraph_format, "page_break_before", False))


def _paragraph_has_page_break(paragraph: Paragraph) -> bool:
    element = paragraph._element
    for br in element.iter(W_BR):
        if br.get(W_TYPE) == "page":
            return True
    if any(True for _ in element.iter(W_LAST_RENDERED_PAGE_BREAK)):
        return True
    if any(True for _ in element.iter(W_SECT_PR)):
        return True
    return False


def _finalize_page(buffer: List[str]) -> str:
    content = "\n\n".join(line.strip() for line in buffer if line.strip()).strip()
    buffer.clear()
    return content


def extract_markdown_pages(document: DocxDocument) -> List[str]:
    pages: List[str] = []
    current_lines: List[str] = []
    table_counter = 0

    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            if current_lines and _paragraph_breaks_before(block):
                page = _finalize_page(current_lines)
                if page:
                    pages.append(page)
            lines = paragraph_to_markdown_lines(block)
            if lines:
                current_lines.extend(lines)
            if _paragraph_has_page_break(block):
                page = _finalize_page(current_lines)
                if page:
                    pages.append(page)
        else:  # Table
            table_counter += 1
            lines = table_to_markdown_lines(block, table_counter)
            if lines:
                current_lines.extend(lines)

    page = _finalize_page(current_lines)
    if page:
        pages.append(page)

    return pages


def convert_docx_to_pages(docx_path: pathlib.Path) -> List[str]:
    document = LoadDocx(str(docx_path))
    return extract_markdown_pages(document)


def _table_identifier(table_name: str) -> sql.Identifier:
    parts = table_name.split(".")
    if not parts or any(not IDENTIFIER_RE.match(part) for part in parts):
        raise ValueError(f"Invalid table name: {table_name}")
    return sql.Identifier(*parts)


def insert_pages(
    conn: psycopg2.extensions.connection,
    table_name: str,
    filename: str,
    pages: Sequence[str],
) -> int:
    if not pages:
        return 0

    identifier = _table_identifier(table_name)
    with conn.cursor() as cur:
        statement = sql.SQL(
            "INSERT INTO {} (filename, page_number, content) VALUES (%s, %s, %s)"
        ).format(identifier)
        values = (
            (filename, str(index), page)
            for index, page in enumerate(pages, start=1)
        )
        execute_batch(cur, statement.as_string(cur), values)
    conn.commit()
    return len(pages)


def collect_target_files(file_path: str | None, input_dir: str | None, recursive: bool) -> List[pathlib.Path]:
    if file_path:
        p = pathlib.Path(file_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        return [p]

    if not input_dir:
        raise ValueError("Either --file or --input-dir must be provided")

    base = pathlib.Path(input_dir)
    if not base.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    if not base.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    pattern = "**/*.docx" if recursive else "*.docx"
    files = sorted(p for p in base.glob(pattern) if p.is_file())
    return files


def configure_logging(verbose: bool, quiet: bool) -> logging.Logger:
    log_level = logging.WARNING
    if quiet:
        log_level = logging.ERROR
    elif verbose:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")
    return logging.getLogger(LOGGER_NAME)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert .docx files into Markdown pages and insert into PostgreSQL"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Single .docx file to ingest")
    group.add_argument("--input-dir", help="Directory containing .docx files to ingest")

    parser.add_argument("--table", default="markdown_table", help="Target table name (default: markdown_table)")
    parser.add_argument("--recursive", action="store_true", help="Recurse into subdirectories when using --input-dir")
    parser.add_argument("--verbose", action="store_true", help="Enable INFO logging")
    parser.add_argument("--quiet", action="store_true", help="Only show warnings and errors")

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logger = configure_logging(args.verbose, args.quiet)

    try:
        targets = collect_target_files(args.file, args.input_dir, args.recursive)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        logger.error(str(exc))
        return 2

    if not targets:
        logger.warning("No .docx files were found for the provided path")
        return 0

    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"],
        )
    except Exception as exc:
        logger.error("Failed to connect to PostgreSQL: %s", exc)
        return 5

    total_pages = 0
    processed_files = 0

    try:
        for path in targets:
            try:
                pages = convert_docx_to_pages(path)
            except Exception as exc:  # pragma: no cover - defensive for unexpected docx issues
                logger.error("Failed to parse %s: %s", path, exc)
                continue

            if not pages:
                logger.info("Skipping %s because no textual content was extracted", path)
                continue

            try:
                inserted = insert_pages(conn, args.table, path.name, pages)
            except Exception as exc:
                conn.rollback()
                logger.error("Failed to insert %s (rolled back): %s", path, exc)
                continue

            processed_files += 1
            total_pages += inserted
            logger.info("Inserted %d page(s) from %s", inserted, path)
    finally:
        conn.close()

    logger.info(
        "Completed run: %d file(s) processed, %d page(s) inserted into %s",
        processed_files,
        total_pages,
        args.table,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
