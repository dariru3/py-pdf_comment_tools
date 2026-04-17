# Repository Guidelines

## Project Structure & Module Organization
`main.py` is the active entrypoint for the merged PDF comment tool. It contains the CLI and shared logic for:
- `highlight-keywords`
- `extract-shape-comments`
- `extract-highlights`

`tests/test_main.py` contains the automated pytest suite. `tests/fixtures/` holds small reusable test assets such as `test_keywords.csv`; PDF fixtures are ignored by Git. The three imported directories (`py-extract_PDF_highlights-main/`, `py-extract_pdf_comments_content-main/`, and `py-pdf_highlight_comment-main/`) are reference sources and should not receive new primary logic unless the task is explicitly sub-repo cleanup.

## Build, Test, and Development Commands
Create an isolated environment before working:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
```

Key commands:

```bash
python main.py --help
./.venv/bin/python -m pytest -q
python3 -m py_compile main.py tests/test_main.py
```

Use the first to inspect CLI modes, the second to run the full test suite, and the third for a quick syntax check.

## Coding Style & Naming Conventions
Use 4-space indentation and keep code Pythonic and minimal. Prefer small helper functions over duplicated inline logic. Use `snake_case` for functions, variables, and test names. Keep new CLI behavior in `main.py` unless the repo is explicitly being refactored into modules. Follow the existing style: standard library imports first, then third-party imports, and concise comments only where behavior is non-obvious.

## Testing Guidelines
Tests use `pytest`. Add or update tests for every behavioral change in the merged CLI, especially around annotation extraction, reply chains, output paths, and CSV generation. Name tests `test_<behavior>()`. Prefer self-contained temporary fixtures created inside tests over committed PDFs.

## Commit & Pull Request Guidelines
Recent history favors short, imperative commit messages such as `Add pytest coverage for merged PDF tools` and `Restore output directory creation for highlights`. Keep commits focused and avoid mixing refactors with behavior changes. PRs should include:
- a brief summary of what changed
- validation commands run
- any follow-up work, especially sub-repo deduplication or cleanup

If a change affects outputs, mention the impacted CLI mode explicitly.
