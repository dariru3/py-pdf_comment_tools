import argparse
from pathlib import Path
import sys

from pdf_comment_tools.constants import (
    DEFAULT_HIGHLIGHT_OUTPUT,
    DEFAULT_SHAPE_OUTPUT,
    DEFAULT_SUMMARY_NAME,
)
from pdf_comment_tools.csv_utils import load_keywords
from pdf_comment_tools.extraction import (
    extract_highlight_rows,
    extract_shape_comment_rows,
    map_replies_to_parents,
    run_extract_highlights,
    run_extract_shape_comments,
)
from pdf_comment_tools.highlighting import highlight_keywords
from pdf_comment_tools.pdf_utils import (
    default_annotated_pdf_path,
    ensure_output_dir,
    expand_rect,
    extract_text_from_rect,
    format_rect,
    iter_annotations,
    parse_pages,
    resolve_pdf_paths,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Unified PDF comment tool with highlight and extraction modes."
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=("highlight-keywords", "extract-shape-comments", "extract-highlights"),
        help="Which tool mode to run.",
    )
    parser.add_argument("--pdf", help="Path to a single PDF file.")
    parser.add_argument("--input-dir", help="Directory of PDFs for batch highlighting.")
    parser.add_argument(
        "--keywords-csv",
        help="CSV with columns keyword, comment, and optional color. Required in highlight mode.",
    )
    parser.add_argument(
        "--output",
        help="Explicit CSV output path for extraction modes or summary CSV for highlight mode.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for annotated PDFs and default CSV outputs. Defaults to the input file directory or current directory.",
    )
    parser.add_argument(
        "--pages",
        help="Optional page selection, e.g. 1,3-5,9.",
    )

    args = parser.parse_args()
    validate_args(parser, args)
    return args


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.mode == "highlight-keywords":
        if not args.keywords_csv:
            parser.error("--keywords-csv is required for highlight-keywords mode.")
        if not args.pdf and not args.input_dir:
            parser.error("highlight-keywords mode requires --pdf or --input-dir.")
        if args.pdf and args.input_dir:
            parser.error("Use either --pdf or --input-dir, not both.")
        return

    if not args.pdf:
        parser.error(f"{args.mode} mode requires --pdf.")
    if args.input_dir:
        parser.error(f"{args.mode} mode does not support --input-dir.")
    if args.keywords_csv:
        parser.error(f"{args.mode} mode does not use --keywords-csv.")


def main() -> int:
    try:
        args = parse_args()
        pages = parse_pages(args.pages)

        if args.mode == "highlight-keywords":
            pdf_paths = resolve_pdf_paths(args.pdf, args.input_dir)
            base_dir = Path(args.pdf).expanduser().parent if args.pdf else Path(args.input_dir).expanduser()
            output_dir = ensure_output_dir(args.output_dir, base_dir)
            summary_path = Path(args.output).expanduser() if args.output else output_dir / DEFAULT_SUMMARY_NAME
            keywords = load_keywords(args.keywords_csv)
            highlight_keywords(pdf_paths, keywords, pages, output_dir, summary_path)
            return 0

        pdf_path = Path(args.pdf).expanduser()
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        output_dir = ensure_output_dir(args.output_dir, pdf_path.parent)
        if args.mode == "extract-shape-comments":
            output_path = Path(args.output).expanduser() if args.output else output_dir / DEFAULT_SHAPE_OUTPUT
            run_extract_shape_comments(pdf_path, pages, output_path)
            return 0

        output_path = Path(args.output).expanduser() if args.output else output_dir / DEFAULT_HIGHLIGHT_OUTPUT
        run_extract_highlights(pdf_path, pages, output_path)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


__all__ = [
    "default_annotated_pdf_path",
    "ensure_output_dir",
    "expand_rect",
    "extract_highlight_rows",
    "extract_shape_comment_rows",
    "extract_text_from_rect",
    "format_rect",
    "highlight_keywords",
    "iter_annotations",
    "load_keywords",
    "main",
    "map_replies_to_parents",
    "parse_args",
    "parse_pages",
    "resolve_pdf_paths",
    "run_extract_highlights",
    "run_extract_shape_comments",
    "validate_args",
]
