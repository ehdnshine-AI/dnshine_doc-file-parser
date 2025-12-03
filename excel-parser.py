<<<<<<< HEAD
=======

>>>>>>> eaecb7694d4ba2d061beb0d55423ca327910db47
import argparse
import logging
import os
import pathlib
import sys

import pandas as pd
from pytablewriter import MarkdownTableWriter

def excel_sheet_to_markdown(excel_path, sheet_name, md_path):
    """Convert a single Excel sheet to a Markdown file."""
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
    writer = MarkdownTableWriter(dataframe=df, table_name=sheet_name)
    md = writer.dumps()
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

def process_excel_file(excel_path, output_dir, sheet_name=None, logger=None):
    """Process Excel file: convert all or specified sheets to markdown."""
    xls = pd.ExcelFile(excel_path)
    sheets = [sheet_name] if sheet_name else xls.sheet_names

    out_p = pathlib.Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)

    processed = []
    for s in sheets:
        md_name = f"{s}.md"
        md_path = out_p.joinpath(md_name)
        try:
            excel_sheet_to_markdown(excel_path, s, str(md_path))
            processed.append((excel_path, s, str(md_path)))
            if logger:
                logger.info("Converted: %s sheet %s -> %s", excel_path, s, md_path)
            else:
                print(f"Converted: {excel_path} sheet {s} -> {md_path}")
        except Exception as e:
            if logger:
                logger.exception("Failed to convert sheet %s in %s", s, excel_path)
            else:
                print(f"Failed to convert sheet {s} in {excel_path}: {e}", file=sys.stderr)
    return processed

if __name__ == "__main__":
<<<<<<< HEAD

    ap = argparse.ArgumentParser(description="Convert Excel sheets to Markdown files")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-dir", help="Directory with Excel files to convert")
    ap.add_argument("--output-dir", default=None, help="Output directory for markdown files (default: input file's folder or current directory)")
=======
    ap = argparse.ArgumentParser(description="Convert Excel sheets to Markdown files")
    ap.add_argument("--file", required=True, help="Excel file to convert")
    ap.add_argument("--output-dir", default=None, help="Output directory for markdown files (default: input file's folder)")
>>>>>>> eaecb7694d4ba2d061beb0d55423ca327910db47
    ap.add_argument("--sheet", default=None, help="Sheet name to convert (default: all sheets)")
    ap.add_argument("--quiet", action="store_true", help="Minimal output")
    ap.add_argument("--verbose", action="store_true", help="Detailed info logging")

    args = ap.parse_args()

    log_level = logging.WARNING
    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger("excel-parser")

    try:
<<<<<<< HEAD
        p = pathlib.Path(args.input_dir)
        if not p.exists() or not p.is_dir():
            logger.error("Input directory does not exist or is not a directory: %s", args.input_dir)
            sys.exit(2)

        out_dir = args.output_dir or str(pathlib.Path('.').resolve())
        pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)

        files = list(p.glob("*.xls*"))
        if not files:
            logger.warning("No Excel files found in directory: %s", args.input_dir)
        for file in files:
            process_excel_file(str(file), out_dir, args.sheet, logger=logger)
            if not args.quiet:
                logger.info("Processed file: %s", file)
=======
        fpath = pathlib.Path(args.file)
        if not fpath.exists() or not fpath.is_file():
            logger.error("Input file does not exist or is not a file: %s", args.file)
            sys.exit(2)

        out_dir = args.output_dir or str(fpath.parent)
        pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)

        results = process_excel_file(str(fpath), out_dir, args.sheet, logger=logger)
        if not args.quiet:
            logger.info("Processed %d sheets.", len(results))
>>>>>>> eaecb7694d4ba2d061beb0d55423ca327910db47

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)
<<<<<<< HEAD
=======


def excel_to_markdown(
    excel_path: str,
    output_dir: str,
    sheet_name=None,     # None이면 모든 시트
    md_filename_template: str = "{sheet_name}.md",
):
    # 읽기
    xls = pd.ExcelFile(excel_path)
    sheets = [sheet_name] if sheet_name else xls.sheet_names

    os.makedirs(output_dir, exist_ok=True)

    for s in sheets:
        df = pd.read_excel(xls, sheet_name=s, engine="openpyxl")
        # 테이블 출력
        writer = MarkdownTableWriter(
            dataframe=df,
            table_name=s  # optional: 헤더 위에 시트명 출력
        )
        md = writer.dumps()  # string로 md 생성
        out_path = os.path.join(
            output_dir,
            md_filename_template.format(sheet_name=s)
        )
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Wrote sheet {s} → {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Convert Excel sheets to Markdown files")
    ap.add_argument("--file", required=True, help="Excel file to convert")
    ap.add_argument("--output-dir", default=None, help="Output directory for markdown files (default: input file's folder)")
    ap.add_argument("--sheet", default=None, help="Sheet name to convert (default: all sheets)")
    ap.add_argument("--quiet", action="store_true", help="Minimal output")
    ap.add_argument("--verbose", action="store_true", help="Detailed info logging")

    args = ap.parse_args()

    log_level = logging.WARNING
    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger("excel-parser")

    try:
        fpath = pathlib.Path(args.file)
        if not fpath.exists() or not fpath.is_file():
            logger.error("Input file does not exist or is not a file: %s", args.file)
            sys.exit(2)

        out_dir = args.output_dir or str(fpath.parent)
        pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)

        results = process_excel_file(str(fpath), out_dir, args.sheet, logger=logger)
        if not args.quiet:
            logger.info("Processed %d sheets.", len(results))

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)
>>>>>>> eaecb7694d4ba2d061beb0d55423ca327910db47
