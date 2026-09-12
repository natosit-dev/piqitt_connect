"""Synthetic entity generators (Patient / Encounter / Observation)."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

from faker import Faker

from .models import Encounter, Observation, Patient
from .utils import one_line

fake = Faker()

ZIP_POOL = [
    ("02139", "Cambridge", "MA"),
    ("02138", "Cambridge", "MA"),
    ("10001", "New York", "NY"),
    ("19104", "Philadelphia", "PA"),
    ("60611", "Chicago", "IL"),
    ("94103", "San Francisco", "CA"),
]

CPT_POOL = [
    ("71045", "Chest X-ray, single view"),
    ("70450", "CT head/brain w/o contrast"),
    ("72125", "CT cervical spine w/o contrast"),
]

ICD_POOL = [
    ("R07.9", "Chest pain, unspecified"),
    ("S09.90XA", "Unspecified injury of head, initial encounter"),
    ("M54.2", "Cervicalgia"),
]


def gen_patient() -> Patient:
    zip_code, city, state = random.choice(ZIP_POOL)
    sex = random.choice(["M", "F"])

    name_parts = (fake.name_female() if sex == "F" else fake.name_male()).split()
    first, last = name_parts[0], name_parts[-1]

    return Patient(
        patient_id=fake.unique.bothify("RAD#######"),
        patient_name=f"{last.upper()}, {first.upper()}",
        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%Y-%m-%d"),
        sex=sex,
        race=random.choice(["White", "Black", "Asian", "Hispanic", "Other"]),
        ssn=fake.ssn(),
        address=fake.street_address(),
        phone=one_line(fake.phone_number()),
        zip_code=zip_code,
        city=city,
        state=state,
    )


def gen_encounter(patient_id: str) -> Encounter:
    admit_dt = fake.date_time_between(start_date="-14d", end_date="-1d")
    disch_dt = admit_dt + timedelta(hours=random.randint(1, 6))
    visit = fake.unique.bothify("VN##########")

    prov = fake.name().split()
    first, last = prov[0], prov[-1]
    prov_disp = f"{last.upper()}, {first.upper()}"

    return Encounter(
        encounter_id=f"{patient_id}_{visit}",
        patient_id=patient_id,
        visit_number=visit,
        patient_class="OUTPATIENT",
        assigned_patient_location="DEPT1",
        admit_datetime=admit_dt.strftime("%Y-%m-%d %H:%M:%S"),
        discharge_datetime=disch_dt.strftime("%Y-%m-%d %H:%M:%S"),
        hospital_service="OP",
        ordering_provider_id=fake.bothify("R######"),
        ordering_provider_name=prov_disp,
        attending_provider_id=fake.bothify("P######"),
        attending_provider_name=prov_disp,
        placer_order_number=str(uuid.uuid4()),
        filler_order_number=str(uuid.uuid4()),
    )


def gen_observation(enc: Encounter) -> Observation:
    admit_ts = datetime.strptime(enc.admit_datetime, "%Y-%m-%d %H:%M:%S")
    disch_ts = datetime.strptime(enc.discharge_datetime, "%Y-%m-%d %H:%M:%S")
    delta_sec = max(1, int((disch_ts - admit_ts).total_seconds()))
    completed = admit_ts + timedelta(seconds=random.randint(0, delta_sec))

    cpt = random.choice(CPT_POOL)
    icd = random.choice(ICD_POOL)
    report_text = fake.paragraph(nb_sentences=6)

    return Observation(
        encounter_id=enc.encounter_id,
        observation_id=str(uuid.uuid4()),
        cpt_code=cpt[0],
        cpt_description=cpt[1],
        icd_code=icd[0],
        icd_description=icd[1],
        placer_order_number=enc.placer_order_number,
        filler_order_number=enc.filler_order_number,
        procedure_description=cpt[1],
        observation_text=report_text,
        result_status="F",
        completed_time=completed.strftime("%Y-%m-%d %H:%M:%S"),
    )
