from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pdf_comment_tools import (  # noqa: E402
    COLOR_MAP,
    COMMENT_AUTHOR,
    DEFAULT_HIGHLIGHT_OUTPUT,
    DEFAULT_SHAPE_OUTPUT,
    DEFAULT_SUMMARY_NAME,
    SHAPE_TYPES,
    default_annotated_pdf_path,
    ensure_output_dir,
    expand_rect,
    extract_highlight_rows,
    extract_shape_comment_rows,
    extract_text_from_rect,
    format_rect,
    highlight_keywords,
    iter_annotations,
    load_keywords,
    main,
    map_replies_to_parents,
    parse_args,
    parse_pages,
    resolve_pdf_paths,
    run_extract_highlights,
    run_extract_shape_comments,
    validate_args,
)


if __name__ == "__main__":
    raise SystemExit(main())
