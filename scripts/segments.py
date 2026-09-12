"""HL7 segment builders (MSH/EVN/PID/PV1/OBR/OBX/DG1).

Only includes segments needed for this contest project:
- ADT^A01: MSH, EVN, PID, PV1, OBX (SDOH/vitals/gender), optional DG1
- ORU^R01: MSH, PID, PV1, OBR, OBX (report lines)
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from .models import Encounter, Observation, Patient
from .utils import (
    get_next_control_id,
    hl7_escape,
    hl7_name_from_display,
    hl7_name_from_full,
    one_line,
    ts_hl7,
)


def msh(
    message_type: str,
    *,
    sending_app: str = "FAKELAB",
    sending_facility: str = "MEDILACRAHS",
    receiving_app: str = "MLHS",
    receiving_facility: str = "STAGE",
) -> str:
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    structures = {"ADT^A01": "ADT_A01", "ORU^R01": "ORU_R01"}
    if "^" in message_type and message_type.count("^") == 1:
        message_type = f"{message_type}^{structures.get(message_type, '')}"
    control_id = str(get_next_control_id())
    return (
        f"MSH|^~\\&|{sending_app}|{sending_facility}|{receiving_app}|{receiving_facility}|"
        f"{now}||{message_type}|{control_id}|P|2.5|||AL|NE||UNICODE UTF-8"
    )


def evn(enc: Encounter, event_type: str = "A01") -> str:
    evn_ts = ts_hl7(enc.admit_datetime)
    return f"EVN|{event_type}|{evn_ts}||||{evn_ts}"


def pid(p: Patient) -> str:
    street = one_line(p.address)
    phone = one_line(p.phone)
    addr_comp = f"{street}^^{p.city}^{p.state}^{p.zip_code}"
    return (
        f"PID|1||{p.patient_id}||{hl7_name_from_display(p.patient_name)}||"
        f"{ts_hl7(p.date_of_birth)}|{p.sex}||{p.race}|{addr_comp}||{phone}||||||{p.ssn}"
    )


def pv1(enc: Encounter) -> str:
    admit = ts_hl7(enc.admit_datetime)
    disch = ts_hl7(enc.discharge_datetime)
    attending_nm = hl7_name_from_full(enc.attending_provider_name)
    return (
        f"PV1|1|{enc.patient_class}|{enc.assigned_patient_location}||||{enc.attending_provider_id}^{attending_nm}"
        f"||{enc.hospital_service}||||||||||{enc.visit_number}|||||||||||||||||||||||||{admit}|{disch}"
    )


def obr(enc: Encounter, obs: Optional[Observation]) -> str:
    cpt = obs.cpt_code if obs else ""
    desc = (obs.cpt_description or obs.procedure_description) if obs else ""
    usi = f"{cpt}^{desc}^CPT" if (cpt or desc) else ""
    when = ts_hl7(obs.completed_time if obs else enc.admit_datetime)
    ordering_nm = hl7_name_from_full(enc.ordering_provider_name)
    return f"OBR|1|{enc.placer_order_number}|{enc.filler_order_number}|{usi}|R|||{when}||||||||{enc.ordering_provider_id}^{ordering_nm}"


def obx_report_lines(obs: Observation, *, start_set_id: int = 1, wrap_width: int = 200) -> List[str]:
    ident = f"{obs.cpt_code}^{(obs.cpt_description or obs.procedure_description)}^CPT"
    status = obs.result_status or "F"
    producer = "MEDILACRAHS^DEPT1"

    norm = (obs.observation_text or "").replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = norm.split("\n")

    lines: List[str] = []
    for ln in raw_lines:
        ln = (ln or "").strip()
        if not ln:
            lines.append("")
            continue
        if len(ln) <= wrap_width:
            lines.append(ln)
            continue
        for i in range(0, len(ln), wrap_width):
            lines.append(ln[i:i + wrap_width])

    segs: List[str] = []
    sid = start_set_id
    sub = 1
    for ln in lines:
        segs.append(f"OBX|{sid}|TX|{ident}|{sub}|{hl7_escape(ln)}||||||{status}|||{producer}")
        sid += 1
        sub += 1
    return segs


def dg1(
    enc: Encounter,
    icd_code: str,
    desc: str = "",
    *,
    set_id: int = 1,
    diag_type: str = "F",
    coding_system: str = "ICD-10-CM",
    diag_dt: Optional[str] = None,
) -> str:
    dt_hl7 = ts_hl7(diag_dt or enc.admit_datetime)
    ce = f"{icd_code}^{hl7_escape(desc)}^{coding_system}" if icd_code else "^^"
    return f"DG1|{set_id}||{ce}||{dt_hl7}|{diag_type}"
