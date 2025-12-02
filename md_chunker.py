#!/usr/bin/env python3
"""
Markdown chunker: splits a markdown file into pages/chunks by heading level
and optionally further splits large sections by paragraph boundaries.

Usage examples:
    python md_chunker.py \
        /home/dnshine/python-files/output.md \
        --out-dir /home/dnshine/python-files/output_chunks \
        --level 1 --max-chars 20000 --min-chars 500

This script will write chunk files and a `index.json` describing them.
"""

import argparse
import os
import re
import json
import pathlib
from typing import List, Tuple

HEADING_RE = re.compile(r"^(#{1,6})\s*(.*)$")


def split_by_heading(md_text: str, level: int = 1) -> List[Tuple[str, str]]:
    """Split markdown into blocks each starting with a heading of `level`.

    Returns list of tuples: (heading_text, body_text) where body_text does NOT include the heading line.
    If there is content before the first matching heading, it will be returned as a chunk with heading '' (empty).
    """
    pattern = re.compile(rf"^({'#' * level})\s*(.*)$", re.MULTILINE)
    parts = []
    last_pos = 0
    matches = list(pattern.finditer(md_text))

    if not matches:
        # no matching headings at this level -> return entire document as one chunk
        return [("", md_text.strip())]

    # if content before first heading
    first = matches[0]
    if first.start() > 0:
        pre = md_text[: first.start()].strip()
        if pre:
            parts.append(("", pre))

    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        body = md_text[start:end].strip()
        parts.append((heading, body))

    return parts


def split_long_chunk(block_text: str, max_chars: int) -> List[str]:
    """Split a long chunk into shorter subchunks by blank-line paragraph boundaries.

    If paragraphs are still too long, forcibly chunk by max_chars.
    """
    if len(block_text) <= max_chars:
        return [block_text]

    paragraphs = re.split(r"\n\s*\n", block_text)
    chunks = []
    cur = []
    cur_len = 0

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        pl = len(p) + 2  # add separation len
        if cur_len + pl <= max_chars:
            cur.append(p)
            cur_len += pl
        else:
            if cur:
                chunks.append('\n\n'.join(cur))
            # if this single paragraph is larger than max_chars then force-split
            if pl > max_chars:
                # naive split at max_chars inside paragraph
                start = 0
                while start < len(p):
                    chunks.append(p[start : start + max_chars])
                    start += max_chars
                cur = []
                cur_len = 0
            else:
                cur = [p]
                cur_len = pl
    if cur:
        chunks.append('\n\n'.join(cur))

    return chunks


def sanitize_filename(s: str, max_len: int = 60) -> str:
    s = s.strip()
    s = re.sub(r"[\\/:*?\"<>|]", "", s)
    s = re.sub(r"\s+", "_", s)
    if len(s) > max_len:
        s = s[: max_len - 3] + "..."
    return s or "untitled"


def chunk_markdown_file(
    infile: str,
    out_dir: str,
    level: int = 1,
    max_chars: int = 10000,
    min_chars: int = 200,
    split_large: bool = True,
    prefix: str = "chunk",
):
    p = pathlib.Path(infile)
    text = p.read_text(encoding="utf-8")

    pieces = split_by_heading(text, level=level)

    os.makedirs(out_dir, exist_ok=True)
    index = []
    file_no = 1

    raw_chunks = []

    for i, (heading, body) in enumerate(pieces, start=1):
        # Body may be empty but we still create a chunk containing the heading
        full = (f"# {heading}\n\n" + body).strip() if heading else body.strip()

        # If split_large and chunk too large, attempt to split by paragraphs
        subchunks = [full]
        if split_large and len(full) > max_chars and body:
            # try to split leaving heading at top of each subchunk
            body_subs = split_long_chunk(body, max_chars)
            subchunks = [f"# {heading}\n\n" + s for s in body_subs]

        # Possibly merge very small chunks into the next (if below min_chars) by naive approach.
        # For simplicity, we keep them but you can post-process merging if needed.

        # collect subchunks first so we can merge very small ones later
        for sub in subchunks:
            raw_chunks.append({"heading": heading, "text": sub.strip()})

    # If min_chars is set, merge very small chunks into neighboring chunks
    if min_chars and min_chars > 0 and raw_chunks:
        merged = []
        for idx, ch in enumerate(raw_chunks):
            txt = ch["text"]
            if len(txt) >= min_chars:
                # big enough to stand alone
                merged.append(ch)
            else:
                # small chunk: prefer merging into previous merged chunk
                if merged:
                    merged[-1]["text"] += "\n\n" + txt
                else:
                    # no previous chunk, merge into next if possible
                    if idx + 1 < len(raw_chunks):
                        raw_chunks[idx + 1]["text"] = txt + "\n\n" + raw_chunks[idx + 1]["text"]
                    else:
                        # only chunk and small -> keep as-is
                        merged.append(ch)
        raw_chunks = merged

    # write final chunks to disk
    for chunk in raw_chunks:
        heading = chunk.get("heading", "")
        sub = chunk.get("text", "")
        nice = sanitize_filename(heading or f"part_{file_no}")
        fname = f"{file_no:03d}_{prefix}_{nice}.md"
        out_path = os.path.join(out_dir, fname)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(sub.strip() + "\n")
        index.append({"file": fname, "heading": heading, "chars": len(sub)})
        file_no += 1

    # save index
    with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)

    return index


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Chunk a markdown file by headings (and optionally by size)")
    ap.add_argument("infile")
    ap.add_argument("--out-dir", default="./md_chunks")
    ap.add_argument("--level", type=int, default=1, help="Heading level used for chunk boundaries (1 => '#')")
    ap.add_argument("--max-chars", type=int, default=10000, help="Maximum chars per chunk (will try paragraph-splitting)")
    ap.add_argument("--min-chars", type=int, default=200, help="Minimum chars to consider if merging later (not auto-merged by default)")
    ap.add_argument("--prefix", default="page", help="Filename prefix")
    args = ap.parse_args()

    idx = chunk_markdown_file(
        args.infile,
        args.out_dir,
        level=args.level,
        max_chars=args.max_chars,
        min_chars=args.min_chars,
        split_large=True,
        prefix=args.prefix,
    )

    print(f"Wrote {len(idx)} chunk files to {args.out_dir}")
