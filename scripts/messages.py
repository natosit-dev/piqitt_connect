"""High-level HL7 message builders for the contest demo.

Keeps only what you need:
- ADT^A01 with SDOH + vitals + gender harmony OBXs
- ORU^R01 with a radiology-style report in OBXs
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from .models import Encounter, Observation, Patient
from .segments import msh, evn, pid, pv1, obr, obx_report_lines, dg1
from .vitals import predict_vitals, obx_vitals
from .gender_harmony import choose, obx_gender_identity, obx_pronouns, obx_spcu

AIRNOW_MILES_DEFAULT = 75


def build_adt(
    p: Patient,
    enc: Encounter,
    *,
    include_vitals: bool = True,
    include_gender_harmony: bool = True,
    obs_for_dg1: Optional[Observation] = None,
) -> str:
    parts = [msh("ADT^A01"), evn(enc, "A01"), pid(p), pv1(enc)]
    set_id = 1

    if include_vitals:
        age = datetime.now().year - datetime.strptime(p.date_of_birth, "%Y-%m-%d").year
        parts.extend(obx_vitals(set_id, predict_vitals(age)))
        set_id += 4

    if include_gender_harmony:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gh = choose(p.sex, match_bias=0.95)
        parts.append(obx_gender_identity(set_id, gh["gi"], effective_dt=now)); set_id += 1
        parts.append(obx_pronouns(set_id, gh["pro"], effective_dt=now)); set_id += 1
        parts.append(obx_spcu(set_id, gh["spcu"], effective_dt=now)); set_id += 1

    if obs_for_dg1 and obs_for_dg1.icd_code:
        parts.append(
            dg1(
                enc,
                obs_for_dg1.icd_code,
                obs_for_dg1.icd_description,
                set_id=1,
                diag_type="A",
                diag_dt=obs_for_dg1.completed_time,
            )
        )

    return "\r".join(parts)


def build_oru(p: Patient, enc: Encounter, obs_list: List[Observation]) -> str:
    first = obs_list[0] if obs_list else None
    parts = [msh("ORU^R01"), pid(p), pv1(enc), obr(enc, first)]
    set_id = 1
    for obs in obs_list:
        parts.extend(obx_report_lines(obs, start_set_id=set_id))
        set_id += len(parts)
    return "\r".join(parts)
