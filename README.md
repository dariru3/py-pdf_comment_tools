# Unified PDF Comment Tools

This repo is organized around a single PDF comment tool with a thin top-level CLI wrapper and a shared internal package.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
```

You can also install the package directly:

```bash
pip install -e .
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

Extract supported annotation comments in one mode:

- square / circle / polygon comments
- highlight comments
- reply chains on both shapes and highlights

```bash
python main.py --mode extract-comments --pdf /path/to/file.pdf
```

Default output: `annotation_comments.csv`

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

## Google Colab

For a shareable Colab workflow, use the notebook in
[`notebooks/py_pdf_comment_tools_colab.ipynb`](notebooks/py_pdf_comment_tools_colab.ipynb).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dariru3/py-pdf_comment_tools/blob/main/notebooks/py_pdf_comment_tools_colab.ipynb)

The notebook is optimized for a single PDF at a time and supports:

- uploading one PDF and one keywords CSV for `highlight-keywords`
- uploading one annotated PDF for `extract-comments`
- downloading the generated output files directly from Colab

The Colab notebook installs the repo from GitHub and uses the package API directly rather than shelling through `main.py`.
