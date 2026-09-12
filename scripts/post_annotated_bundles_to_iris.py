from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import requests


def read_ndjson(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="POST annotated FHIR bundles to IRIS custom REST endpoint.")
    ap.add_argument("--in", dest="inp", default="out/fhir_bundles_annotated.ndjson")
    ap.add_argument("--base", default="http://localhost:52773/csp/piqitt/api")
    ap.add_argument("--user", default="_SYSTEM")
    ap.add_argument("--password", default="")
    ap.add_argument("--limit", type=int, default=1, help="How many bundles to send. Use 0 for all.")
    ap.add_argument("--timeout", type=int, default=30)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    inp = Path(args.inp)
    if not inp.exists():
        raise SystemExit(f"Input not found: {inp}")

    bundles = read_ndjson(inp)
    if not bundles:
        raise SystemExit(f"No bundles found in: {inp}")

    if args.limit and args.limit > 0:
        bundles = bundles[: args.limit]

    url = args.base.rstrip("/") + "/bundle"

    s = requests.Session()
    s.auth = (args.user, args.password)
    s.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    ok = 0
    ids: List[str] = []

    for i, b in enumerate(bundles, start=1):
        resp = s.post(url, json=b, timeout=args.timeout)
        if resp.status_code >= 400:
            print(f"[{i}] FAIL {resp.status_code}: {resp.text[:800]}")
            continue
        payload = resp.json()
        ids.append(payload.get("id", ""))
        print(f"[{i}] OK: {payload}")
        ok += 1

    print(f"[DONE] sent={len(bundles)} ok={ok} failed={len(bundles)-ok}")
    if ids and ids[0]:
        print(f"[HINT] Try GET {args.base.rstrip('/')}/bundle/{ids[0]}")


if __name__ == "__main__":
    main()
