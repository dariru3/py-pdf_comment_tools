import csv
import os
import sys

import fitz  # type: ignore

STRINGS = {
    "author_key": "[author] comment",
    "target_key": "target data",
    "shape_type": "Shape Annotation",
    "csv_path": "annotations.csv",
    "labels": {"comment_chain": "Comment Chain :", "referred_data": "Referred Data :"},
    "messages": {
        "no_annotations": "No annotations found; CSV not written.",
        "saved_csv": "Saved CSV to {path}",
        "processing": "--- Processing File: {pdf} ---\n",
        "page_found": "--- Page {page} Found {count} annotated areas ---",
    },
}

CSV_HEADERS = ["page", "type", STRINGS["author_key"], STRINGS["target_key"]]


def get_annotations(page):
    """Generator to iterate over all annotations on a page."""
    annot = page.first_annot
    while annot:
        yield annot
        annot = annot.next


def map_replies_to_parents(page):
    """
    Scans a page for 'Reply' annotations and maps them to their parent's IRT (In Reply To) xref.
    Returns a dictionary: { parent_xref: [list_of_reply_contents] }
    """
    reply_map = {}

    for annot in get_annotations(page):
        # irt was renamed to in_reply_to in newer PyMuPDF versions; handle both
        parent_ref = getattr(annot, "irt", None) or getattr(annot, "in_reply_to", None)

        # Check if this annotation is a reply (has a parent reference)
        if parent_ref:
            parent_xref = getattr(parent_ref, "xref", None)
            if parent_xref is None:
                continue

            content = annot.info.get("content") or ""
            author = annot.info.get("title") or "Unknown"

            if parent_xref not in reply_map:
                reply_map[parent_xref] = []

            # Format the reply for readability
            if content.strip():
                reply_map[parent_xref].append(f"[{author}]: {content}")

    return reply_map


def extract_text_from_rect(page, rect, padding=2):
    """
    Extracts text strictly inside a given rectangle.
    Padding adds a small margin to capture edge characters.
    """
    # Create a slightly larger rect to ensure we catch text right on the border
    clip_rect = rect + (-padding, -padding, padding, padding)

    # "text" mode gives plain text. You can change to "dict" or "blocks" for layout analysis.
    return page.get_text("text", clip=clip_rect).strip()


def process_page(page, page_num):
    """
    Processes a single page: finds shapes, links comments/replies, and extracts underlying data.
    Returns a list of result dictionaries.
    """
    results = []

    # 1. Build the map of replies for this page
    reply_map = map_replies_to_parents(page)

    # 2. Iterate through annotations to find the "Parent" shapes
    for annot in get_annotations(page):
        # Filter for shapes: 4 (Square), 5 (Circle), 8 (Polygon)
        # You can add others if needed (e.g., Highlight is 8)
        if annot.type[0] in (4, 5, 8):
            # --- Get Comment Data ---
            parent_content = annot.info.get("content") or ""
            parent_author = annot.info.get("title") or "Unknown"

            # Combine parent comment with any replies found in the map
            comment_chain = []

            # Add parent comment if it exists
            if parent_content.strip():
                comment_chain.append(f"[{parent_author}]: {parent_content}")

            # Add replies associated with this annotation's xref
            if annot.xref in reply_map:
                comment_chain.extend(reply_map[annot.xref])

            # Join them into a single string
            full_comment_text = " | ".join(comment_chain)

            # --- Get Underlying Data ---
            # Only proceed if there is actually a comment or reply attached to this shape
            if full_comment_text:
                data_inside = extract_text_from_rect(page, annot.rect)

                entry = {
                    "page": page_num,
                    "type": STRINGS["shape_type"],
                    "coordinates": tuple(annot.rect),
                    STRINGS["author_key"]: full_comment_text,
                    STRINGS["target_key"]: data_inside,
                }
                results.append(entry)

    return results


def extract_comments_and_data(pdf_path):
    """
    Main entry point. Opens PDF and aggregates results from all pages.
    """
    try:
        doc = fitz.open(pdf_path)
        all_extractions = []

        print(STRINGS["messages"]["processing"].format(pdf=pdf_path))

        for i, page in enumerate(doc):
            page_results = process_page(page, page_num=i + 1)

            if page_results:
                print(
                    STRINGS["messages"]["page_found"].format(
                        page=i + 1, count=len(page_results)
                    )
                )
                for item in page_results:
                    print(
                        f"{STRINGS['labels']['comment_chain']} {item[STRINGS['author_key']]}"
                    )
                    print(
                        f"{STRINGS['labels']['referred_data']} {item[STRINGS['target_key']]}"
                    )
                    print("-" * 40)

                all_extractions.extend(page_results)

        return all_extractions

    except Exception as e:
        print(f"Error processing PDF: {e}")
        return []


def write_csv(results, output_path):
    """Persist extracted data to CSV."""
    if not results:
        print(STRINGS["messages"]["no_annotations"])
        return

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(CSV_HEADERS)
        for item in results:
            writer.writerow(
                [
                    item.get("page"),
                    item.get("type"),
                    item.get(STRINGS["author_key"], ""),
                    item.get(STRINGS["target_key"], ""),
                ]
            )
    print(STRINGS["messages"]["saved_csv"].format(path=output_path))


def resolve_pdf_path():
    """Get PDF path from CLI arg or PDF_PATH env."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.getenv("PDF_PATH")


if __name__ == "__main__":
    file_path = resolve_pdf_path()
    if not file_path:
        raise SystemExit("Provide PDF path via CLI arg or PDF_PATH env.")
    data = extract_comments_and_data(file_path)
    write_csv(data, STRINGS["csv_path"])
