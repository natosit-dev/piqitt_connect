#!/usr/bin/env python3
"""Top-level runner.

Run:
  python scripts_generate_hl7.py --n 10 --out out --per-encounter

Assumes this file is at repo root and `scripts/` is a package directory.
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.run_pipeline import generate_run


def _parse_args():
    ap = argparse.ArgumentParser(description="Generate synthetic HL7 v2 (ADT/ORU) with SDOH + gender identity.")
    ap.add_argument("--n", type=int, default=10, help="Number of patients")
    ap.add_argument("--seed", type=int, default=None, help="Seed for deterministic runs")
    ap.add_argument("--out", type=str, default="out", help="Output folder")
    ap.add_argument("--per-encounter", action="store_true", help="Write one file per encounter per message type")
    return ap.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    res = generate_run(
        n_patients=int(args.n),
        seed=args.seed,
        out_dir=args.out,
        per_encounter=bool(args.per_encounter),
    )
    print("[DONE]", {"run_id": res["run_id"], "counts": res["counts"], "written_files": len(res["written_files"])})
