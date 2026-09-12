"""Utility helpers for HL7 building and deterministic synthetic values."""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime
from typing import Optional

COUNTER_FILE = "control_id_counter.txt"


def get_next_control_id() -> int:
    """Incrementing integer control ID persisted between runs."""
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            current = int((f.read().strip() or "0"))
    else:
        current = 0
    next_id = current + 1
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        f.write(str(next_id))
    return next_id


def ts_hl7(dt: Optional[datetime | str]) -> str:
    """HL7 TS: YYYYMMDDHHMMSS; None -> '' ; str -> digits-only."""
    if dt is None:
        return ""
    if isinstance(dt, str):
        return re.sub(r"\D", "", dt)
    return dt.strftime("%Y%m%d%H%M%S")


def one_line(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.replace("\r", " ").replace("\n", " ")).strip()


def hl7_name_from_display(patient_name: str) -> str:
    """Convert 'LAST, FIRST' into HL7 XPN family^given."""
    if not patient_name:
        return "^"
    parts = [p.strip() for p in str(patient_name).split(",", 1)]
    family = parts[0] if parts else ""
    given = parts[1] if len(parts) > 1 else ""
    return f"{family}^{given}"


def hl7_name_from_full(display_name: str) -> str:
    """Convert 'First Last' or 'LAST, FIRST' into HL7 XPN family^given."""
    if not display_name:
        return "^"
    s = str(display_name).strip()
    if "," in s:
        return hl7_name_from_display(s)
    parts = s.split()
    if len(parts) == 1:
        return f"{parts[0]}^"
    given, family = parts[0], parts[-1]
    return f"{family.upper()}^{given.upper()}"


def hl7_escape(value: Optional[str]) -> str:
    """Escape HL7 delimiters for fields."""
    if value is None:
        return ""
    s = str(value)
    s = s.replace("\\", "\\E\\")
    s = s.replace("|", "\\F\\").replace("^", "\\S\\").replace("&", "\\T\\").replace("~", "\\R\\")
    return s


def stable_int(seed: str, lo: int, hi: int) -> int:
    """Deterministic int in [lo, hi] based on a seed string."""
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    n = int(h[:8], 16)
    return lo + (n % (hi - lo + 1))


def safe_for_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]", "_", value or "")
