# Provenance

## Source repository

The initial PIQITT Connect baseline was reconstructed from:

- Repository: `natosit-dev/piqitt-contest`
- Branch: `main`
- Source commit: `fa01286f93b54da48e3660620fabc2e2da2bb548`
- Source commit message: `Finalize PIQITT contest demo: HL7 > FHIR > PIQI → IRIS REST + Streamlit UI`

## Rebuild session

The working environment was rebuilt on 2026-09-10 through 2026-09-12 using InterSystems IRIS for Health Community 2026.1, Docker Desktop, Conda Python 3.10, and the recovered contest code.

The known-good baseline established during the rebuild includes:

- `PIQITT` IRIS namespace
- file-based HL7 interoperability production
- `PIQITT.REST.BundleService`
- web application `/csp/piqitt/api`
- synthetic ADT and ORU generation
- HL7 to FHIR Bundle conversion
- PIQI evaluation and PIQI Observation annotation
- storage in `^PIQITT`
- Streamlit browsing of stored bundles and PIQI summary metrics

## Files carried forward

The following implementation areas were copied or normalized from the contest baseline:

- `app.py`
- `scripts_generate_hl7.py`
- `scripts/` generation and pipeline modules
- `lib/fhir_convert_backend.py`
- `lib/piqi_eval.py`
- `lib/PIQITT.REST.BundleService.cls`
- `config/piqi_sam_library.yaml`
- `config/profile_clinical_minimal.yaml`
- `config/plausibility.yaml`

## Intentional baseline adjustments

PIQITT Connect is not a byte-for-byte mirror of the contest repository. The baseline intentionally applies a small number of environment updates:

- IRIS container baseline updated from 2024.3 to 2026.1.
- The Streamlit custom API default is `http://localhost:52773/csp/piqitt/api`.
- No local password is committed to the repository.
- The broken merge-conflict state in the old `requirements.txt` was replaced with the dependency set proven during rebuild.
- Documentation and prompt provenance were added under `docs/`.

## Raw prompt record

`docs/PROMPTS_RAW.md` contains the user-side rebuild prompts and command output used to establish the baseline. Local credentials and account-specific secrets are redacted.

## Baseline policy

This repository is intended to become the durable integration branch for PIQITT. Historical experiment repositories remain useful as references, but new architecture work should start from this known-good baseline and record material changes in `docs/DECISION_LOG.md` and `docs/PROJECT_BUILD.md`.
