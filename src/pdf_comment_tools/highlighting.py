from pathlib import Path

import fitz  # type: ignore

from pdf_comment_tools.constants import COLOR_MAP, COMMENT_AUTHOR
from pdf_comment_tools.csv_utils import write_csv_rows
from pdf_comment_tools.pdf_utils import default_annotated_pdf_path


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
    output_dir.mkdir(parents=True, exist_ok=True)
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
