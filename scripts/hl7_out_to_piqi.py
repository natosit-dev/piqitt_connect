# scripts/hl7_out_to_piqi.py
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib import fhir_convert_backend as fhir
from lib.piqi_eval import PIQIEvaluator

try:
    import yaml
except ImportError as e:
    raise SystemExit("Missing dependency: pyyaml. Install with: pip install pyyaml") from e


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_yaml_dict(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def find_patient_reference(bundle: Dict[str, Any]) -> Optional[str]:
    for entry in bundle.get("entry", []):
        r = (entry or {}).get("resource") or {}
        if r.get("resourceType") == "Patient" and r.get("id"):
            return f"Patient/{r['id']}"
    return None


def minimal_piqi_observation(piqi: Dict[str, Any], *, patient_ref: Optional[str]) -> Dict[str, Any]:
    score = float(piqi.get("piqiIndex", 0.0))
    weighted = float(piqi.get("piqiWeightedIndex", 0.0))
    numer = int(piqi.get("numerator", 0))
    denom = int(piqi.get("denominator", 0))
    crit = int(piqi.get("criticalFailureCount", 0))

    obs: Dict[str, Any] = {
        "resourceType": "Observation",
        "id": f"piqi-{int(datetime.now().timestamp())}",
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "survey"}]}],
        "code": {"text": "PIQI Score"},
        "effectiveDateTime": utc_now_iso(),
        "valueQuantity": {"value": round(score * 100.0, 2), "unit": "%"},
        "component": [
            {"code": {"text": "piqiIndex"}, "valueDecimal": score},
            {"code": {"text": "piqiWeightedIndex"}, "valueDecimal": weighted},
            {"code": {"text": "numerator"}, "valueInteger": numer},
            {"code": {"text": "denominator"}, "valueInteger": denom},
            {"code": {"text": "criticalFailureCount"}, "valueInteger": crit},
        ],
    }
    if patient_ref:
        obs["subject"] = {"reference": patient_ref}
    return obs


def add_piqi_to_bundle(bundle: Dict[str, Any], piqi: Dict[str, Any], profile_name: str) -> Dict[str, Any]:
    patient_ref = find_patient_reference(bundle)

    if hasattr(fhir, "build_piqi_observation"):
        piqi_obs = fhir.build_piqi_observation(piqi, bundle, profile_name=profile_name)
    else:
        piqi_obs = minimal_piqi_observation(piqi, patient_ref=patient_ref)

    bundle.setdefault("entry", []).append({"resource": piqi_obs})
    return bundle


def split_messages(text: str) -> List[str]:
    if hasattr(fhir, "split_messages"):
        msgs = fhir.split_messages(text)
        return [m.strip() for m in msgs if m and m.strip()]

    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    buf: List[str] = []
    out: List[str] = []
    for line in norm.split("\n"):
        if line.startswith("MSH|") and buf:
            out.append("\r".join(buf))
            buf = [line]
        else:
            buf.append(line)
    if buf:
        out.append("\r".join(buf))
    return [m.strip() for m in out if m and m.strip()]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def ndjson_write(objs: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for o in objs:
            f.write(json.dumps(o))
            f.write("\n")


def process_out_folder(
    out_dir: Path,
    *,
    sam_yaml: Path,
    profile_yaml: Path,
    plausibility_yaml: Optional[Path],
    include_annotated_bundle: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    profile_doc = load_yaml_dict(profile_yaml)
    profile_name = (profile_doc.get("profile") or {}).get("name")
    if not profile_name:
        raise ValueError(f"Missing profile.name in: {profile_yaml}")

    plaus_cfg = load_yaml_dict(plausibility_yaml) if plausibility_yaml else None

    evaluator = PIQIEvaluator(
        sam_library_path=str(sam_yaml.resolve()),
        profile_paths=[str(profile_yaml.resolve())],
        plausibility_cfg=plaus_cfg,
    )

    bundles: List[Dict[str, Any]] = []
    scores: List[Dict[str, Any]] = []
    annotated: List[Dict[str, Any]] = []

    hl7_files = sorted(out_dir.glob("*.hl7"))
    if not hl7_files:
        raise RuntimeError(f"No .hl7 files found in: {out_dir}")

    for hl7_path in hl7_files:
        raw = read_text(hl7_path)
        messages = split_messages(raw)

        for idx, msg in enumerate(messages, start=1):
            result = fhir.convert_message_to_bundle(msg)
            if not result:
                continue

            if isinstance(result, tuple):
                bundle, msg_type = result
            else:
                bundle, msg_type = result, "UNKNOWN"

            if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
                raise TypeError(f"Expected FHIR Bundle dict; got {type(bundle)} from {hl7_path.name}")

            bundle.setdefault("meta", {})
            bundle["meta"].setdefault("tag", []).append(
                {"system": "http://example.org/piqitt", "code": "source-hl7-file", "display": str(hl7_path.name)}
            )
            bundle["meta"]["tag"].append(
                {"system": "http://example.org/piqitt", "code": "source-hl7-index", "display": str(idx)}
            )
            bundle["meta"]["tag"].append(
                {"system": "http://example.org/piqitt", "code": "hl7-msg-type", "display": str(msg_type)}
            )

            bundles.append(bundle)

            piqi = evaluator.evaluate_bundle(bundle, profile_name)
            piqi["_source_file"] = str(hl7_path.name)
            piqi["_source_index"] = idx
            piqi["_hl7_msg_type"] = str(msg_type)
            piqi["_profile_name"] = profile_name
            scores.append(piqi)

            if include_annotated_bundle:
                annotated.append(add_piqi_to_bundle(copy.deepcopy(bundle), piqi, profile_name))

    return bundles, scores, annotated


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Convert HL7 .hl7 files in /out to FHIR bundles and PIQI scores.")
    ap.add_argument("--out-dir", default="out", help="Folder containing .hl7 files (default: out)")
    ap.add_argument("--sam", required=True, help="SAM library YAML")
    ap.add_argument("--profile", required=True, help="Profile YAML")
    ap.add_argument("--plausibility", default=None, help="Optional plausibility YAML")
    ap.add_argument("--no-annotate", action="store_true", help="Do not append PIQI Observation to bundles")
    ap.add_argument("--bundles-out", default="out/fhir_bundles.ndjson")
    ap.add_argument("--scores-out", default="out/piqi_scores.ndjson")
    ap.add_argument("--annotated-out", default="out/fhir_bundles_annotated.ndjson")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    out_dir = Path(args.out_dir)
    sam = Path(args.sam)
    profile = Path(args.profile)
    plaus = Path(args.plausibility) if args.plausibility else None

    bundles, scores, annotated = process_out_folder(
        out_dir,
        sam_yaml=sam,
        profile_yaml=profile,
        plausibility_yaml=plaus,
        include_annotated_bundle=not args.no_annotate,
    )

    ndjson_write(bundles, Path(args.bundles_out))
    ndjson_write(scores, Path(args.scores_out))
    if not args.no_annotate:
        ndjson_write(annotated, Path(args.annotated_out))

    print(
        "[OK]",
        {
            "hl7_out_dir": str(out_dir),
            "bundles": len(bundles),
            "scores": len(scores),
            "annotated": (0 if args.no_annotate else len(annotated)),
            "bundles_out": args.bundles_out,
            "scores_out": args.scores_out,
            "annotated_out": (None if args.no_annotate else args.annotated_out),
        },
    )


if __name__ == "__main__":
    main()
