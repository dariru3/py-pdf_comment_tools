import csv
from pathlib import Path
import subprocess
import sys

import fitz

import pdf_comment_tools as tool


def _make_sample_pdf(pdf_path: Path) -> None:
    with fitz.open() as doc:
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

        highlight_reply = page1.add_text_annot(fitz.Point(alpha_rect.x1 + 20, alpha_rect.y0), "reply")
        highlight_reply_info = highlight_reply.info
        highlight_reply_info["title"] = "Reviewer Four"
        highlight_reply_info["content"] = "Highlight reply comment."
        highlight_reply.set_info(highlight_reply_info)
        highlight_reply.set_irt_xref(highlight.xref)
        highlight_reply.update()

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


def test_extract_comment_rows_includes_highlight_reply_chain(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_sample_pdf(pdf_path)

    rows = tool.extract_comment_rows(pdf_path, pages=None)
    highlight_rows = [row for row in rows if row["type"] == "Highlight"]

    assert len(highlight_rows) == 1
    assert highlight_rows[0]["page"] == 1
    assert "[Reviewer One]: Check highlighted keyword." in str(highlight_rows[0]["author_comment"])
    assert "[Reviewer Four]: Highlight reply comment." in str(highlight_rows[0]["author_comment"])
    assert "Alpha keyword" in str(highlight_rows[0]["target_text"])


def test_extract_comment_rows_includes_shape_reply_chain(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_sample_pdf(pdf_path)

    rows = tool.extract_comment_rows(pdf_path, pages=None)
    shape_rows = [row for row in rows if row["type"] == "Square"]

    assert len(shape_rows) == 1
    assert shape_rows[0]["page"] == 2
    assert shape_rows[0]["type"] == "Square"
    assert "[Reviewer Two]: Parent shape comment." in str(shape_rows[0]["author_comment"])
    assert "[Reviewer Three]: Reply comment." in str(shape_rows[0]["author_comment"])
    assert "Shape annotation target text." in str(shape_rows[0]["target_text"])


def test_highlight_keywords_writes_summary_and_output_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    csv_path = tmp_path / "keywords.csv"
    output_dir = tmp_path / "out"
    summary_path = tmp_path / "summary.csv"
    _make_sample_pdf(pdf_path)
    _make_keywords_csv(csv_path)

    tool.highlight_keywords(
        pdf_paths=[pdf_path],
        keywords=tool.load_keywords(str(csv_path)),
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
    assert rows[0]["comment_author"] == tool.COMMENT_AUTHOR
    assert rows[1]["keyword"] == "Beta"
    assert rows[1]["count"] == "1"


def test_parse_pages_supports_single_values_and_ranges() -> None:
    assert tool.parse_pages("1,3-4,7") == {1, 3, 4, 7}


def test_main_wrapper_shows_cli_help() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Unified PDF comment tool" in result.stdout


def test_combined_extract_mode_is_exposed_in_help() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "extract-comments" in result.stdout
    assert "extract-highlights" not in result.stdout
    assert "extract-shape-comments" not in result.stdout


def test_annotated_fixture_includes_highlight_reply_chain() -> None:
    fixture_pdf = Path(__file__).resolve().parent / "fixtures" / "TEST PDF annotated.pdf"

    rows = tool.extract_comment_rows(fixture_pdf, pages=None)
    highlight_rows = [row for row in rows if row["type"] == "Highlight"]

    assert len(highlight_rows) == 4
    threaded_rows = [
        row
        for row in highlight_rows
        if "[Threaded Reviewer]: Parent highlight comment for reply-chain testing." in str(row["author_comment"])
    ]

    assert len(threaded_rows) == 1
    assert "[Threaded Reply Reviewer]: Reply on highlight annotation for combined extraction testing." in str(
        threaded_rows[0]["author_comment"]
    )
    assert "NITRO™" in str(threaded_rows[0]["target_text"])
