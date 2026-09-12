"""Gender Harmony value selection and OBX builders.

Uses a minimal set of SNOMED/LOINC concepts sufficient for the demo.
"""

from __future__ import annotations

import random
from typing import Dict, Tuple, Optional

from .utils import hl7_escape, ts_hl7

GI_POOL = [
    ("446151000124109", "Male", "SCT"),
    ("446141000124107", "Female", "SCT"),
    ("33791000087105", "Non-binary gender", "SCT"),
    ("74964007", "Intersex", "SCT"),
]

PRONOUN_POOL = [
    ("LA29518-0", "he/him/his/his/himself", "LN"),
    ("LA29519-8", "she/her/her/hers/herself", "LN"),
    ("LA29520-6", "they/them/their/theirs/themselves", "LN"),
]

SPCU_POOL = [
    ("M-T", "Apply male-typical settings", "HL7"),
    ("F-T", "Apply female-typical settings", "HL7"),
    ("S", "Specific (organ/system-specific)", "HL7"),
]

TYPICAL_BY_SEX: Dict[str, Dict[str, Tuple[str, str, str]]] = {
    "M": {"gi": GI_POOL[0], "pro": PRONOUN_POOL[0], "spcu": SPCU_POOL[0]},
    "F": {"gi": GI_POOL[1], "pro": PRONOUN_POOL[1], "spcu": SPCU_POOL[1]},
}

PRODUCER = "MEDILACRAHS^DEPT1"


def _rand_other(pool, not_this):
    choices = [x for x in pool if x != not_this]
    return random.choice(choices) if choices else not_this


def choose(admin_sex: str, match_bias: float = 0.95) -> Dict[str, Tuple[str, str, str]]:
    sex = (admin_sex or "").upper()
    typical = TYPICAL_BY_SEX.get(sex)
    if not typical:
        return {"gi": random.choice(GI_POOL), "pro": random.choice(PRONOUN_POOL), "spcu": random.choice(SPCU_POOL)}
    if random.random() < match_bias:
        return typical
    return {
        "gi": _rand_other(GI_POOL, typical["gi"]),
        "pro": _rand_other(PRONOUN_POOL, typical["pro"]),
        "spcu": _rand_other(SPCU_POOL, typical["spcu"]),
    }


def _obx_cwe(
    *,
    set_id: int,
    obx3: Tuple[str, str, str],
    value: Tuple[str, str, str],
    effective_dt: Optional[str] = None,
    method: Optional[Tuple[str, str, str]] = None,
    performing_org: Optional[str] = None,
) -> str:
    obx3_ce = f"{obx3[0]}^{hl7_escape(obx3[1])}^{obx3[2]}"
    val_ce = f"{value[0]}^{hl7_escape(value[1])}^{value[2]}"
    obx14 = ts_hl7(effective_dt) if effective_dt else ""
    obx17 = f"{method[0]}^{hl7_escape(method[1])}^{method[2]}" if method else ""
    obx23 = performing_org or ""
    return f"OBX|{set_id}|CWE|{obx3_ce}|1|{val_ce}||||||F|||{obx14}|{PRODUCER}|||{obx17}||||{obx23}"


def obx_gender_identity(set_id: int, gi: Tuple[str, str, str], effective_dt: Optional[str] = None) -> str:
    return _obx_cwe(
        set_id=set_id,
        obx3=("76691-5", "Gender identity", "LN"),
        value=gi,
        effective_dt=effective_dt,
        method=("ptReport", "Patient-reported", "HL7"),
        performing_org="MEDILACRAHS",
    )


def obx_pronouns(set_id: int, pronouns: Tuple[str, str, str], effective_dt: Optional[str] = None) -> str:
    return _obx_cwe(
        set_id=set_id,
        obx3=("90778-2", "Personal pronouns - Reported", "LN"),
        value=pronouns,
        effective_dt=effective_dt,
    )


def obx_spcu(set_id: int, spcu: Tuple[str, str, str], effective_dt: Optional[str] = None) -> str:
    return _obx_cwe(
        set_id=set_id,
        obx3=("SPCU", "Sex parameter for clinical use", "HL7"),
        value=spcu,
        effective_dt=effective_dt,
        method=("endo", "Endocrinology assessment", "HL7"),
    )
