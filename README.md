# PIQITT Connect

PIQITT Connect is the working integration baseline for the PIQI Transformation Tool: synthetic HL7 v2 -> FHIR R4 Bundles -> PIQI evaluation -> InterSystems IRIS persistence and browsing.

This repository was rebuilt from the cleaner `natosit-dev/piqitt-contest` implementation and normalized for the current IRIS for Health 2026.1 development environment.

## Current architecture

```text
Synthetic HL7 v2 (ADT / ORU)
        |
        v
Python HL7 -> FHIR conversion
        |
        v
PIQI evaluation
        |
        v
PIQI Observation annotation
        |
        v
/csp/piqitt/api
        |
        v
PIQITT.REST.BundleService
        |
        v
^PIQITT globals
        |
        v
Streamlit IRIS Browser
```

A separate IRIS interoperability production is also available for file-based HL7 intake:

```text
ADT_File_Service -> ADT_Routing_Engine -> ADT_Archive
```

The custom REST persistence path is the known-good baseline. Native IRIS FHIR repository integration is the next major phase.

## Repository layout

```text
app.py                         Streamlit demo/browser
scripts_generate_hl7.py        Synthetic HL7 CLI entrypoint
config/                        PIQI SAM/profile/plausibility config
lib/
  fhir_convert_backend.py      HL7 -> FHIR conversion
  piqi_eval.py                 PIQI evaluator
  PIQITT.REST.BundleService.cls IRIS REST persistence service
scripts/
  run_pipeline.py              Synthetic data generation
  hl7_out_to_piqi.py           HL7 -> FHIR -> PIQI driver
  post_annotated_bundles_to_iris.py
  summarize_piqi_scores.py
  ...                          HL7 segment/generator helpers
docs/
  PROJECT_BUILD.md             Rebuild baseline and architecture
  DECISION_LOG.md              Architecture decisions
  PROVENANCE.md                Source lineage
  PROMPTS_RAW.md               User prompt provenance, with secrets redacted
```

## Python setup

Conda is the preferred local environment manager.

```powershell
conda create -n piqitt python=3.10 -y
conda activate piqitt
python -m pip install -r requirements.txt
```

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

The IRIS class in `lib/PIQITT.REST.BundleService.cls` is compiled into that namespace and exposed through a web application at:

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

Credentials are local configuration and are intentionally not committed.

## Generate synthetic HL7

```powershell
python .\scripts_generate_hl7.py --n 1 --out out --per-encounter
```

One encounter produces an ADT and an ORU message.

Gender Harmony source OBXs intentionally use `CWE`.

## Convert and score

```powershell
python -m scripts.hl7_out_to_piqi `
  --sam config/piqi_sam_library.yaml `
  --profile config/profile_clinical_minimal.yaml `
  --plausibility config/plausibility.yaml
```

Outputs:

```text
out/fhir_bundles.ndjson
out/fhir_bundles_annotated.ndjson
out/piqi_scores.ndjson
```

Optional score summary:

```powershell
python -m scripts.summarize_piqi_scores
```

## Post annotated bundles to IRIS

```powershell
python -m scripts.post_annotated_bundles_to_iris `
  --base http://localhost:52773/csp/piqitt/api `
  --user _SYSTEM `
  --password <LOCAL_PASSWORD> `
  --limit 2
```

The rebuild smoke test verified both bundle persistence and extraction of PIQI summary values from the PIQI Observation.

## Run the Streamlit UI

```powershell
python -m streamlit run app.py
```

Typical local URL:

```text
http://localhost:8501
```

The default custom IRIS API URL in the UI is:

```text
http://localhost:52773/csp/piqitt/api
```

## Verified rebuild results

A one-encounter smoke test produced two messages and two annotated FHIR Bundles. Example PIQI results from the rebuild were:

```text
PIQI index 0.7059, numerator 24, denominator 34, critical failures 0
PIQI index 0.4286, numerator 3, denominator 7, critical failures 0
```

## Documentation and provenance

See:

- `docs/PROJECT_BUILD.md` for the current build baseline
- `docs/DECISION_LOG.md` for key design decisions
- `docs/PROVENANCE.md` for source repository and rebuild lineage
- `docs/PROMPTS_RAW.md` for prompt-level provenance from the rebuild session

## Next phase

Stand up a native IRIS FHIR R4 repository alongside `/csp/piqitt/api`, then connect the IRIS interoperability production to the FHIR/PIQI pipeline while preserving the recovered contest workflow as a regression baseline.
