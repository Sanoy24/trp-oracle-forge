#!/usr/bin/env python3
"""Simple leakage lint for runtime-injectable KB files.

Fails when files contain benchmark-shaped leakage patterns such as query labels,
explicit expected answers, ground-truth mentions, or forbidden-list wording.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Only lint files that can affect runtime prompts in non-strict mode.
TARGETS = [
    REPO_ROOT / "kb" / "domain" / "stockindex.md",
    REPO_ROOT / "kb" / "domain" / "bookreview.md",
    REPO_ROOT / "kb" / "domain" / "yelp.md",
    REPO_ROOT / "kb" / "corrections" / "corrections-log.md",
    REPO_ROOT / "probes" / "probes.md",
]

PATTERNS = {
    "query_label": re.compile(r"\bQ\d+\s*:", re.IGNORECASE),
    "ground_truth": re.compile(r"ground\s*truth|expected\s*answer", re.IGNORECASE),
    "forbidden_list": re.compile(r"forbidden\s+list|none\s+of\s+these\s+may\s+appear", re.IGNORECASE),
    "score_hint": re.compile(r"matches\s+ground\s+truth|post-fix\s+score", re.IGNORECASE),
}


def lint_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    findings: list[str] = []
    for name, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            line = text.splitlines()[line_no - 1].strip()
            line_lower = line.lower()
            # Policy negations like "do not store ... ground-truth" are expected.
            if "do not" in line_lower and name in {"ground_truth", "forbidden_list", "score_hint"}:
                continue
            if "no expected answers" in line_lower or "no ground-truth values" in line_lower:
                continue
            findings.append(f"{path.relative_to(REPO_ROOT)}:{line_no}: {name}: {line}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Leakage lint for runtime KB files")
    parser.add_argument("--strict", action="store_true", help="exit non-zero on findings")
    args = parser.parse_args()

    all_findings: list[str] = []
    for target in TARGETS:
        if target.exists():
            all_findings.extend(lint_file(target))

    if all_findings:
        print("KB leakage lint findings:")
        for f in all_findings:
            print(f"- {f}")
        return 1 if args.strict else 0

    print("KB leakage lint: PASS (no blocked patterns found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
