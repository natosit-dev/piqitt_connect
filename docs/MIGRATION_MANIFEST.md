# Migration Manifest

## Source

Initial implementation source:

```text
natosit-dev/piqitt-contest
main @ fa01286f93b54da48e3660620fabc2e2da2bb548
```

## Carried into PIQITT Connect

Core end-to-end path:

- `app.py`
- `scripts_generate_hl7.py`
- `scripts/__init__.py`
- `scripts/run_pipeline.py`
- `scripts/generators.py`
- `scripts/models.py`
- `scripts/messages.py`
- `scripts/segments.py`
- `scripts/utils.py`
- `scripts/vitals.py`
- `scripts/gender_harmony.py`
- `scripts/hl7_out_to_piqi.py`
- `scripts/post_annotated_bundles_to_iris.py`
- `scripts/summarize_piqi_scores.py`
- `lib/fhir_convert_backend.py`
- `lib/piqi_eval.py`
- `lib/PIQITT.REST.BundleService.cls`
- `config/piqi_sam_library.yaml`
- `config/profile_clinical_minimal.yaml`
- `config/plausibility.yaml`

Environment and documentation:

- `docker-compose.yaml` updated for IRIS for Health Community 2026.1
- cleaned `requirements.txt`
- project-specific `.gitignore`
- `docs/PROJECT_BUILD.md`
- `docs/DECISION_LOG.md`
- `docs/PROVENANCE.md`
- `docs/PROMPTS_RAW.md`

## Contest files not copied into the first baseline

The following source scripts were not required by the proven rebuild path and were intentionally left behind for now:

- `scripts/fhir_annotate.py`
- `scripts/fhir_convert.py`
- `scripts/piqi_score.py`
- `scripts/process_hl7.py`
- `scripts/push_to_iris.py`
- `scripts/reset_iris.ps1`

These remain available in the source repository for reference. In particular, `push_to_iris.py` is relevant when native IRIS FHIR repository work resumes.

## Baseline normalization

PIQITT Connect is intentionally not a byte-for-byte fork. Changes include:

- IRIS container updated from 2024.3 to 2026.1.
- Streamlit custom REST base URL updated to port 52773.
- runtime passwords removed from current CLI/UI defaults where practical.
- the merge-conflicted contest `requirements.txt` replaced by the dependency set proven during rebuild.
- generated output, local exchange folders, local environments, and secrets excluded by `.gitignore`.
- provenance and build documentation added.

## Regression expectation

The baseline should continue to reproduce the verified workflow:

```text
1 synthetic encounter
-> 1 ADT + 1 ORU
-> 2 FHIR Bundles
-> 2 PIQI scorecards
-> 2 annotated Bundles
-> IRIS custom REST storage
-> Streamlit browse/retrieve
```

Representative rebuild PIQI results:

```text
0.7059 (24/34), critical failures 0
0.4286 (3/7), critical failures 0
```
