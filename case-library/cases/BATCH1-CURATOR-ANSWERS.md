# Batch 1: the curator's answers to the starter cases' open questions

Task L1.3 · Case Library · 25 Sep 2026 · Claude (Case Curator)

> Spoiler warning: for the Case Reviewer and developers only. Educational and research use only; nothing here is clinical advice.

Atul asked Claude on 25 Sep 2026 to take the open decisions on his behalf and document them. The questions in each `cases/<PMCID>/CASE.md` fall into two kinds:

- **Method decisions** (how the curator records things). Claude decides these here, and they apply from the next curation run.
- **Reviewer decisions** (a value or a judgement that becomes part of the case). Claude only proposes these. Invariant 1 says nothing reaches a player unreviewed, and a curator approving its own values would defeat that, so each one stays open for Atul's case review (L1.4) and is marked **Proposed** below.

Curation of these cases resumes after the pilot review (SPEC §7.1), so nothing here has been written to the Case Vault.

## One decision for all four cases: units

**Decided.** Facts are converted to the catalogue's SI units at extraction, and the article's printed value and unit are kept in the fact's `note`, for example "printed 7.5 g/dL". The case's `lab_profile` gives ranges in SI. The player sees the case's display units, which the catalogue's `unit_conv` and `conv_factor` produce (Hb in g/dL, urea in mg/dL, as Indian reports read). This keeps the value rules (MCH, MCHC, TSAT, anion gap) valid and matches catalogue v1, where urea's conventional unit is now mg/dL.

This settles PMC11227049 Q1, PMC12007988 Q1, PMC11227436 Q1 and PMC11890614 Q3.

## PMC11227049

| Q | Kind | Answer |
| --- | --- | --- |
| 1 | Method | SI conversion (above) |
| 2 | Method | Keep the corrected units with notes. Urine lead: record as printed, flag it for review as a probable µg/L |
| 3 | Proposed | Keep iron and TIBC as printed, and leave TSAT unresolved with a `note`; the review decides whether one is a misprint |
| 4 | Proposed | Transcribe the table (done). G14 carries no cause; the raised enzymes stay as an unexplained finding |
| 5 | Proposed | MCV 80 fL from MCH/MCHC, origin `derived`, marked as a judgement call |
| 6 | Proposed | The generic toxin question does not release H15, as in the pilot |
| 7 | Method | The brand name stays out of anything a player sees |
| 8 | Method | Download the figures and check annotations at curation time (as for the pilot) |
| 9 | Proposed | Any appropriate chelator counts for must-do (BAL, d-penicillamine or succimer) |
| 10 | Method | Undated results stay on day 0; the clock runs for day 0 only |

## PMC12007988

| Q | Kind | Answer |
| --- | --- | --- |
| 1 | Method | SI conversion (above) |
| 2 | Proposed | Flags as set, for review |
| 3 | Method | B12 on day 0, with the real turnaround in play (the catalogue's turnaround applies) |
| 4 | Method | Marrow on day 0 |
| 5 | Method | Split DAT, as done |
| 6 | Proposed | Day-35 follow-up values `release: never` (outcome only), so the case stays within its admission |
| 7 | Method | Hypersegmented, as recorded |
| 8 | Proposed | Keep "look for the cause, including IF antibodies" as a must-do; G13 values are Atul's |
| 9 | Proposed | Penalise only starting plasma exchange, not skipping ADAMTS13 |
| 10 | Method | Check the figures at curation time |

## PMC11227436

| Q | Kind | Answer |
| --- | --- | --- |
| 1 | Method | SI conversion (above) |
| 2 | Method | µmol/L with a note, as done |
| 3 | Method | Use the catalogue's reticulocyte range; keep the printed threshold in the `note` |
| 4 | Proposed | "Positive" as an inference, marked as a judgement call |
| 5 | Proposed | Both `PROC.BM.ASPIRATE` and `PROC.BM.TREPHINE`, since the caption suggests a section |
| 6 | Proposed | Set G10 from the PT (INR raised, APTT and fibrinogen normal); values are Atul's |
| 7 | Method | Download and check the figures at curation time; flags stay false until then |
| 8 | Method | Replacement starts on day 1 of the case |
| 9 | Proposed | Yes, H07 may also answer the bleeding history question |
| 10 | Proposed | Leave jaundice for the examination |

## PMC11890614

| Q | Kind | Answer |
| --- | --- | --- |
| 1 | Method | Read Figure 5 to date the work-up at curation time; days from it are marked as the curator's reading |
| 2 | Proposed | Platelet range 139–361 ×10⁹/L, as a probable misprint |
| 3 | Method | SI conversion (above) |
| 4 | Proposed | Two scans (day 18 and day 29), as drafted |
| 5 | Proposed | Keep the vignette as drafted |
| 6 | Proposed | Both diagnosis ids, and keep D76.1 (the catalogue's code) |
| 7 | Proposed | Follow the authors: present from the start |
| 8 | Proposed | Yes, steroid without tuberculosis cover is a must-not-do |
| 9 | Method | Keep L04 on Xpert MTB/RIF until a generic PCR item exists |
