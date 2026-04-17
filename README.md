# Unified PDF Comment Tools

This repo is organized around a single PDF comment tool with a thin top-level CLI wrapper and a shared internal package.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
```

## Repo Layout

- `main.py`: compatibility entrypoint for local CLI use
- `src/pdf_comment_tools/`: active implementation modules
- `tests/`: pytest coverage for the active tool

## Modes

### 1. Highlight keywords and add comments

Use a CSV with `keyword`, `comment`, and optional `color` columns.

```bash
python main.py --mode highlight-keywords --pdf /path/to/file.pdf --keywords-csv keywords.csv
python main.py --mode highlight-keywords --input-dir /path/to/pdfs --keywords-csv keywords.csv --output-dir ./out
```

Default outputs:

- Annotated PDFs with the suffix ` Highlighter.pdf`
- Summary CSV named `keyword_summary.csv`

### 2. Extract comments from shape annotations

Extract square / circle / polygon comments and the text under the annotated area.

```bash
python main.py --mode extract-shape-comments --pdf /path/to/file.pdf
```

Default output: `shape_annotations.csv`

### 3. Extract highlight annotations

Extract highlight annotation metadata and the text inside the highlighted region.

```bash
python main.py --mode extract-highlights --pdf /path/to/file.pdf
```

Default output: `highlight_annotations.csv`

## Common options

- `--pages 1,3-5` to limit processing to selected pages
- `--output-dir /path/to/out` to redirect default output files
- `--output /path/to/file.csv` to override the CSV output path

## Tests

```bash
./.venv/bin/python -m pytest -q
```

## Notes

- Active development belongs in `src/pdf_comment_tools/`.
- `main.py` remains the stable local runner and compatibility wrapper.
- The merged CLI uses PyMuPDF for all modes.
