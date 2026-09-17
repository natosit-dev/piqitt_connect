# PIQITT Connect

PIQITT Connect is the combined working application for the PIQI Transformation Tool and its InterSystems IRIS integration lab.

It brings together two previously separate workflows:

1. **PIQITT evaluation** — upload HL7 v2, convert to FHIR R4, evaluate with PIQI, inspect scorecards, and export results.
2. **IRIS Connect demo** — generate synthetic HL7, convert and score it with the same shared engine, append a PIQI Observation, POST the annotated Bundle to IRIS, and browse stored Bundles.

Both Streamlit pages use the same converter, evaluator, SAM library, profiles, and reference data.

## Application architecture

```text
                    +----------------------+
HL7 v2 ------------>| shared FHIR converter|----+
                    +----------------------+    |
                                                   v
                    +----------------------+   FHIR Bundle
                    | shared PIQI evaluator|<---+
                    +----------------------+    |
                              |                  |
              +---------------+------------------+
              |                                  |
              v                                  v
     PIQITT Evaluator page              IRIS Connect page
     scorecards / exports               annotate PIQI Observation
                                                |
                                                v
                                      /csp/piqitt/api
                                                |
                                                v
                                      ^PIQITT global storage
```

A separate IRIS interoperability production is also available for file-based HL7 intake:

```text
ADT_File_Service -> ADT_Routing_Engine -> ADT_Archive
```

The custom REST persistence path is the current known-good IRIS baseline. Native IRIS FHIR repository integration is a later phase.

## Repository layout

```text
piqitt.py                       Main Streamlit PIQITT evaluator
pages/
  2_IRIS_Connect_Demo.py       Synthetic HL7 -> PIQI -> IRIS workflow

lib/
  fhir_convert_backend.py      Canonical HL7 -> FHIR converter
  piqi_eval.py                 Canonical PIQI evaluator
  PIQITT.REST.BundleService.cls IRIS REST persistence service

profiles/
  profile_clinical_minimal.yaml
  profile_claims_minimal.yaml

ref/
  loinc.csv
  cpt.csv
  plausibility.yaml

piqi_sam_library.yaml          Canonical SAM library

scripts/
  hl7_out_to_piqi.py
  post_annotated_bundles_to_iris.py
  summarize_piqi_scores.py
  run_pipeline.py
  ... synthetic HL7 helpers

scripts_generate_hl7.py        Synthetic HL7 CLI entrypoint

docs/
  PROJECT_BUILD.md
  DECISION_LOG.md
  PROVENANCE.md
  PROMPTS_RAW.md
  INTEGRATION_TEST.md
```

The old duplicate `config/` tree and legacy single-page `app.py` entrypoint were removed during integration cleanup. The canonical configuration now lives only in `piqi_sam_library.yaml`, `profiles/`, and `ref/`.

## Python setup

Conda is the preferred local environment manager.

```powershell
conda create -n piqitt python=3.10 -y
conda activate piqitt
python -m pip install -r requirements.txt
```

## Run the multipage application

```powershell
python -m streamlit run piqitt.py
```

Typical local URL:

```text
http://localhost:8501
```

Streamlit navigation exposes the normal PIQITT evaluator and the IRIS Connect demo page.

## Main PIQITT workflow

The main page supports:

- HL7 ADT / ORU / DFT upload
- HL7 -> FHIR conversion
- Clinical-Minimal and Claims-Minimal PIQI evaluation
- per-message PIQI scorecards
- aggregate summaries
- JSON / NDJSON / CSV / Markdown exports
- drill-down into individual PIQI evaluation details

Canonical configuration paths:

```text
piqi_sam_library.yaml
profiles/profile_clinical_minimal.yaml
profiles/profile_claims_minimal.yaml
ref/loinc.csv
ref/cpt.csv
ref/plausibility.yaml
```

## IRIS Connect workflow

Generate synthetic HL7:

```powershell
python .\scripts_generate_hl7.py --n 1 --out out --per-encounter
```

Convert, score, and annotate:

```powershell
python -m scripts.hl7_out_to_piqi `
  --sam piqi_sam_library.yaml `
  --profile profiles/profile_clinical_minimal.yaml `
  --plausibility ref/plausibility.yaml
```

Outputs:

```text
out/fhir_bundles.ndjson
out/fhir_bundles_annotated.ndjson
out/piqi_scores.ndjson
```

Post annotated Bundles to IRIS:

```powershell
python -m scripts.post_annotated_bundles_to_iris `
  --base http://localhost:52773/csp/piqitt/api `
  --user _SYSTEM `
  --password <LOCAL_PASSWORD> `
  --limit 2
```

Gender Harmony source OBXs intentionally use `CWE`.

## IRIS baseline

The repository includes a Docker Compose baseline for:

- InterSystems IRIS for Health Community 2026.1
- web port `52773`
- SuperServer port `1972`
- durable storage under `/durable/iris`
- host exchange mount `./exchange:/exchange`

Start it with:

```powershell
docker compose up -d
```

The rebuilt application namespace is `PIQITT`.

The class `lib/PIQITT.REST.BundleService.cls` is compiled into that namespace and exposed through a web application at:

```text
/csp/piqitt/api
```

Routes:

```text
POST /bundle
GET  /bundle/{id}
GET  /bundles
POST /wipe
```

Credentials remain local and are intentionally not committed.

## PIQI score scale

PIQI scores are represented consistently as **percent values on a 0-100 scale** throughout the Python evaluator, FHIR PIQI Observation, and current REST service source.

Example:

```text
70.59 means 70.59%
```

Older IRIS-stored rows may still show legacy decimal values such as `0.7059` until the updated REST class is imported and new demo data is posted.

## Documentation and provenance

See:

- `docs/PROJECT_BUILD.md` for the current build and architecture
- `docs/DECISION_LOG.md` for key design decisions
- `docs/PROVENANCE.md` for source lineage
- `docs/PROMPTS_RAW.md` for prompt-level provenance with credentials redacted
- `docs/INTEGRATION_TEST.md` for the multipage smoke test

## Next phase

After the integrated baseline is merged, the next major step is to stand up a native IRIS FHIR R4 repository alongside `/csp/piqitt/api` and decide how the interoperability production should invoke or enqueue conversion and PIQI evaluation without breaking the known-good regression path.
