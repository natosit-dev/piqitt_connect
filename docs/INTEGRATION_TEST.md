# PIQITT multipage integration test

Branch: `feature/piqitt-multipage-integration`

This branch combines the original PIQITT upload/evaluation UI with the restored PIQITT Connect / IRIS demo as two pages in one Streamlit application.

## Run

```powershell
conda activate piqitt
cd C:\dev\piqitt_connect
python -m pip install -r requirements.txt
python -m streamlit run piqitt.py
```

Streamlit should show the main PIQITT page plus `2 IRIS Connect Demo` in the page navigation.

## Main PIQITT smoke test

1. Open the main PIQITT page.
2. Upload an ADT, ORU, or DFT `.hl7` file.
3. Confirm message parsing and FHIR Bundle creation.
4. Leave PIQI evaluation enabled and confirm per-message and summary scorecards render.

The page uses shared configuration under:

- `piqi_sam_library.yaml`
- `profiles/`
- `ref/`

## IRIS Connect smoke test

1. Confirm the IRIS container and `/csp/piqitt/api` web application are running.
2. Open the IRIS Connect page.
3. Enter the local IRIS password in the sidebar.
4. Generate one encounter.
5. Convert + Score.
6. POST one or two annotated bundles to IRIS.
7. Open the IRIS Browser tab and confirm the stored bundles can be listed and fetched.

The IRIS page now uses the same Clinical-Minimal profile, SAM library, and plausibility reference as the main PIQITT page.

## Known cleanup after smoke test

- The existing contest `app.py` remains in the repository as the legacy single-page entry point; use `piqitt.py` for this branch test.
- The core evaluator/converter should be reconciled against the exact upstream source artifacts after the multipage UI is proven.
- PIQI display scale between the Python scorecard and the IRIS summary API still needs one canonical convention.
