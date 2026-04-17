import csv
from pathlib import Path

import fitz

import main


def _make_sample_pdf(pdf_path: Path) -> None:
    doc = fitz.open()

    page1 = doc.new_page()
    page1.insert_text(
        fitz.Point(72, 72),
        "Alpha keyword is here.\nBeta keyword is also here.",
        fontsize=12,
    )
    alpha_rect = page1.search_for("Alpha keyword")[0]
    highlight = page1.add_highlight_annot(alpha_rect)
    highlight_info = highlight.info
    highlight_info["title"] = "Reviewer One"
    highlight_info["content"] = "Check highlighted keyword."
    highlight.set_info(highlight_info)
    highlight.update()

    page2 = doc.new_page()
    page2.insert_text(
        fitz.Point(72, 72),
        "Shape annotation target text.\nReply chain target.",
        fontsize=12,
    )
    target_rect = page2.search_for("Shape annotation target text.")[0]
    square = page2.add_rect_annot(
        fitz.Rect(target_rect.x0 - 4, target_rect.y0 - 4, target_rect.x1 + 4, target_rect.y1 + 4)
    )
    square_info = square.info
    square_info["title"] = "Reviewer Two"
    square_info["content"] = "Parent shape comment."
    square.set_info(square_info)
    square.update()

    reply = page2.add_text_annot(fitz.Point(target_rect.x1 + 20, target_rect.y0), "reply")
    reply_info = reply.info
    reply_info["title"] = "Reviewer Three"
    reply_info["content"] = "Reply comment."
    reply.set_info(reply_info)
    reply.set_irt_xref(square.xref)
    reply.update()

    doc.save(pdf_path)
    doc.close()


def _make_keywords_csv(csv_path: Path) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["keyword", "comment", "color"])
        writer.writeheader()
        writer.writerow(
            {
                "keyword": "Alpha",
                "comment": "Alpha comment",
                "color": "yellow",
            }
        )
        writer.writerow(
            {
                "keyword": "Beta",
                "comment": "Beta comment",
                "color": "light blue",
            }
        )


def test_extract_highlight_rows_reads_highlight_comment(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_sample_pdf(pdf_path)

    rows = main.extract_highlight_rows(pdf_path, pages=None)

    assert len(rows) == 1
    assert rows[0]["page"] == 1
    assert rows[0]["author"] == "Reviewer One"
    assert rows[0]["comment"] == "Check highlighted keyword."
    assert "Alpha keyword" in str(rows[0]["highlighted_text"])


def test_extract_shape_comment_rows_includes_reply_chain(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_sample_pdf(pdf_path)

    rows = main.extract_shape_comment_rows(pdf_path, pages=None)

    assert len(rows) == 1
    assert rows[0]["page"] == 2
    assert rows[0]["type"] == "Square"
    assert "[Reviewer Two]: Parent shape comment." in str(rows[0]["author_comment"])
    assert "[Reviewer Three]: Reply comment." in str(rows[0]["author_comment"])
    assert "Shape annotation target text." in str(rows[0]["target_text"])


def test_highlight_keywords_writes_summary_and_output_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    csv_path = tmp_path / "keywords.csv"
    output_dir = tmp_path / "out"
    summary_path = tmp_path / "summary.csv"
    _make_sample_pdf(pdf_path)
    _make_keywords_csv(csv_path)

    main.highlight_keywords(
        pdf_paths=[pdf_path],
        keywords=main.load_keywords(str(csv_path)),
        pages=None,
        output_dir=output_dir,
        summary_path=summary_path,
    )

    output_pdf = output_dir / "sample Highlighter.pdf"
    assert output_pdf.exists()
    assert summary_path.exists()

    with summary_path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert rows[0]["keyword"] == "Alpha"
    assert rows[0]["count"] == "1"
    assert rows[0]["comment_author"] == main.COMMENT_AUTHOR
    assert rows[1]["keyword"] == "Beta"
    assert rows[1]["count"] == "1"


def test_parse_pages_supports_single_values_and_ranges() -> None:
    assert main.parse_pages("1,3-4,7") == {1, 3, 4, 7}
