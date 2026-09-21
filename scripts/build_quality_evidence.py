"""Builds a compact CI evidence file from Coverage and Flake8 outputs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--flake8-critical", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()

    coverage = json.loads(args.coverage.read_text(encoding="utf-8"))
    percentage = round(float(coverage["totals"]["percent_covered"]), 2)
    critical_lines = [line for line in args.flake8_critical.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = {
        "format_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit": args.commit,
        "metrics": [
            {"id": "service_test_coverage", "value": percentage, "unit": "%", "target": ">= 80%"},
            {"id": "critical_flake8_errors", "value": len(critical_lines), "unit": "findings", "target": "0"},
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
