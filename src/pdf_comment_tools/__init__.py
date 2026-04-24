from pdf_comment_tools.cli import main, parse_args, validate_args
from pdf_comment_tools.constants import (
    COLOR_MAP,
    COMMENT_AUTHOR,
    DEFAULT_COMMENTS_OUTPUT,
    DEFAULT_SUMMARY_NAME,
    SHAPE_TYPES,
)
from pdf_comment_tools.csv_utils import load_keywords
from pdf_comment_tools.extraction import (
    extract_comment_rows,
    map_replies_to_parents,
    run_extract_comments,
)
from pdf_comment_tools.highlighting import highlight_keywords
from pdf_comment_tools.pdf_utils import (
    default_annotated_pdf_path,
    ensure_output_dir,
    expand_rect,
    extract_text_from_highlight,
    extract_text_from_rect,
    format_rect,
    highlight_quad_rects,
    iter_annotations,
    parse_pages,
    resolve_pdf_paths,
)

__all__ = [
    "COLOR_MAP",
    "COMMENT_AUTHOR",
    "DEFAULT_COMMENTS_OUTPUT",
    "DEFAULT_SUMMARY_NAME",
    "SHAPE_TYPES",
    "default_annotated_pdf_path",
    "ensure_output_dir",
    "expand_rect",
    "extract_text_from_highlight",
    "extract_comment_rows",
    "extract_text_from_rect",
    "format_rect",
    "highlight_keywords",
    "highlight_quad_rects",
    "iter_annotations",
    "load_keywords",
    "main",
    "map_replies_to_parents",
    "parse_args",
    "parse_pages",
    "resolve_pdf_paths",
    "run_extract_comments",
    "validate_args",
]
