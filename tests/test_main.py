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
            "Alpha keyword is here.\nBeta keyword is also here.\nGamma highlight no comment.",
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

        gamma_rect = page1.search_for("Gamma highlight no comment.")[0]
        gamma_highlight = page1.add_highlight_annot(gamma_rect)
        gamma_highlight.update()

        page2 = doc.new_page()
        page2.insert_text(
            fitz.Point(72, 72),
            "Shape annotation target text.\nReply chain target.\nShape without comment target.",
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

        no_comment_rect = page2.search_for("Shape without comment target.")[0]
        no_comment_square = page2.add_rect_annot(
            fitz.Rect(
                no_comment_rect.x0 - 4,
                no_comment_rect.y0 - 4,
                no_comment_rect.x1 + 4,
                no_comment_rect.y1 + 4,
            )
        )
        no_comment_square.update()

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


def _make_bleed_pdf(pdf_path: Path) -> None:
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text(
            fitz.Point(72, 72),
            "Alpha A\nGamma",
            fontsize=12,
        )
        doc.save(pdf_path)


def _make_annotated_fixture_pdf(pdf_path: Path) -> None:
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text(
            fitz.Point(72, 72),
            "NITRO release note.\nSecondary highlighted phrase.\nThird highlighted phrase.\nFourth highlighted phrase.",
            fontsize=12,
        )

        nitro_rect = page.search_for("NITRO")[0]
        threaded_highlight = page.add_highlight_annot(nitro_rect)
        threaded_info = threaded_highlight.info
        threaded_info["title"] = "Threaded Reviewer"
        threaded_info["content"] = "Parent highlight comment for reply-chain testing."
        threaded_highlight.set_info(threaded_info)
        threaded_highlight.update()

        threaded_reply = page.add_text_annot(fitz.Point(nitro_rect.x1 + 20, nitro_rect.y0), "reply")
        threaded_reply_info = threaded_reply.info
        threaded_reply_info["title"] = "Threaded Reply Reviewer"
        threaded_reply_info["content"] = "Reply on highlight annotation for combined extraction testing."
        threaded_reply.set_info(threaded_reply_info)
        threaded_reply.set_irt_xref(threaded_highlight.xref)
        threaded_reply.update()

        for phrase in (
            "Secondary highlighted phrase.",
            "Third highlighted phrase.",
            "Fourth highlighted phrase.",
        ):
            highlight = page.add_highlight_annot(page.search_for(phrase)[0])
            highlight.update()

        doc.save(pdf_path)


def test_extract_comment_rows_includes_highlight_reply_chain(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_sample_pdf(pdf_path)

    rows = tool.extract_comment_rows(pdf_path, pages=None)
    highlight_rows = [row for row in rows if row["type"] == "Highlight"]

    assert len(highlight_rows) == 2
    threaded_rows = [row for row in highlight_rows if "[Reviewer One]: Check highlighted keyword." in str(row["author_comment"])]

    assert len(threaded_rows) == 1
    assert threaded_rows[0]["page"] == 1
    assert "[Reviewer Four]: Highlight reply comment." in str(threaded_rows[0]["author_comment"])
    assert "Alpha keyword" in str(threaded_rows[0]["target_text"])


def test_extract_comment_rows_keeps_highlight_without_comment_chain(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_sample_pdf(pdf_path)

    rows = tool.extract_comment_rows(pdf_path, pages=None)
    plain_highlights = [
        row for row in rows if row["type"] == "Highlight" and "Gamma highlight no comment." in str(row["target_text"])
    ]

    assert len(plain_highlights) == 1
    assert plain_highlights[0]["author_comment"] == ""


def test_extract_comment_rows_includes_shape_reply_chain(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_sample_pdf(pdf_path)

    rows = tool.extract_comment_rows(pdf_path, pages=None)
    shape_rows = [row for row in rows if row["type"] == "Square"]

    assert len(shape_rows) == 2
    threaded_rows = [row for row in shape_rows if "[Reviewer Two]: Parent shape comment." in str(row["author_comment"])]

    assert len(threaded_rows) == 1
    assert threaded_rows[0]["page"] == 2
    assert threaded_rows[0]["type"] == "Square"
    assert "[Reviewer Three]: Reply comment." in str(threaded_rows[0]["author_comment"])
    assert "Shape annotation target text." in str(threaded_rows[0]["target_text"])


def test_extract_comment_rows_keeps_shape_without_comment_chain(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _make_sample_pdf(pdf_path)

    rows = tool.extract_comment_rows(pdf_path, pages=None)
    plain_shapes = [
        row for row in rows if row["type"] == "Square" and "Shape without comment target." in str(row["target_text"])
    ]

    assert len(plain_shapes) == 1
    assert plain_shapes[0]["author_comment"] == ""


def test_extract_comment_rows_preserves_tight_highlight_bounds(tmp_path: Path) -> None:
    pdf_path = tmp_path / "bleed.pdf"
    csv_path = tmp_path / "keywords.csv"
    output_dir = tmp_path / "out"
    summary_path = tmp_path / "summary.csv"
    _make_bleed_pdf(pdf_path)

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["keyword", "comment", "color"])
        writer.writeheader()
        writer.writerow({"keyword": "Alpha", "comment": "Alpha comment", "color": "yellow"})

    tool.highlight_keywords(
        pdf_paths=[pdf_path],
        keywords=tool.load_keywords(str(csv_path)),
        pages=None,
        output_dir=output_dir,
        summary_path=summary_path,
    )

    extracted_rows = tool.extract_comment_rows(output_dir / "bleed Highlighter.pdf", pages=None)
    highlight_rows = [row for row in extracted_rows if row["type"] == "Highlight"]

    assert len(highlight_rows) == 1
    assert highlight_rows[0]["target_text"] == "Alpha"


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


def test_run_extract_comments_returns_rows_and_writes_csv_once(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    output_csv = tmp_path / "annotation_comments.csv"
    _make_sample_pdf(pdf_path)

    rows = tool.run_extract_comments(pdf_path, pages=None, output_path=output_csv)

    assert output_csv.exists()
    assert len(rows) == 4

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        written_rows = list(csv.DictReader(handle))

    assert len(written_rows) == len(rows)


def test_run_extract_comments_skips_csv_when_no_supported_annotations(tmp_path: Path) -> None:
    pdf_path = tmp_path / "plain.pdf"
    output_csv = tmp_path / "annotation_comments.csv"

    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text(fitz.Point(72, 72), "Plain text without annotations.", fontsize=12)
        doc.save(pdf_path)

    rows = tool.run_extract_comments(pdf_path, pages=None, output_path=output_csv)

    assert rows == []
    assert not output_csv.exists()


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


def test_annotated_fixture_includes_highlight_reply_chain(tmp_path: Path) -> None:
    fixture_pdf = tmp_path / "annotated.pdf"
    _make_annotated_fixture_pdf(fixture_pdf)

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
    assert "NITRO" in str(threaded_rows[0]["target_text"])
