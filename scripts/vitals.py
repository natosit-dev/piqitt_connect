"""Vitals prediction and OBX builders.

Kept intentionally lightweight: no ML deps, deterministic-ish behavior.
"""

from __future__ import annotations

from typing import Dict, List


def predict_vitals(age: int) -> Dict[str, float]:
    age = max(0, min(120, int(age)))

    systolic = 105 + 0.55 * age
    hr = 65 + 0.12 * age
    o2 = 99 - 0.01 * age
    bmi = 20 + 0.05 * age

    return {
        "systolic_bp": round(systolic, 1),
        "heart_rate": round(hr, 1),
        "o2_sat": round(max(75.0, min(100.0, o2)), 1),
        "bmi": round(max(14.0, min(60.0, bmi)), 1),
    }


def obx_vitals(start_set_id: int, vitals: Dict[str, float]) -> List[str]:
    return [
        f"OBX|{start_set_id}|NM|8480-6^Systolic BP^LN||{vitals.get('systolic_bp', 0.0):.1f}|mmHg|90-140||||F",
        f"OBX|{start_set_id+1}|NM|8867-4^Heart rate^LN||{vitals.get('heart_rate', 0.0):.1f}|/min|60-100||||F",
        f"OBX|{start_set_id+2}|NM|59408-5^Oxygen saturation^LN||{vitals.get('o2_sat', 0.0):.1f}|%|95-100||||F",
        f"OBX|{start_set_id+3}|NM|39156-5^Body mass index^LN||{vitals.get('bmi', 0.0):.1f}|kg/m2|18.5-24.9||||F",
    ]
