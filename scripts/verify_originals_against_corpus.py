#!/usr/bin/env python3
"""Check generated excerpts against a local public-domain Zizhi Tongjian corpus.

The expected corpus layout is the ``web/public/text`` directory from
https://github.com/shenyingjun/zizhi-tongjian-reader.  The check is deliberately
local: it never changes content and never sends a DingTalk message.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LESSONS = ROOT / "content" / "deep_read_218_365.json"
NOTE_MARKERS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
CHINESE_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def chinese_number(value: str) -> int:
    value = value.removeprefix("卷")
    number = 0
    pending = 0
    for character in value:
        if character in CHINESE_DIGITS:
            pending = CHINESE_DIGITS[character]
            continue
        unit = {"十": 10, "百": 100, "千": 1000}.get(character)
        if unit:
            number += (pending or 1) * unit
            pending = 0
    return number + pending


def converter():
    try:
        from opencc import OpenCC  # type: ignore
    except ImportError:
        return lambda text: text
    instance = OpenCC("t2s")
    return instance.convert


TO_SIMPLIFIED = converter()


def normalize(text: str) -> str:
    text = TO_SIMPLIFIED(text)
    return re.sub(rf"[{NOTE_MARKERS}\W_]+", "", text)


def load_corpus(directory: Path) -> dict[int, str]:
    corpus: dict[int, str] = {}
    for path in directory.glob("juan_*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        number = payload.get("juan_no")
        paragraphs = payload.get("paragraphs")
        if not isinstance(number, int) or not isinstance(paragraphs, list):
            continue
        main_text = "".join(
            paragraph.get("main", "")
            for paragraph in paragraphs
            if isinstance(paragraph, dict)
        )
        corpus[number] = normalize(main_text)
    if not corpus:
        raise ValueError(f"no juan_*.json corpus files found in {directory}")
    return corpus


def ngram_coverage(excerpt: str, source: str, size: int) -> float:
    if len(excerpt) < size:
        return float(excerpt in source)
    source_grams = {
        source[index : index + size]
        for index in range(len(source) - size + 1)
    }
    covered = [False] * len(excerpt)
    for index in range(len(excerpt) - size + 1):
        if excerpt[index : index + size] not in source_grams:
            continue
        for position in range(index, index + size):
            covered[position] = True
    return sum(covered) / len(covered)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--lessons", type=Path, default=DEFAULT_LESSONS)
    parser.add_argument("--ngram-size", type=int, default=6)
    parser.add_argument("--minimum-coverage", type=float, default=0.70)
    args = parser.parse_args()

    corpus = load_corpus(args.corpus_dir)
    lessons = json.loads(args.lessons.read_text(encoding="utf-8"))
    failures: list[str] = []
    for lesson in lessons:
        number = lesson["number"]
        volume = chinese_number(lesson["vol"])
        excerpt = normalize(lesson["original"])
        source = corpus.get(volume)
        if not source:
            failures.append(f"lesson {number}: corpus volume {volume} is missing")
            continue
        coverage = ngram_coverage(excerpt, source, args.ngram_size)
        print(
            f"lesson {number}: volume {volume:03d}, "
            f"{args.ngram_size}-gram coverage {coverage:.1%}"
        )
        if coverage < args.minimum_coverage:
            failures.append(
                f"lesson {number}: coverage {coverage:.1%} is below "
                f"{args.minimum_coverage:.1%}"
            )
    if failures:
        raise SystemExit("original-text verification failed:\n" + "\n".join(failures))
    print(f"Verified {len(lessons)} excerpts against the public-domain corpus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
