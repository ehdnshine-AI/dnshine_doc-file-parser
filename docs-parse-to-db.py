from docx import Document
import os
import argparse
import logging
import pathlib
import sys

import os
import pathlib
from docx import Document
import psycopg2
from db_config import DB_CONFIG

def docx_to_markdown_full(docx_path, md_path, image_dir="images"):
    """Convert a single .docx file to Markdown.

    - docx_path: path to source .docx
    - md_path: path to write resulting markdown (.md)
    - image_dir: path to store any images (will be created)
    """
    doc = Document(docx_path)
    md_lines = []

    # 이미지 저장 폴더 생성




    def insert_markdown_to_db(content):
        """Insert markdown content into PostgreSQL markdown_table."""
        conn = None
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                dbname=DB_CONFIG["database"]
            )
            cur = conn.cursor()
            # Create table if not exists
            create_table_query = '''
                CREATE TABLE IF NOT EXISTS markdown_table (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL
                );
            '''
            cur.execute(create_table_query)
            # Insert content
            insert_query = "INSERT INTO markdown_table (content) VALUES (%s)"
            cur.execute(insert_query, (content,))
            conn.commit()
            cur.close()
        except Exception as e:
            print(f"DB Insert Error: {e}")
        finally:
            if conn:
                conn.close()
        if not text:
    def docx_to_markdown_full(docx_path, md_path, image_dir="images"):
        """Convert a single .docx file to Markdown and save to file and DB."""
        doc = Document(docx_path)
        md_lines = []

        # Create image directory
        os.makedirs(image_dir, exist_ok=True)
        image_count = 1

        # Process paragraphs (headings and text)
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

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

            # Simple hyperlink handling
            for run in para.runs:
                if hasattr(run, "hyperlink") and run.hyperlink:
                    try:
                        url = run.hyperlink.target
                        link_text = run.text.strip() or url
                        md_lines.append(f"[{link_text}]({url})")
                    except Exception:
                        pass

        # Process tables
        for t_idx, table in enumerate(doc.tables, start=1):
            md_lines.append(f"\n### Table {t_idx}\n")
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                md_lines.append("| " + " | ".join(cells) + " |")
            md_lines.append("\n")

        # Image extraction helper
        def _unique_filename(dirpath, base, ext):
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
                    ext = None
                    try:
                        partname = getattr(rel.target_part, 'partname', None)
                        if partname:
                            ext = pathlib.Path(partname).suffix
                    except Exception:
                        ext = None

                    if not ext:
                        try:
                            ctype = getattr(rel.target_part, 'content_type', '')
                            if '/' in ctype:
                                subtype = ctype.split('/')[1]
                                subtype = subtype.split('+')[0]
                                ext = '.' + ('jpg' if subtype == 'jpeg' else subtype)
                        except Exception:
                            ext = '.bin'

                    if not ext:
                        ext = '.bin'

                    base = f"image_{image_count}"
                    fname = _unique_filename(image_dir, base, ext)
                    image_filename = os.path.join(image_dir, fname)
                    with open(image_filename, "wb") as f:
                        f.write(image_data)
                    relpath = os.path.relpath(image_filename, os.path.dirname(md_path))
                    md_lines.append(f"![{base}]({relpath})")
                    image_count += 1
            except Exception:
                continue

        markdown_content = "\n\n".join(md_lines)

        # Write markdown file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Insert into DB
        insert_markdown_to_db(markdown_content)
        raise PermissionError(f"Cannot create or write to output directory: {output_dir} — check permissions")
    except Exception as e:
        raise OSError(f"Failed to create output directory {output_dir}: {e}")

    pattern = "**/*.docx" if recursive else "*.docx"
    files = list(p.glob(pattern))
    processed = []

    for f in files:
        if not f.is_file():
            continue

        # construct output names
        stem = f.stem
        md_name = stem + ".md"
        md_path = out_p.joinpath(md_name)

        # image dir: per-file subdir under output_dir
        image_dir = out_p.joinpath(f"{stem}_{image_subdir_name}")
        try:
            docx_to_markdown_full(str(f), str(md_path), str(image_dir))
            processed.append((str(f), str(md_path), str(image_dir)))
            if logger:
                logger.info("Converted: %s -> %s (images: %s)", f, md_path, image_dir)
            else:
                print(f"Converted: {f} -> {md_path} (images: {image_dir})")
        except Exception as e:
            if logger:
                logger.exception("Failed to convert %s", f)
            else:
                print(f"Failed to convert {f}: {e}", file=sys.stderr)

    if not processed and logger:
        logger.warning("No .docx files were found in %s (pattern=%s)", input_dir, pattern)

    return processed


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Convert .docx files into Markdown files (single-file or directory batch mode)")

    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-dir", help="Directory with .docx files to convert")
    group.add_argument("--file", help="Single .docx file to convert")

    ap.add_argument("--output-dir", default=None, help="Directory to write .md files and images (for --file, defaults to parent folder)" )
    ap.add_argument("--images-subdir", default="images", help="Name for per-file images subdirectory suffix (default 'images')")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subdirectories to find .docx files")
    ap.add_argument("--quiet", action="store_true", help="Minimal output")
    ap.add_argument("--verbose", action="store_true", help="Show detailed processing info (INFO level)")
    args = ap.parse_args()

    # configure logging
    log_level = logging.WARNING
    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger("docs-parser")

    try:
        if args.file:
            # single-file mode
            fpath = pathlib.Path(args.file)
            if not fpath.exists() or not fpath.is_file():
                logger.error("Input file does not exist or is not a file: %s", args.file)
                sys.exit(2)

            # determine output directory
            out_dir = args.output_dir or str(fpath.parent)
            pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)

            stem = fpath.stem
            md_path = pathlib.Path(out_dir).joinpath(stem + ".md")
            image_dir = pathlib.Path(out_dir).joinpath(f"{stem}_{args.images_subdir}")
            try:
                docx_to_markdown_full(str(fpath), str(md_path), str(image_dir))
                logger.info("Converted file: %s -> %s (images: %s)", fpath, md_path, image_dir)
            except Exception:
                logger.exception("Failed to convert %s", fpath)
                sys.exit(1)
        else:
            # directory/batch mode
            if not args.input_dir:
                logger.error("--input-dir must be provided in directory mode.")
                sys.exit(2)
            results = process_directory(args.input_dir, args.output_dir or '.', image_subdir_name=args.images_subdir, recursive=args.recursive, logger=logger)
            if not args.quiet:
                logger.info("Processed %d files.", len(results))
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.info("Verify the path and try again.")
        sys.exit(2)
    except NotADirectoryError as e:
        logger.error(str(e))
        sys.exit(2)
    except PermissionError as e:
        logger.error(str(e))
        sys.exit(3)
    except OSError as e:
        logger.error(str(e))
        sys.exit(3)
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)
