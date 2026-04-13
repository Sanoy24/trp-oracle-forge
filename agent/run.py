from __future__ import annotations

import json
import sys

from dotenv import load_dotenv

from oracle_forge_agent import run_agent


def main(argv: list[str]) -> int:
    load_dotenv()

    if len(argv) < 2:
        print("Usage: python agent/run.py \"<question>\"")
        return 2

    question = " ".join(argv[1:]).strip()
    resp = run_agent(question)
    print(json.dumps(resp.model_dump(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

