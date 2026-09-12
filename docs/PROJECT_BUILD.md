# PIQITT Connect Project Build

Baseline date: 2026-09-12

Source baseline: natosit-dev/piqitt-contest

## Current working flow

Synthetic HL7 v2 ADT/ORU -> Python HL7-to-FHIR conversion -> PIQI evaluation -> PIQI Observation annotation -> IRIS custom REST API -> ^PIQITT storage -> Streamlit browser.

A separate IRIS interoperability production is also working for file-based HL7 ingestion:

ADT_File_Service -> ADT_Routing_Engine -> ADT_Archive.

## IRIS baseline

- InterSystems IRIS for Health Community 2026.1
- Container name: piqitt-iris
- Namespace: PIQITT
- Durable data root: /durable/iris
- Exchange mount: ./exchange:/exchange
- Web port: 52773
- SuperServer port: 1972

## Interoperability production

Business Service:
- Name: ADT_File_Service
- Class: EnsLib.HL7.Service.FileService
- File Path: /exchange/inbound/adt
- File Spec: *.hl7
- Archive Path: /exchange/archive/source/adt
- Target Config Names: ADT_Routing_Engine
- Message Schema Category: 2.5

Routing Engine:
- Name: ADT_Routing_Engine
- Class: EnsLib.HL7.MsgRouter.RoutingEngine
- Validation: dm-z
- Initial rule sends messages to ADT_Archive without transformation

Business Operation:
- Name: ADT_Archive
- Class: EnsLib.HL7.Operation.FileOperation
- File Path: /exchange/archive/routed/adt

## Custom IRIS REST layer

Class: PIQITT.REST.BundleService

Web application: /csp/piqitt/api

Routes:
- POST /bundle
- GET /bundle/{id}
- GET /bundles
- POST /wipe

Storage:
- ^PIQITT("bundle", id)
- ^PIQITT("idx", id)

The service stores complete annotated FHIR Bundles and extracts PIQI summary values for listing.

## Python baseline

Conda environment name: piqitt

Python: 3.10

Dependencies:
- requests>=2.31.0
- pyyaml>=6.0
- faker>=19.0.0
- streamlit>=1.30.0

## Synthetic data

One generated encounter produces an ADT and an ORU message.

Gender Harmony source fields intentionally use CWE. This is part of the intended HL7 design and should not be changed as cleanup.

Representative observations:
- 76691-5 Gender identity
- 90778-2 Personal pronouns
- SPCU Sex parameter for clinical use

## PIQI pipeline outputs

- out/fhir_bundles.ndjson
- out/fhir_bundles_annotated.ndjson
- out/piqi_scores.ndjson

A one-encounter test produced two FHIR Bundles, two PIQI scorecards, and two annotated Bundles.

Verified example results:
- PIQI index 0.7059, numerator 24, denominator 34, critical failures 0
- PIQI index 0.4286, numerator 3, denominator 7, critical failures 0

## Streamlit baseline

The UI supports:
- synthetic HL7 generation
- conversion and PIQI scoring
- posting annotated Bundles to IRIS
- listing stored Bundles
- fetching a full Bundle
- wiping demo data

## Baseline decisions

1. piqitt-contest is the source implementation for this baseline because it is cleaner than the older experimental repositories.
2. IRIS 2026.1 is the current container baseline.
3. The custom /csp/piqitt/api service remains the known-good persistence path.
4. Native IRIS FHIR R4 repository integration is deferred to the next phase.
5. CWE in source Gender Harmony OBX segments is intentional.
6. Credentials stay local and are not committed.
7. Provenance is stored under docs/.

## Next phase

Stand up a native IRIS FHIR R4 repository alongside the custom API, then decide how the interoperability production should invoke or enqueue FHIR conversion and PIQI evaluation without breaking the recovered contest workflow.
