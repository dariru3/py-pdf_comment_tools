import argparse
import csv
from pathlib import Path
import sys

import fitz  # type: ignore


COMMENT_AUTHOR = "Highlighter"
DEFAULT_SUMMARY_NAME = "keyword_summary.csv"
DEFAULT_SHAPE_OUTPUT = "shape_annotations.csv"
DEFAULT_HIGHLIGHT_OUTPUT = "highlight_annotations.csv"
COLOR_MAP = {
    "blue": (0.0, 0.0, 1.0),
    "light blue": (0.22, 0.9, 1.0),
    "green": (0.42, 0.85, 0.16),
    "light green": (0.77, 0.98, 0.45),
    "yellow": (1.0, 0.82, 0.0),
    "light yellow": (0.99, 0.96, 0.52),
    "orange": (1.0, 0.44, 0.01),
    "light orange": (1.0, 0.75, 0.62),
    "red": (0.9, 0.13, 0.22),
    "light red": (1.0, 0.5, 0.62),
    "pink": (0.64, 0.19, 0.53),
    "light pink": (0.98, 0.53, 1.0),
}
SHAPE_TYPES = {"square", "circle", "polygon"}


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


def parse_pages(pages_arg: str | None) -> set[int] | None:
    if not pages_arg:
        return None

    selected_pages: set[int] = set()
    for chunk in pages_arg.split(","):
        token = chunk.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start <= 0 or end <= 0 or end < start:
                raise ValueError(f"Invalid page range: {token}")
            selected_pages.update(range(start, end + 1))
            continue

        page_num = int(token)
        if page_num <= 0:
            raise ValueError(f"Invalid page number: {token}")
        selected_pages.add(page_num)

    return selected_pages or None


def ensure_output_dir(output_dir_arg: str | None, fallback: Path) -> Path:
    base_dir = Path(output_dir_arg).expanduser() if output_dir_arg else fallback
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def resolve_pdf_paths(pdf_arg: str | None, input_dir_arg: str | None) -> list[Path]:
    if pdf_arg:
        pdf_path = Path(pdf_arg).expanduser()
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        return [pdf_path]

    input_dir = Path(input_dir_arg or "").expanduser()
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    pdf_paths = sorted(path for path in input_dir.iterdir() if path.suffix.lower() == ".pdf")
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in: {input_dir}")
    return pdf_paths


def load_keywords(csv_path_arg: str) -> list[dict[str, str]]:
    csv_path = Path(csv_path_arg).expanduser()
    if not csv_path.is_file():
        raise FileNotFoundError(f"Keywords CSV not found: {csv_path}")

    rows: list[dict[str, str]] = []
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Keywords CSV must include a header row.")

        normalized_fieldnames = {name.strip().lower(): name for name in reader.fieldnames}
        if "keyword" not in normalized_fieldnames or "comment" not in normalized_fieldnames:
            raise ValueError("Keywords CSV must include 'keyword' and 'comment' columns.")

        for row in reader:
            keyword = (row.get(normalized_fieldnames["keyword"]) or "").strip()
            comment = (row.get(normalized_fieldnames["comment"]) or "").strip()
            color_field = normalized_fieldnames.get("color")
            color = (row.get(color_field) or "").strip() if color_field else ""
            if keyword:
                rows.append({"keyword": keyword, "comment": comment, "color": color})

    if not rows:
        raise ValueError("Keywords CSV did not contain any usable keyword rows.")
    return rows


def iter_annotations(page: fitz.Page):
    annot = page.first_annot
    while annot:
        yield annot
        annot = annot.next


def expand_rect(rect: fitz.Rect, padding: float = 2.0) -> fitz.Rect:
    return fitz.Rect(rect.x0 - padding, rect.y0 - padding, rect.x1 + padding, rect.y1 + padding)


