# Shared-contract changelog

Every change to the shared contract (S-004) gets an entry here, newest first. Each entry says what changed and has one acknowledgement item per part. A part acknowledges by making the change, or by pinning the previous version with a reason, and then ticks its item with a note.

Versions: bundle schema `MAJOR.MINOR`; catalogue `vN`.

## 2026-09-26: notice: the Case Vault exports one layout for conditions; six bundles re-exported (no contract change)

- Follows the schema correction below (both fixes kept, Atul's decision). Migration `20260926173522_casevault_condition_shape` makes `export_bundle` write every `finding_released` condition as the list of finding ids with `from_tests` beside it, so bundles leave the Case Vault in one layout. Frozen rows and `bundle_rows` are unchanged, so every `frozen_hash` still reproduces.
- New revisions, catalogue version 2, recorded and published for development on Atul's instruction:
  - `PMC11227049@v1.r2` (replaces `r1`: one must-do)
  - `PMC11227436@v1.r2` (replaces `r1`: one consult note condition)
  - `PMC12007988@v1.r2` (replaces `r1`: one must-do)
  - `PMC12364935@v1.r2` (replaces `r1`: one must-do and three consult note conditions)
  - `PMC13193864@v1.r2` (replaces `r1`: one rubric anchor, which the schema leaves unchecked)
  - `PMC12949993@v1.r3` (replaces `r2`: the film-review must-do)
- Each new revision equals the one it replaces with only those conditions rewritten; the clinical content and the review records are unchanged. The other four cases re-export byte for byte. The old revisions stay valid (the schema accepts both layouts) and stay in `exports/` and `casevault.bundle`; engines should load the newest revision of each case.
- The Case Library's tests now check the newest bundle of every case against the whole schema, rubric anchors included.
- The shared contract is unchanged: no bundle, schema or catalogue version moves.

Acknowledgements:

- [x] Nidana: the engine's tests and the pilot's conformance playthrough load the newest revision of each case (`PMC12949993@v1.r3` for the pilot), and all pass; the game server will load the newest published revision (N1.4). Ticked 2026-09-26, N1.2.
- [x] Sambhasha: P0.2's bundle tests read the newest revision of each case, and all pass. Ticked 2026-09-26, P0.2.

## 2026-09-26: bundle schema 0.3 correction: `finding_released` also takes an object (Case Library L1.7)

- The condition `finding_released` now takes either a list of finding ids or an object `{"findings": [...], "from_tests": [...]}` (`from_tests` optional, no other keys). The curated cases have always used both forms, but the schema allowed only the list, so six exported bundles did not validate against their own schema: `PMC11227049@v1.r1`, `PMC11227436@v1.r1`, `PMC12007988@v1.r1`, `PMC12364935@v1.r1`, and the pilot `PMC12949993@v1.r1` and `.r2`. Nidana's contracts (N1.1) found this.
- A `from_tests` key beside `finding_released` in the same condition stays valid and means the same as the object's `from_tests`; no bundle uses it. Case Library SPEC §10.4 now shows both forms, and the case-curate consult note template shows the object form.
- The schema only widens, so no version moves: the schema stays `0.3` and no bundle, export or `.sha256` changes. Atul approved the fix without new bundle revisions. All eleven exports validate against the corrected schema (checked with Python `jsonschema`, with the format checker on).

Acknowledgements:

- [x] Nidana: regenerated `@nidana/contracts`; all 11 exported bundles validate (N1.1, 2026-09-26). The engine's condition evaluator (N1.3) will handle both forms and the sibling `from_tests` key.
- [x] Sambhasha: `Condition` accepts both forms and the sibling `from_tests` key; `finding_ids()` and `finding_tests()` give the Evaluator (P1.8) one answer for either. Every export parses, older revisions included. Ticked 2026-09-26, P0.2.

## 2026-09-26: notice: the repository is public, and every committed case is development-only (no contract change)

- The umbrella repository is public from 26 Sep 2026 (S-010, superseding S-005; `CLAUDE.md` rule 7). All ten committed cases and their eleven bundles, including their answers, are now public.
- Atul's decision: these cases are for building and testing the apps only. They never go into Nidana's store release, and never count as held-out or primary-result cases in a Sambhasha study. This supersedes the eligibility granted to the four Sambhasha starter cases in the item-by-item review notice below; their review still stands as a record.
- Production and study cases will be a new set, curated once the apps work and kept outside this repository.
- The shared contract is unchanged: no bundle, schema or catalogue version moves.

Acknowledgements:

- [x] Nidana: no action for development play; before the store release (Phase 4), load only cases from the new production set. Ticked 2026-09-26, U0.2.
- [x] Sambhasha: the importer (P0.6) marks every bundle it imports not eligible, with the reason S-010, and the primary analysis admits only eligible bundles (none today); the study will use the new private case set (PLAN Phase 2). Ticked 2026-09-26, P0.6.

## 2026-09-26: notice: Sambhasha's four starter cases are now reviewed item by item (no contract change)

- Atul reviewed four cases item by item in the Case Studio and confirmed every item as it stands, with no edits or rejections: `PMC11227049@v1`, `PMC11227436@v1`, `PMC11890614@v1` and `PMC12007988@v1`. The Case Vault records this as review batch `chat-2026-09-26-atul-itemwise-sambhasha-starters` (7,154 `approve` decisions by `atul`: every fact, live ledger row, report and consult note, and each ground truth).
- The frozen content did not change, so the published bundles `PMC11227049@v1.r1`, `PMC11227436@v1.r1`, `PMC11890614@v1.r1` and `PMC12007988@v1.r1` stand as they are, with the same SHA-256.
- These four bundles, and only these four, are now eligible for a Sambhasha study's primary results (invariant 1). This lifts the caveat of the bulk-approval notice below for these four only. The other five batch 1 bundles (`PMC11015937`, `PMC12364935`, `PMC12643702`, `PMC13193864`, `PMC13400839`) and the pilot (`PMC12949993@v1.r1` and `.r2`) are still bulk approvals and stay ineligible.
- The shared contract is unchanged: no bundle, schema or catalogue version moves.

Acknowledgements:

- [x] Nidana: no action needed (development play has no primary results). Ticked 2026-09-26, N1.1.
- [x] Sambhasha: superseded by the S-010 notice above before Sambhasha had a registry: all four stay not eligible. Ticked 2026-09-26, P0.6.

## 2026-09-26: notice: the ten published bundles were approved in bulk (no contract change)

- Every bundle the Case Vault has published so far was approved by Atul as a whole, not reviewed item by item: `PMC12949993@v1.r1` and `.r2` (the pilot), and the nine batch 1 bundles `PMC11015937@v1.r1`, `PMC11227049@v1.r1`, `PMC11227436@v1.r1`, `PMC11890614@v1.r1`, `PMC12007988@v1.r1`, `PMC12364935@v1.r1`, `PMC12643702@v1.r1`, `PMC13193864@v1.r1`, `PMC13400839@v1.r1`. Sambhasha's four starter cases are among the nine.
- The Case Vault records this on every row (review batches `chat-2026-09-25-atul-blanket`, `chat-2026-09-26-atul-blanket-batch1`, `chat-2026-09-26-atul-blanket-batch1-corrections` and `chat-2026-09-26-atul-blanket-pilot-r2`, each decision noted "not reviewed item by item"), but the bundles do not carry review notes, so this entry is how the other parts learn of it. Batch 1 also had an independent second review and corrections before its bundles were exported (Case Library PLAN L1.4).
- Invariant 1 applies: nothing unreviewed counts in a study's primary results. Until the Case Library records an item-by-item review of a case and announces it here, these cases must not count in a Sambhasha study's primary results. They may be used for development, pilot runs and secondary or exploratory analyses, labelled as such.
- The shared contract is unchanged: no bundle, schema or catalogue version moves.

Acknowledgements:

- [x] Nidana: no action needed (development play has no primary results). Ticked 2026-09-26, N1.1.
- [x] Sambhasha: the case registry has the flag and the primary analysis honours it; every imported bundle is not eligible (now for S-010). Ticked 2026-09-26, P0.6.

## 2026-09-25: catalogue v2 (Case Library L1.3, batch 1)

- Items the nine batch-1 cases need, proposed by each case's curator and merged by the lead curator (Claude), under Atul's instruction to decide on his behalf: 5 history questions, 1 examination, 51 tests, 16 actions, 1 referral (`REF.DENTISTRY`), 4 diagnoses, 14 findings, 63 components with 64 reference ranges, 3 value rules. Totals: history 146, exam 69, test 302, action 132, referral 20, diagnosis 496, finding 74, component 434. New prices are estimates; the 4 new diagnoses have unverified codes.
- The 7 new normal templates were approved by Atul in chat on 2026-09-25.
- Merge decisions: `LAB.HAEM.ADAMTS13` is activity only (`CMP.ADAMTS13_ACT`), with a separate `LAB.HAEM.ADAMTS13_INHIBITOR` (`CMP.ADAMTS13_ANTIBODY`); `CMP.SIL2R` is in U/mL (HLH-2004), and a case whose laboratory reports another unit states it in its `lab_profile`; `LAB.SERO.BRUCELLA` reports one agglutination titre (`CMP.BRUCELLA_SAT`); the synonym "CD55 CD59" moved from `LAB.HAEM.PNH_FLOW` to the new conventional `LAB.HAEM.PNH_CD55_CD59`.
- Value rules `R.GLOBULIN` and `R.AG_RATIO` chain (the ratio uses the calculated globulin), so the skill's normals step runs the formula pass twice.
- The published pilot resolves the new items without changing its frozen content (new ledger rows only), so it gets bundle revision `PMC12949993@v1.r2` once v2 is loaded.

Acknowledgements:

- [x] Nidana: pinned catalogue v2 in N1.1 (2026-09-26; `nidana/CLAUDE.md` and `@nidana/contracts`). `PMC12949993@v1.r2` is the pilot bundle Nidana uses; `.r1` is on catalogue v1 and the server will refuse it (N1.4).
- [x] Sambhasha: `sambhasha tables generate` writes both from the catalogue (pinned v2), and a test fails if they drift from `tests.csv`. Ticked 2026-09-27, P1.5.

## 2026-09-25: a day without a result returns the latest earlier result (bundle schema 0.3, planned)

- When a player or seat orders a test on a day for which the case holds no value for a component, the engine returns the most recent earlier value of that component, marked with the day it was taken ("result from day 0"). A value with no day is valid throughout the admission. Only the days before a component's first value need their own value (Case Library SPEC §10.2).
- The Case Vault's coverage check and normal generator follow the same rule (migration `20260925140203_casevault_carry_forward.sql`, Case Library L0.9). Bundle rows are unchanged: a bundle simply holds fewer rows per component.

Acknowledgements:

- [x] Nidana: the engine answers an order on a day without a value with the latest earlier value and marks its day (`requestedDay` and `day` on each release; N1.2, 2026-09-26). The player app shows the day (N1.5).
- [x] Sambhasha: the Gatekeeper (P1.3) returns the latest earlier value for a day without one and marks the line with its day ("result from day 6"); tested on the pilot. Ticked 2026-09-27, P1.3.

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

- [x] Nidana: superseded; Nidana pins catalogue v2 (see the catalogue v2 entry). Ticked 2026-09-26, N1.1.
- [x] Sambhasha: superseded by catalogue v2; generated from v2 (P1.5). Ticked 2026-09-27.

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
- [ ] Sambhasha: move the domain models and the importer from schema 0.2 to 0.3 (Sambhasha PLAN P0.2 and P0.6); map Gatekeeper requests, and before scoring the Commit and each service report, to catalogue ids (D-022, P1.2 and P1.8). Progress 2026-09-26: models (P0.2) and importer (P0.6) are on schema 0.3; the catalogue mapping (P1.2, P1.8) remains.
