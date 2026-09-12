from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="PIQITT Connect", layout="wide")
st.title("PIQITT Connect: HL7 -> FHIR -> PIQI -> IRIS")

# ----------------------------
# Sidebar: IRIS connection
# ----------------------------
with st.sidebar:
    st.header("IRIS API")
    base_url = st.text_input("Base URL", value="http://localhost:52773/csp/piqitt/api")
    user = st.text_input("Username", value="_SYSTEM")
    password = st.text_input("Password", value="", type="password")
    timeout_s = st.number_input("Timeout (sec)", min_value=5, max_value=120, value=30)

    st.divider()
    st.header("Local Paths")
    out_dir = st.text_input("HL7 out folder", value=str(REPO_ROOT / "out"))
    config_dir = st.text_input("Config folder", value=str(REPO_ROOT / "config"))

    st.divider()
    st.header("Generation")
    n_messages = st.number_input("HL7 encounters", min_value=1, max_value=500, value=10)
    per_encounter = st.checkbox("Per-encounter files", value=True)


def run_cmd(cmd: list[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return p.returncode, p.stdout


def api_get(path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        r = requests.get(url, auth=(user, password), timeout=timeout_s)
        if r.status_code >= 400:
            return None, f"{r.status_code} {r.reason}: {r.text[:800]}"
        if not r.text.strip():
            return {"ok": True}, None
        return r.json(), None
    except Exception as e:
        return None, str(e)


def api_post(path: str, payload: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        r = requests.post(url, json=payload, auth=(user, password), timeout=timeout_s)
        if r.status_code >= 400:
            return None, f"{r.status_code} {r.reason}: {r.text[:800]}"
        if not r.text.strip():
            return {"ok": True}, None
        return r.json(), None
    except Exception as e:
        return None, str(e)


def api_post_bundle(bundle: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    return api_post("bundle", bundle)


# ----------------------------
# Tabs
# ----------------------------
tab_run, tab_iris = st.tabs(["Run Pipeline", "IRIS Browser"])

# ----------------------------
# Run Pipeline
# ----------------------------
with tab_run:
    st.subheader("1) Generate HL7")
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("Generate HL7", use_container_width=True):
            cmd = ["python", "scripts_generate_hl7.py", "--n", str(int(n_messages)), "--out", out_dir]
            if per_encounter:
                cmd.append("--per-encounter")
            rc, out = run_cmd(cmd)
            st.code(out)
            if rc != 0:
                st.error(f"Generate HL7 failed (exit {rc})")
            else:
                st.success("HL7 generated.")

    st.subheader("2) Convert + PIQI annotate")
    sam_yaml = Path(config_dir) / "piqi_sam_library.yaml"
    profile_yaml = Path(config_dir) / "profile_clinical_minimal.yaml"
    plaus_yaml = Path(config_dir) / "plausibility.yaml"

    if st.button("Convert + Score (hl7_out_to_piqi)", use_container_width=True):
        cmd = [
            "python",
            "-m",
            "scripts.hl7_out_to_piqi",
            "--sam",
            str(sam_yaml),
            "--profile",
            str(profile_yaml),
            "--plausibility",
            str(plaus_yaml),
        ]
        rc, out = run_cmd(cmd)
        st.code(out)
        if rc != 0:
            st.error(f"Convert/Score failed (exit {rc})")
        else:
            st.success("FHIR bundles scored + annotated.")

    st.subheader("3) Send annotated bundles to IRIS")
    annotated_path = Path(out_dir) / "fhir_bundles_annotated.ndjson"
    limit = st.number_input("How many bundles to send", min_value=1, max_value=500, value=5)

    if st.button("POST to IRIS", use_container_width=True):
        if not annotated_path.exists():
            st.error(f"Missing: {annotated_path}")
        else:
            sent = 0
            ok = 0
            with annotated_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if sent >= int(limit):
                        break
                    line = line.strip()
                    if not line:
                        continue
                    bundle = json.loads(line)
                    sent += 1
                    resp, err = api_post_bundle(bundle)
                    if err:
                        st.error(f"[{sent}] {err}")
                    else:
                        ok += 1
                        st.write(resp)
            st.success(f"Done. sent={sent} ok={ok} failed={sent-ok}")

# ----------------------------
# IRIS Browser
# ----------------------------
with tab_iris:
    st.subheader("Stored Bundles (IRIS)")

    cbtn1, cbtn2, cbtn3 = st.columns([1, 1, 3])

    with cbtn1:
        if st.button("Refresh list", use_container_width=True):
            st.session_state.pop("bundle_list", None)

    with cbtn2:
        if st.button("Wipe IRIS Demo Data", type="secondary", use_container_width=True):
            resp, err = api_post("wipe")
            if err:
                st.error(err)
            else:
                st.success("Wiped IRIS demo data.")
                st.session_state.pop("bundle_list", None)

    with cbtn3:
        st.caption("Wipe clears the demo global (^PIQITT). Use when rerunning the pipeline for a clean demo.")

    if "bundle_list" not in st.session_state:
        data, err = api_get("bundles")
        if err:
            st.error(err)
            data = None
        st.session_state.bundle_list = data

    data = st.session_state.bundle_list
    if data:
        items = data.get("items", [])
        st.caption(f"Count: {data.get('count', len(items))}")

        items_sorted = sorted(items, key=lambda x: x.get("storedAt", ""), reverse=True)
        st.dataframe(items_sorted, use_container_width=True, hide_index=True)

        st.markdown("### View one bundle")
        bundle_id = st.text_input("Bundle ID", value=(items_sorted[0]["id"] if items_sorted else ""))
        if st.button("Fetch bundle JSON"):
            if bundle_id:
                bundle, err = api_get(f"bundle/{bundle_id}")
                if err:
                    st.error(err)
                else:
                    st.json(bundle)
            else:
                st.warning("Enter a bundle id.")
