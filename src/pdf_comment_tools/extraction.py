from pathlib import Path

import fitz  # type: ignore

from pdf_comment_tools.constants import SHAPE_TYPES
from pdf_comment_tools.csv_utils import write_csv_rows
from pdf_comment_tools.pdf_utils import extract_text_from_rect, format_rect, iter_annotations


def map_replies_to_parents(page: fitz.Page) -> dict[int, list[str]]:
    reply_map: dict[int, list[str]] = {}
    for annot in iter_annotations(page):
        parent_ref = getattr(annot, "irt", None) or getattr(annot, "in_reply_to", None)
        if isinstance(parent_ref, int):
            parent_xref = parent_ref
        else:
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


def build_comment_chain(annot: fitz.Annot, reply_map: dict[int, list[str]]) -> str:
    comment_chain: list[str] = []
    parent_content = (annot.info.get("content") or "").strip()
    parent_author = (annot.info.get("title") or "Unknown").strip()
    if parent_content:
        comment_chain.append(f"[{parent_author}]: {parent_content}")
    if annot.xref in reply_map:
        comment_chain.extend(reply_map[annot.xref])
    return " | ".join(comment_chain)


def is_supported_comment_annotation(annot: fitz.Annot) -> bool:
    annot_name = annot.type[1].lower()
    return annot_name == "highlight" or annot_name in SHAPE_TYPES


def extract_comment_rows(pdf_path: Path, pages: set[int] | None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    print(f"Processing {pdf_path}...")
    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc, start=1):
            if pages and page_index not in pages:
                continue

            page_rows = 0
            reply_map = map_replies_to_parents(page)
            for annot in iter_annotations(page):
                if not is_supported_comment_annotation(annot):
                    continue

                comment_chain = build_comment_chain(annot, reply_map)

                rows.append(
                    {
                        "page": page_index,
                        "type": annot.type[1],
                        "author_comment": comment_chain,
                        "target_text": extract_text_from_rect(page, annot.rect),
                        "coordinates": format_rect(annot.rect),
                        "input_file": str(pdf_path),
                    }
                )
                page_rows += 1

            if page_rows:
                print(f"  Page {page_index}: found {page_rows} supported comment annotations")

    return rows


def run_extract_comments(pdf_path: Path, pages: set[int] | None, output_path: Path) -> None:
    rows = extract_comment_rows(pdf_path, pages)
    if not rows:
        print("No supported annotations found; CSV not written.")
        return

    write_csv_rows(
        output_path,
        ["page", "type", "author_comment", "target_text", "coordinates", "input_file"],
        rows,
    )
    print(f"Saved CSV to {output_path}")
