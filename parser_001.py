from docx import Document
from docx.document import Document as DocxDocument
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
import os
import argparse
import logging
import pathlib
import sys


W_BR = qn("w:br")
W_TYPE = qn("w:type")
W_LAST_RENDERED_PAGE_BREAK = qn("w:lastRenderedPageBreak")
W_SECT_PR = qn("w:sectPr")
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def iter_block_items(parent: DocxDocument | _Cell):
    """Yield paragraphs and tables in the order they appear."""
    if isinstance(parent, DocxDocument):
        parent_element = parent.element.body
    else:
        parent_element = parent._tc

    for child in parent_element.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, parent)
        elif child.tag.endswith("}tbl"):
            yield Table(child, parent)


def paragraph_to_markdown_lines(paragraph: Paragraph, image_helper=None):
    """Convert a paragraph (including heading/hyperlink) to markdown lines."""
    text = paragraph.text.strip()
    if not text:
        return []

    lines = []
    style_name = getattr(paragraph.style, "name", "") or ""
    if style_name.startswith("Heading"):
        try:
            level = int(style_name.replace("Heading ", ""))
        except ValueError:
            level = 1
        lines.append("#" * max(1, min(level, 6)) + " " + text)
    else:
        lines.append(text)

    for run in paragraph.runs:
        hyperlink = getattr(run, "hyperlink", None)
        if not hyperlink:
            continue
        try:
            url = hyperlink.target
            if not url:
                continue
            link_text = run.text.strip() or url
            lines.append(f"[{link_text}]({url})")
        except Exception:
            continue
        if image_helper:
            lines.extend(image_helper.markdown_for_run(run))

    return lines


def table_to_markdown_lines(table: Table, index: int):
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


class ImageExtractor:
    """Extract inline images and provide markdown references in document order."""

    def __init__(self, doc: DocxDocument, image_dir: str, md_path: str):
        self.doc = doc
        self.image_dir = image_dir
        self.md_path = md_path
        self.counter = 1
        self.cache = {}

    def _save_part(self, part):
        ext = pathlib.Path(part.partname).suffix or ""
        if not ext:
            ctype = getattr(part, "content_type", "")
            if "/" in ctype:
                subtype = ctype.split("/")[1].split("+")[0]
                ext = "." + ("jpg" if subtype == "jpeg" else subtype)
            else:
                ext = ".bin"
        base = f"image_{self.counter}"
        fname = self._unique_filename(base, ext)
        filepath = os.path.join(self.image_dir, fname)
        with open(filepath, "wb") as fh:
            fh.write(part.blob)
        self.counter += 1
        relpath = os.path.relpath(filepath, os.path.dirname(self.md_path))
        return relpath

    def _unique_filename(self, base, ext):
        os.makedirs(self.image_dir, exist_ok=True)
        candidate = f"{base}{ext}"
        i = 1
        while os.path.exists(os.path.join(self.image_dir, candidate)):
            candidate = f"{base}_{i}{ext}"
            i += 1
        return candidate

    def markdown_for_run(self, run) -> list[str]:
        md_lines = []
        elements = run._element.xpath(
            ".//a:blip/@r:embed",
            namespaces={"a": A_NS, "r": R_NS},
        )
        for embed in elements:
            if embed in self.cache:
                relpath = self.cache[embed]
            else:
                part = self.doc.part.related_parts.get(embed)
                if not part:
                    continue
                relpath = self._save_part(part)
                self.cache[embed] = relpath
            md_lines.append(f"![image]({relpath})")
        return md_lines


def convert_docx_to_pages(docx_path, image_dir, md_path):
    """Return list of markdown strings, one per logical page."""
    doc = Document(docx_path)
    os.makedirs(image_dir, exist_ok=True)
    image_helper = ImageExtractor(doc, image_dir, md_path)

    pages = []
    current_lines = []
    table_counter = 0

    def flush_page():
        content = "\n\n".join(line.strip() for line in current_lines if line.strip()).strip()
        if content:
            pages.append(content)
        current_lines.clear()

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            if current_lines and _paragraph_breaks_before(block):
                flush_page()
            lines = paragraph_to_markdown_lines(block, image_helper)
            if lines:
                current_lines.extend(lines)
            if _paragraph_has_page_break(block):
                flush_page()
        else:
            table_counter += 1
            current_lines.extend(table_to_markdown_lines(block, table_counter))

    flush_page()

    return pages


def docx_to_markdown_full(docx_path, md_path, image_dir="images"):
    """Convert a single .docx file to Markdown with page markers."""
    pages = convert_docx_to_pages(docx_path, image_dir, md_path)

    if not pages:
        content = ""
    elif len(pages) == 1:
        content = pages[0]
    else:
        sections = []
        for idx, page in enumerate(pages, start=1):
            sections.append(f"<!-- page:{idx} -->\n{page}")
        content = "\n\n".join(sections)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + ("\n" if content else ""))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Convert .docx files into Markdown files (single-file or directory batch mode)")
    ap.add_argument("--file", type=str, help="Path to input .docx file")
    ap.add_argument("--output-dir", type=str, help="Path to output .md file")
    ap.add_argument("--image-dir", type=str, help="image path.")
    args = ap.parse_args()

    print(f"file path.....{args.file}")
    print(f"file path.....{args.output_dir}")
    print(f"file path.....{args.image_dir}")
                    
    docx_to_markdown_full(args.file,args.output_dir,args.image_dir)
