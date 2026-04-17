#!/usr/bin/env python3
"""Validate KB discoverability, format, and basic non-leakage constraints."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_DOMAIN = REPO_ROOT / "kb" / "domain"
DAB_ROOT = REPO_ROOT / "DataAgentBench"

CORE_DOCS = [
    "dab_schemas.md",
    "query_patterns.md",
    "join_keys.md",
    "unstructured_fields.md",
    "domain_terms.md",
]

RUNTIME_DOCS = [
    KB_DOMAIN / "stockindex.md",
    KB_DOMAIN / "bookreview.md",
    KB_DOMAIN / "yelp.md",
    REPO_ROOT / "kb" / "corrections" / "corrections-log.md",
    REPO_ROOT / "probes" / "probes.md",
]

BLOCKED_PATTERNS = {
    "query_label": re.compile(r"\bQ\d+\s*:", re.IGNORECASE),
    "expected_answer": re.compile(r"expected\s*answer|ground\s*truth", re.IGNORECASE),
    "forbidden_list": re.compile(r"forbidden\s+list|none\s+of\s+these\s+may\s+appear", re.IGNORECASE),
}


def check_markdown_heading(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.exists():
        return [f"missing file: {path.relative_to(REPO_ROOT)}"]
    text = path.read_text(encoding="utf-8")
    if not text.lstrip().startswith("#"):
        issues.append(f"missing top-level markdown heading: {path.relative_to(REPO_ROOT)}")
    return issues


def lint_runtime_file(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing runtime KB file: {path.relative_to(REPO_ROOT)}"]
    text = path.read_text(encoding="utf-8")
    for name, pat in BLOCKED_PATTERNS.items():
        for m in pat.finditer(text):
            ln = text.count("\n", 0, m.start()) + 1
            line = text.splitlines()[ln - 1].strip().lower()
            # Allow negation policy statements.
            if "do not" in line:
                continue
            if "no expected answers" in line or "no ground-truth values" in line:
                continue
            findings.append(f"{path.relative_to(REPO_ROOT)}:{ln}: blocked {name}")
    return findings


def check_dataset_docs() -> tuple[list[str], dict[str, str]]:
    issues: list[str] = []
    mapping: dict[str, str] = {}
    if not DAB_ROOT.exists():
        return ["DataAgentBench directory not found"], mapping

    for ds in sorted(p for p in DAB_ROOT.glob("query_*") if p.is_dir()):
        dataset_key = ds.name.replace("query_", "")
        # agent normalizes to lowercase in strict resolution path for kb filename
        doc_name = f"{dataset_key.lower()}.md"
        doc_path = KB_DOMAIN / doc_name
        mapping[dataset_key] = doc_name
        if not doc_path.exists():
            issues.append(f"missing dataset KB doc for {dataset_key}: kb/domain/{doc_name}")
    return issues, mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="KB integrity/discoverability checks")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument("--strict", action="store_true", help="exit non-zero on issues")
    args = parser.parse_args()

    issues: list[str] = []

    for name in CORE_DOCS:
        issues.extend(check_markdown_heading(KB_DOMAIN / name))

    dataset_issues, dataset_map = check_dataset_docs()
    issues.extend(dataset_issues)

    for p in RUNTIME_DOCS:
        issues.extend(check_markdown_heading(p))
        issues.extend(lint_runtime_file(p))

    report = {
        "issues": issues,
        "core_docs_checked": CORE_DOCS,
        "dataset_kb_map": dataset_map,
        "status": "PASS" if not issues else "FAIL",
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"KB integrity status: {report['status']}")
        if issues:
            for i in issues:
                print(f"- {i}")

    if args.strict and issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
