from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def read_ndjson(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def count_details(details: Any) -> Tuple[int, int, int, int]:
    pass_count = fail_count = skip_count = critical_fail_count = 0
    if not isinstance(details, list):
        return pass_count, fail_count, skip_count, critical_fail_count

    for d in details:
        if not isinstance(d, dict):
            continue
        status = str(d.get("status", "")).upper()
        severity = str(d.get("severity", "")).lower()

        if status == "PASS":
            pass_count += 1
        elif status == "FAIL":
            fail_count += 1
            if severity == "critical":
                critical_fail_count += 1
        elif status == "SKIP":
            skip_count += 1

    return pass_count, fail_count, skip_count, critical_fail_count


def summarize_scores(scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary: List[Dict[str, Any]] = []

    for s in scores:
        source_file = s.get("_source_file")
        source_index = s.get("_source_index")
        hl7_msg_type = s.get("_hl7_msg_type")
        profile_name = s.get("_profile_name")

        piqi_index = safe_float(s.get("piqiIndex", s.get("piqi_index", 0.0)))
        piqi_weighted = safe_float(s.get("piqiWeightedIndex", s.get("piqi_weighted_index", 0.0)))
        numerator = safe_int(s.get("numerator", 0))
        denominator = safe_int(s.get("denominator", 0))
        critical_failures = safe_int(s.get("criticalFailureCount", s.get("critical_failure_count", 0)))

        pass_count, fail_count, skip_count, critical_fail_count = count_details(s.get("details"))

        summary.append({
            "source_file": source_file,
            "source_index": source_index,
            "hl7_msg_type": hl7_msg_type,
            "profile_name": profile_name,
            "piqiIndex": piqi_index,
            "piqiWeightedIndex": piqi_weighted,
            "numerator": numerator,
            "denominator": denominator,
            "criticalFailureCount": critical_failures,
            "detail_pass": pass_count,
            "detail_fail": fail_count,
            "detail_skip": skip_count,
            "detail_critical_fail": critical_fail_count,
        })

    return summary


def write_ndjson(rows: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r))
            f.write("\n")


def write_csv(rows: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Summarize PIQI scores into one row per bundle/message.")
    ap.add_argument("--in", dest="inp", default="out/piqi_scores.ndjson")
    ap.add_argument("--out-ndjson", default="out/piqi_summary.ndjson")
    ap.add_argument("--out-csv", default="out/piqi_summary.csv")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    inp = Path(args.inp)
    if not inp.exists():
        raise SystemExit(f"Input not found: {inp}")

    scores = read_ndjson(inp)
    summary = summarize_scores(scores)

    write_ndjson(summary, Path(args.out_ndjson))
    write_csv(summary, Path(args.out_csv))

    print("[OK]", {
        "input_rows": len(scores),
        "summary_rows": len(summary),
        "out_ndjson": args.out_ndjson,
        "out_csv": args.out_csv,
    })


if __name__ == "__main__":
    main()
