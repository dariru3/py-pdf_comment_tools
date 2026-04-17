import csv
from pathlib import Path


def load_keywords(csv_path_arg: str) -> list[dict[str, str]]:
    csv_path = Path(csv_path_arg).expanduser()
    if not csv_path.is_file():
        raise FileNotFoundError(f"Keywords CSV not found: {csv_path}")

    rows: list[dict[str, str]] = []
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Keywords CSV must include a header row.")

        normalized_fieldnames = {name.strip().lower(): name for name in reader.fieldnames}
        if "keyword" not in normalized_fieldnames or "comment" not in normalized_fieldnames:
            raise ValueError("Keywords CSV must include 'keyword' and 'comment' columns.")

        for row in reader:
            keyword = (row.get(normalized_fieldnames["keyword"]) or "").strip()
            comment = (row.get(normalized_fieldnames["comment"]) or "").strip()
            color_field = normalized_fieldnames.get("color")
            color = (row.get(color_field) or "").strip() if color_field else ""
            if keyword:
                rows.append({"keyword": keyword, "comment": comment, "color": color})

    if not rows:
        raise ValueError("Keywords CSV did not contain any usable keyword rows.")
    return rows


def write_csv_rows(output_path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
