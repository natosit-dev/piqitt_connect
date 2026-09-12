"""CLI entrypoint for HL7 generation.

This is the script you run. Everything else is imported from /scripts.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from typing import Dict, Any, List

from faker import Faker

from .generators import gen_patient, gen_encounter, gen_observation
from .messages import build_adt, build_oru
from .utils import safe_for_filename


def generate_run(
    *,
    n_patients: int,
    seed: int | None,
    out_dir: str,
    per_encounter: bool,
) -> Dict[str, Any]:
    if seed is not None:
        import random
        random.seed(seed)
        Faker.seed(seed)

    os.makedirs(out_dir, exist_ok=True)

    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"run_{run_ts}"

    counts = {"ADT": 0, "ORU": 0}
    written_files: List[str] = []

    for _ in range(n_patients):
        p = gen_patient()
        e = gen_encounter(p.patient_id)
        o = gen_observation(e)

        adt = build_adt(p, e, obs_for_dg1=o)
        oru = build_oru(p, e, [o])

        msgs = {"ADT": adt, "ORU": oru}
        safe_enc = safe_for_filename(e.encounter_id)

        for name, msg in msgs.items():
            counts[name] += 1
            if per_encounter:
                path = os.path.join(out_dir, f"{name}_{safe_enc}_{run_ts}.hl7")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(msg)
                written_files.append(path)
            else:
                path = os.path.join(out_dir, f"{name}_{run_ts}.hl7")
                mode = "a" if os.path.exists(path) else "w"
                with open(path, mode, encoding="utf-8") as f:
                    if mode == "a":
                        f.write("\n\n")
                    f.write(msg)
                if path not in written_files:
                    written_files.append(path)

    return {"run_id": run_id, "counts": counts, "written_files": written_files}


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