def extract_text_from_rect(page: fitz.Page, rect: fitz.Rect, padding: float = 2.0) -> str:
    return page.get_text("text", clip=expand_rect(rect, padding)).strip()


def format_rect(rect: fitz.Rect) -> str:
    return f"{rect.x0:.2f},{rect.y0:.2f},{rect.x1:.2f},{rect.y1:.2f}"


def default_annotated_pdf_path(pdf_path: Path, output_dir: Path) -> Path:
    return output_dir / f"{pdf_path.stem} Highlighter.pdf"


def write_csv_rows(output_path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def apply_highlight(page: fitz.Page, rect: fitz.Rect, comment: str, color: str) -> None:
    annot = page.add_highlight_annot(rect)
    color_value = COLOR_MAP.get(color.lower())
    if color_value:
        annot.set_colors(stroke=color_value)

    info = annot.info
    info["title"] = COMMENT_AUTHOR
    info["content"] = comment
    annot.set_info(info)
    annot.update(opacity=0.4)


def highlight_keywords(
    pdf_paths: list[Path],
    keywords: list[dict[str, str]],
    pages: set[int] | None,
    output_dir: Path,
    summary_path: Path,
) -> None:
    summary_rows: list[dict[str, object]] = []

    for pdf_path in pdf_paths:
        print(f"Processing {pdf_path}...")
        doc = fitz.open(pdf_path)
        matches_record = {item["keyword"]: 0 for item in keywords}

        for page_index, page in enumerate(doc, start=1):
            if pages and page_index not in pages:
                continue

            print(f"  Scanning page {page_index}...")
            for item in keywords:
                matches = page.search_for(item["keyword"])
                if not matches:
                    continue

                matches_record[item["keyword"]] += len(matches)
                for rect in matches:
                    apply_highlight(page, rect, item["comment"], item["color"])

        output_pdf = default_annotated_pdf_path(pdf_path, output_dir)
        doc.save(output_pdf, garbage=3, deflate=True)
        doc.close()

        for item in keywords:
            summary_rows.append(
                {
                    "keyword": item["keyword"],
                    "count": matches_record[item["keyword"]],
                    "input_file": str(pdf_path),
                    "output_file": str(output_pdf),
                    "comment_author": COMMENT_AUTHOR,
                    "comment": item["comment"],
                    "color": item["color"],
                }
            )

        print(f"Saved annotated PDF to {output_pdf}")

    write_csv_rows(
        summary_path,
        [
            "keyword",
            "count",
            "input_file",
            "output_file",
            "comment_author",
            "comment",
            "color",
        ],
        summary_rows,
    )
    print(f"Saved summary CSV to {summary_path}")


def map_replies_to_parents(page: fitz.Page) -> dict[int, list[str]]:
    reply_map: dict[int, list[str]] = {}
    for annot in iter_annotations(page):
        parent_ref = getattr(annot, "irt", None) or getattr(annot, "in_reply_to", None)
        parent_xref = getattr(parent_ref, "xref", None) if parent_ref else None
        if parent_xref is None:
            parent_xref = getattr(annot, "irt_xref", None)
        if parent_xref is None or parent_xref <= 0:
            continue

        content = (annot.info.get("content") or "").strip()
        author = (annot.info.get("title") or "Unknown").strip()
        if not content:
            continue

        reply_map.setdefault(parent_xref, []).append(f"[{author}]: {content}")
    return reply_map


def extract_shape_comment_rows(pdf_path: Path, pages: set[int] | None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    doc = fitz.open(pdf_path)

    print(f"Processing {pdf_path}...")
    for page_index, page in enumerate(doc, start=1):
        if pages and page_index not in pages:
            continue

        reply_map = map_replies_to_parents(page)
        page_rows = 0

        for annot in iter_annotations(page):
            annot_name = annot.type[1].lower()
            if annot_name not in SHAPE_TYPES:
                continue

            comment_chain: list[str] = []
            parent_content = (annot.info.get("content") or "").strip()
            parent_author = (annot.info.get("title") or "Unknown").strip()
            if parent_content:
                comment_chain.append(f"[{parent_author}]: {parent_content}")
            if annot.xref in reply_map:
                comment_chain.extend(reply_map[annot.xref])
            if not comment_chain:
                continue

            rows.append(
                {
                    "page": page_index,
                    "type": annot.type[1],
                    "author_comment": " | ".join(comment_chain),
                    "target_text": extract_text_from_rect(page, annot.rect),
                    "coordinates": format_rect(annot.rect),
                    "input_file": str(pdf_path),
                }
            )
            page_rows += 1

        if page_rows:
            print(f"  Page {page_index}: found {page_rows} shape annotations with comments")

    doc.close()
    return rows


def extract_highlight_rows(pdf_path: Path, pages: set[int] | None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    doc = fitz.open(pdf_path)

    print(f"Processing {pdf_path}...")
    for page_index, page in enumerate(doc, start=1):
        if pages and page_index not in pages:
            continue

        page_rows = 0
        for annot in iter_annotations(page):
            if annot.type[1].lower() != "highlight":
                continue

            info = annot.info
            rows.append(
                {
                    "page": page_index,
                    "type": annot.type[1],
                    "author": (info.get("title") or "").strip(),
                    "comment": (info.get("content") or "").strip(),
                    "highlighted_text": extract_text_from_rect(page, annot.rect),
                    "coordinates": format_rect(annot.rect),
                    "input_file": str(pdf_path),
                }
            )
            page_rows += 1

        if page_rows:
            print(f"  Page {page_index}: found {page_rows} highlights")

    doc.close()
    return rows


def run_extract_shape_comments(pdf_path: Path, pages: set[int] | None, output_path: Path) -> None:
    rows = extract_shape_comment_rows(pdf_path, pages)
    if not rows:
        print("No shape annotations with comments found; CSV not written.")
        return

    write_csv_rows(
        output_path,
        ["page", "type", "author_comment", "target_text", "coordinates", "input_file"],
        rows,
    )
    print(f"Saved CSV to {output_path}")


def run_extract_highlights(pdf_path: Path, pages: set[int] | None, output_path: Path) -> None:
    rows = extract_highlight_rows(pdf_path, pages)
    if not rows:
        print("No highlight annotations found; CSV not written.")
        return

    write_csv_rows(
        output_path,
        ["page", "type", "author", "comment", "highlighted_text", "coordinates", "input_file"],
        rows,
    )
    print(f"Saved CSV to {output_path}")


def main() -> int:
    try:
        args = parse_args()
        pages = parse_pages(args.pages)

        if args.mode == "highlight-keywords":
            pdf_paths = resolve_pdf_paths(args.pdf, args.input_dir)
            base_dir = Path(args.pdf).expanduser().parent if args.pdf else Path(args.input_dir).expanduser()
            output_dir = ensure_output_dir(args.output_dir, base_dir)
            summary_path = (
                Path(args.output).expanduser()
                if args.output
                else output_dir / DEFAULT_SUMMARY_NAME
            )
            keywords = load_keywords(args.keywords_csv)
            highlight_keywords(pdf_paths, keywords, pages, output_dir, summary_path)
            return 0

        pdf_path = Path(args.pdf).expanduser()
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        output_dir = ensure_output_dir(args.output_dir, pdf_path.parent)
        if args.mode == "extract-shape-comments":
            output_path = (
                Path(args.output).expanduser()
                if args.output
                else output_dir / DEFAULT_SHAPE_OUTPUT
            )
            run_extract_shape_comments(pdf_path, pages, output_path)
            return 0

        output_path = (
            Path(args.output).expanduser()
            if args.output
            else output_dir / DEFAULT_HIGHLIGHT_OUTPUT
        )
        run_extract_highlights(pdf_path, pages, output_path)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
