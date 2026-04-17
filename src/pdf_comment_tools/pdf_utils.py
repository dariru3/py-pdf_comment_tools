from pathlib import Path

import fitz  # type: ignore


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
