#!/usr/bin/env python3
"""Validate and merge verified deep-read batches for lessons 218-365."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "content" / "deep_read_218_365.json"
MINIMUMS = {
    "original": 80,
    "translation": 100,
    "person": 160,
    "analysis": 100,
    "work": 50,
    "eq": 45,
    "study": 45,
}
REQUIRED_TEXT = (
    "era",
    "vol",
    "dynasty",
    "person_name",
    "quote",
    "quote_note",
    "next_title",
    "next",
)


def load_rows(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain a JSON array")
    return rows


def validate_rows(rows: list[dict]) -> None:
    seen: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each deep-read entry must be an object")
        number = row.get("number")
        if not isinstance(number, int) or not 218 <= number <= 365:
            raise ValueError(f"invalid lesson number: {number}")
        if number in seen:
            raise ValueError(f"duplicate lesson number: {number}")
        seen.add(number)
        for field in REQUIRED_TEXT:
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"lesson {number} missing {field}")
        for field, minimum in MINIMUMS.items():
            value = row.get(field)
            if not isinstance(value, str) or len(value) < minimum:
                length = len(value) if isinstance(value, str) else 0
                raise ValueError(
                    f"lesson {number} {field} length {length} is below {minimum}"
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--merge", type=Path)
    args = parser.parse_args()
    existing = load_rows(TARGET)
    validate_rows(existing)
    if args.merge:
        incoming = load_rows(args.merge)
        validate_rows(incoming)
        by_number = {row["number"]: row for row in existing}
        overlap = sorted(set(by_number) & {row["number"] for row in incoming})
        if overlap:
            raise ValueError(f"batch overlaps existing lessons: {overlap}")
        by_number.update({row["number"]: row for row in incoming})
        merged = [by_number[number] for number in sorted(by_number)]
        validate_rows(merged)
        temporary = TARGET.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(TARGET)
        print(f"Merged {len(incoming)} lessons; {len(merged)} total deep reads ready.")
    else:
        print(f"Validated {len(existing)} supplemental deep reads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
