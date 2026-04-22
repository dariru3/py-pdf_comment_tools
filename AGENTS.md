# Repository Guidelines

## Project Structure & Module Organization
`main.py` is the compatibility entrypoint for the merged PDF comment tool. Active implementation now lives in `src/pdf_comment_tools/`, with the merged CLI supporting:
- `highlight-keywords`
- `extract-comments`

`tests/test_main.py` contains the automated pytest suite. Keep tests centered on temporary, test-generated inputs and outputs rather than committed PDF or CSV fixtures. Do not add committed test PDFs, keywords CSVs, or generated outputs.

## Build, Test, and Development Commands
Create an isolated environment before working:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Key commands:

```bash
python main.py --help
./.venv/bin/python -m pytest -q
python3 -m py_compile main.py tests/test_main.py
```

Use the first to inspect the current CLI modes, the second to run the full test suite, and the third for a quick syntax check.

## Coding Style & Naming Conventions
Use 4-space indentation and keep code Pythonic and minimal. Prefer small helper functions over duplicated inline logic. Use `snake_case` for functions, variables, and test names. Put new implementation work in `src/pdf_comment_tools/`; keep `main.py` thin. Follow the existing style: standard library imports first, then third-party imports, and concise comments only where behavior is non-obvious.

## Testing Guidelines
Tests use `pytest`. Add or update tests for every behavioral change in the merged CLI, especially around annotation extraction, reply chains, output paths, CSV generation, and wrapper-to-package integration. Name tests `test_<behavior>()`. New tests should create their own temporary PDFs, keywords CSVs, and output files inside the test run instead of adding committed fixtures.

## Commit & Pull Request Guidelines
Recent history favors short, imperative commit messages such as `Add pytest coverage for merged PDF tools` and `Restore output directory creation for highlights`. Keep commits focused and avoid mixing refactors with behavior changes. PRs should include:
- a brief summary of what changed
- validation commands run
- any follow-up work that remains after the change

If a change affects outputs, mention the impacted CLI mode explicitly.
