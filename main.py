from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pdf_comment_tools as _pdf_comment_tools  # noqa: E402

main = _pdf_comment_tools.main
__all__ = _pdf_comment_tools.__all__


def __getattr__(name: str):
    return getattr(_pdf_comment_tools, name)


if __name__ == "__main__":
    raise SystemExit(main())
