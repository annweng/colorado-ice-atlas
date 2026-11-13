#!/usr/bin/env python3
"""Run the Colorado Ice Atlas daily pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.processing.pipeline import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest data and generate ice estimates")
    parser.add_argument("--skip-elevation", action="store_true", help="Reuse inventory without resampling 3DEP")
    args = parser.parse_args()
    result = run(skip_elevation=args.skip_elevation)
    print(json.dumps(result, indent=2))
    return 0 if result.get("processing_status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
