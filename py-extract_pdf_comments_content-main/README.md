# PDF Annotation Extractor

Extract comments from shape annotations (square/circle/polygon) in a PDF and capture the text under each annotated area. Outputs a CSV with `page`, `type`, `[author] comment`, and `target data`.

## Setup

- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`

## Usage

- Provide the PDF path via CLI arg or env var:
  - `source .venv/bin/activate && python main.py /path/to/file.pdf`
  - or `source .venv/bin/activate && PDF_PATH=/path/to/file.pdf python main.py`
- Output CSV: `annotations.csv`

## Notes

- `.env` is ignored; you can set `PDF_PATH` there if you prefer.
- `.csv`, `.pdf`, and the virtual environment directory are git-ignored.
