from docx import Document
import os
import argparse
import logging
import pathlib
import sys


def docx_to_markdown_full(docx_path, md_path, image_dir="images"):
    """Convert a single .docx file to Markdown.

    - docx_path: path to source .docx
    - md_path: path to write resulting markdown (.md)
    - image_dir: path to store any images (will be created)
    """
    doc = Document(docx_path)
    md_lines = []

    # 이미지 저장 폴더 생성
    os.makedirs(image_dir, exist_ok=True)
    image_count = 1

    # 문단 처리 (제목 포함)
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Heading → Markdown 제목 변환
        try:
            style_name = para.style.name
        except Exception:
            style_name = ""

        if style_name.startswith("Heading"):
            try:
                level = int(style_name.replace("Heading ", ""))
            except ValueError:
                level = 1
            md_lines.append("#" * level + " " + text)
        else:
            md_lines.append(text)

        # 하이퍼링크 처리 (간단히 처리)
        for run in para.runs:
            if hasattr(run, "hyperlink") and run.hyperlink:
                try:
                    url = run.hyperlink.target
                    link_text = run.text.strip() or url
                    md_lines.append(f"[{link_text}]({url})")
                except Exception:
                    # best-effort — ignore malformed hyperlink
                    pass

    # 테이블 처리
    for t_idx, table in enumerate(doc.tables, start=1):
        md_lines.append(f"\n### Table {t_idx}\n")
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            md_lines.append("| " + " | ".join(cells) + " |")
        md_lines.append("\n")

    # 이미지 추출 (use relationship blobs) — detect extensions and avoid overwrites
    def _unique_filename(dirpath, base, ext):
        # ensure directory exists
        os.makedirs(dirpath, exist_ok=True)
        candidate = f"{base}{ext}"
        i = 1
        while os.path.exists(os.path.join(dirpath, candidate)):
            candidate = f"{base}_{i}{ext}"
            i += 1
        return candidate

    for rel in getattr(doc.part, "rels", {}).values():
        try:
            if "image" in rel.reltype:
                image_data = rel.target_part.blob

                # try to get extension from partname (eg: /word/media/image1.png)
                ext = None
                try:
                    partname = getattr(rel.target_part, 'partname', None)
                    if partname:
                        ext = pathlib.Path(partname).suffix
                except Exception:
                    ext = None

                # fallback to content_type if no ext
                if not ext:
                    try:
                        ctype = getattr(rel.target_part, 'content_type', '')
                        if '/' in ctype:
                            subtype = ctype.split('/')[1]
                            # handle image/svg+xml
                            subtype = subtype.split('+')[0]
                            ext = '.' + ( 'jpg' if subtype == 'jpeg' else subtype )
                    except Exception:
                        ext = '.bin'

                if not ext:
                    ext = '.bin'

                # pick a base name that is more descriptive than just image_ number
                base = f"image_{image_count}"
                fname = _unique_filename(image_dir, base, ext)
                image_filename = os.path.join(image_dir, fname)
                with open(image_filename, "wb") as f:
                    f.write(image_data)
                # add relative path to markdown (make path relative to md file)
                relpath = os.path.relpath(image_filename, os.path.dirname(md_path))
                md_lines.append(f"![{base}]({relpath})")
                image_count += 1
        except Exception:
            # ignore image extraction errors for robustness
            continue

    # Markdown 저장
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md_lines))

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