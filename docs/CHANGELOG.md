# Shared-contract changelog

Every change to the shared contract (S-004) gets an entry here, newest first. Each entry says what changed and has one acknowledgement item per part. A part acknowledges by making the change, or by pinning the previous version with a reason, and then ticks its item with a note.

Versions: bundle schema `MAJOR.MINOR`; catalogue `vN`.

## 2026-09-25: a day without a result returns the latest earlier result (bundle schema 0.3, planned)

- When a player or seat orders a test on a day for which the case holds no value for a component, the engine returns the most recent earlier value of that component, marked with the day it was taken ("result from day 0"). A value with no day is valid throughout the admission. Only the days before a component's first value need their own value (Case Library SPEC §10.2).
- The Case Vault's coverage check and normal generator follow the same rule (migration `20260925140203_casevault_carry_forward.sql`, Case Library L0.9). Bundle rows are unchanged: a bundle simply holds fewer rows per component.

Acknowledgements:

- [ ] Nidana: the game server answers an order on a day without a value with the latest earlier value and shows its day.
- [ ] Sambhasha: the Gatekeeper does the same when it releases results to the Chart.

## 2026-09-25: catalogue v1 (Case Library L0.5)

- `case-library/catalogue/normal_templates.csv` gains a `review_status` column (`pending` or `approved`); the Case Vault loader takes it from the CSV, and the normal generator uses approved templates only.
- Test prices carry their source: `CGHS 2025, Tier I NABH (OM 03.10.2025)` where a CGHS rate matches, `reviewer` where Atul set it, and `estimate` otherwise. Sambhasha's `prices_inr.yaml` and `turnaround.yaml` are generated from these.
- The MCV formula check (`R.MCV`) tolerates 4% rather than 2%: analysers measure MCV and calculate the haematocrit, and published tables round both haematocrit and red cell count to two decimals (the pilot differs by 2.5% on days 5 and 6).
- Atul approved the catalogue review pack as a whole in chat on 2026-09-25, to be checked again before Nidana's production release. Claude filled the pack from that approval (`review/catalogue-v1/catalogue-review-v1.decided.xlsx`, not in Git): every reference range, price, turnaround and diagnosis code approved as proposed, and the 54 normal texts with an audit suggestion replaced by it. All 228 normal templates are approved.
- Prices: 190 tests take the CGHS NABH Tier I rate; 61 remain flagged estimates. Diagnosis codes: the proposed ICD-10 and ICD-11 codes, 15 of them corrected by the audit.
- Units and sources: urea's conventional unit is now `mg/dL` (factor 6.006, as Indian reports give "blood urea"), no longer BUN. Normal report components that cited Tietz now cite `Catalogue review, Dr Atul Tiwari (2026)`. HbA1c stays in % only; LOINC codes stay empty until a later version.
- Normal texts that depend on the patient (menstrual history, pelvic examination, pulse, ECG rate, postural blood pressure, height and weight, peak flow, capillary glucose) are neutral in v1; the curator writes them from the case's own sex and vital signs where they differ. The curator also records the blood group of every case. Past-infection serology: CMV and EBV IgG detected, IgM not detected, parvovirus IgG not detected.
- Four accepted suggestions carried authoring notes in player-visible text (ABO group, karyotype, pelvic ultrasound, vital signs); the notes were removed the same day, before any case used them, and a test now forbids them.
- Contents unchanged in size: 141 history questions, 68 examinations, 251 tests, 371 components, 116 actions, 19 referrals, 492 diagnoses, 60 findings.

Acknowledgements:

- [ ] Nidana: pin catalogue v1 once it is recorded here.
- [ ] Sambhasha: generate `configs/prices_inr.yaml` and `configs/turnaround.yaml` from the catalogue v1 export.

## 2026-09-25: bundle schema 0.3 and catalogue v0 (planned)

- Bundle schema 0.3, defined in `case-library/docs/SPEC.md` §10. It extends Sambhasha's schema 0.2 with catalogue links, origins, ledger tiers, report variants with provisional or final status, consult notes, licence flags, the case laboratory profile and gaps.
- Catalogue id patterns `HX`, `EX`, `LAB`, `IMG`, `PROC`, `CMP`, `RX`, `ACT`, `REF`, `DX` and `FND` (findings) (Case Library SPEC §5).
- Licence flags `production_ok` and `public_release_ok`, on every case and separately on every figure (S-006).
- Condition vocabulary for rubric anchors, must-do and must-not-do, including `finding_released` (Case Library SPEC §10.4).
- A bundle's SHA-256 is the hash of the exported file's bytes, kept in a `.sha256` file beside it (Case Library SPEC §10.5).
- Added in Case Library L0.3 (same version, still planned): the machine-readable schema `case-library/schemas/case-bundle.v0.3.schema.json`. It carries forward schema 0.2's `release_condition` on facts and `url` on the source, fixes the shape of `case.lab_profile`, and leaves curation provenance (generator, rationale, review fields) out of bundles (Case Library SPEC §10.2).
- Added in Case Library L0.4 (same version, still planned): catalogue v0 as CSV files in `case-library/catalogue/`, with their formats and rules in its `README.md`. Interpretive tests (films, imaging, endoscopy, marrow, histology) each carry one qualitative report component, `CMP.<TEST>_REPORT`, whose normal text is the reviewed normal report. Prices are all estimates until L0.5 matches them against the CGHS rate list; ICD-11 codes are unverified until L0.5. Catalogue v1, after Atul's review, gets its own entry. v0 holds 141 history questions, 68 examinations, 251 tests with 371 components, 116 actions, 19 referrals, 492 diagnoses and 60 findings; drug levels a person is not normally exposed to default to "Not detected".

Acknowledgements:

- [x] Nidana: designed against schema 0.3 (`nidana/docs/SPEC.md`).
- [ ] Sambhasha: move the domain models and the importer from schema 0.2 to 0.3 (Sambhasha PLAN P0.2 and P0.6); map Gatekeeper requests, and before scoring the Commit and each service report, to catalogue ids (D-022, P1.2 and P1.8).
