# Legacy Source Archive

This directory contains the three imported script repositories that were used to build the unified top-level tool.

They are retained temporarily as historical reference while active development continues in:

- `main.py` as the compatibility entrypoint
- `src/pdf_comment_tools/` as the active implementation

Do not add new product logic to the archived directories. If a legacy script still contains useful behavior, migrate the relevant code into the package modules and then remove the duplicated legacy implementation.
