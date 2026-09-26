# Case PMC11890614: miliary tuberculosis mistaken for sarcoidosis, then haemophagocytic lymphohistiocytosis

> Spoiler warning. This file, the JSON beside it and everything in `curation/` contain the answer. They are for the Case Reviewer and for developers, never for a player or a seat.

Case version `PMC11890614@v1` · Status: **curated locally (steps 1–9), awaiting Case Reviewer verification** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json) · Curation rows: [`curation/`](curation/)

Case Library task L1.3 (batch 1, Sambhasha starter case), 25 Sep 2026, Claude (Case Curator). Nothing has been written to the Case Vault. `uv run python -m scripts.case_replay cases/PMC11890614` replays the whole curation on the local database (rolled back) and reports **0 open problems**. Educational and research use only; nothing here is clinical advice.

## Source

Li W, Mann P, De La Hoz I, Constantakos A, Gordon D, Everett G, Maharam E. *A Perplexing Case Highlighting the Diagnostic Conundrum of Miliary Tuberculosis Mimicking Sarcoidosis and Progressing Into Hemophagocytic Lymphohistiocytosis.* Cureus 17(2): e78636. Published 6 Feb 2025. doi:[10.7759/cureus.78636](https://doi.org/10.7759/cureus.78636) · [PMC11890614](https://pmc.ncbi.nlm.nih.gov/articles/PMC11890614/) · PMID 40062127

- **Licence:** CC BY 4.0, read from the JATS `<license>` element of the cached XML (`data/articles/PMC11890614/jats.xml`, SHA-256 `0ebdccaf…63b565`). No figure carries its own permissions or credit line, so the article licence covers them: every figure's flags are set true (brief), `has_annotations` from the captions (panel letters on Figures 1, 3 and 4; Figure 2 has none in its caption, to be checked on the image).
- **Attribution to reuse:** "Adapted from Li W, Mann P, De La Hoz I, et al., Cureus 17(2): e78636 (2025), CC BY 4.0. Restructured into a simulation; diagnosis hidden until the debrief; simulated findings added where marked."
- **Setting:** AdventHealth, Orlando, USA.

## The case in brief

A 36-year-old man from Haiti, previously well, had four months of recurrent fever, dry cough, night sweats and weight loss. On admission he was febrile (39.0 °C) and tachycardic (115/min), with mild normocytic anaemia (Hb 99 g/L), raised inflammatory markers, ferritin 1364 µg/L and AST 63 U/L. HIV was negative. The chest X-ray and CT showed innumerable bilateral miliary nodules, and abdominal CT moderate splenomegaly.

The interferon-gamma release assay, repeated sputum AFB smears, MTB complex PCR and cultures, a bronchoalveolar lavage (smear and culture), and two sequencing tests (Karius cell-free DNA and MicroGenDX) were all negative. A transbronchial biopsy showed non-necrotising granulomas with a negative AFB stain. Fungal, other bacterial and viral tests were negative. Sarcoidosis was diagnosed by exclusion and high-dose steroid started. Fever continued; pancytopenia developed with rising ferritin and transaminases (day 17: Hb 68 g/L, WBC 0.03 ×10⁹/L, platelets 40 ×10⁹/L, ferritin 7821 µg/L, AST 335, ALT 325 U/L). The H-score was 256; sIL-2R 7593 ng/L and CXCL9 52 784 ng/L. The marrow showed non-caseating granulomas and occasional haemophagocytes, and he was given dexamethasone and etoposide (HLH-2004). On day 18 he developed hypoxic respiratory failure and shock. On day 25 repeat sequencing and a second lavage (AFB stain, PCR, later culture) found *Mycobacterium tuberculosis*. Four-drug treatment started and HLH chemotherapy was withheld, but he died about a week later. No autopsy.

## What the players start with

> A 36-year-old man, originally from Haiti and with no significant past medical history, presents to the emergency department with four months of recurrent fever and a dry cough. At triage his temperature is 39.0 °C and his heart rate 115 per minute.

Opening words: "I've had fevers on and off and a dry cough for about four months now, and they just won't go away."

Display title "Four months of fever and dry cough in a young man" · slug `c-c149v` · tags infectious disease, respiratory medicine, haematology, internal medicine · difficulty hard. Nothing is hidden behind a specific question: the difficulty is that the early tests are falsely reassuring.

## Timeline (day 0 = admission = hospital day 1)

The text dates only admission, day 17 (Table 1 "Day 18"), day 18 (hospital day 19), day 25 (hospital day 26, abstract) and day 29 (Figure 4b "day 30"). Figure 5, a timeline image, was not available, so the other days are **the curator's reading of the text**, marked in each fact's note. Each test fact's day is the day its sample was taken; a later request returns the latest earlier result.

| Day | Event | Dated by |
| --- | --- | --- |
| 0 | Admission; HIV, IGRA, three sputum samples (days 0–2: smear, PCR, culture), serum and urine fungal and other screens (cryptococcal and histoplasma antigen, galactomannan, brucella, JC virus); CXR, CT chest, CT abdomen | text order: "initial work-up" |
| 3 | First bronchoscopy: lavage (AFB smear, culture, PJP PCR) and transbronchial biopsy; Karius and MicroGenDX sent "concurrently" | curator |
| 7 | High-dose steroid for presumed sarcoidosis | curator |
| 10 | No improvement (C02) | curator |
| 13 | sIL-2R and CXCL9 | curator |
| 14 | Bone marrow; H-score 256 | curator |
| 15 | Dexamethasone and etoposide (HLH-2004) | curator |
| 17 | Table 1 values: Hb 68, WBC 0.03, ANC 0, platelets 40, ferritin 7821, AST 335, ALT 325 | article |
| 18 | Hypoxic respiratory failure, intubation, vasopressors; CT pulmonary angiogram; empirical antibiotics and antifungals | article |
| 25 | Repeat Karius and MicroGenDX positive; second lavage AFB and PCR positive; culture sent (grows later); four-drug treatment; HLH chemotherapy withheld | article |
| 29 | CT chest (Figure 4b): reticulonodular, flocculent and consolidative opacities | article |
| about 32 | Death | article ("one week later") |

## Facts

53 article facts: 7 history (H01–H07), 2 examination (E01–E02, now vignette facts), 7 course facts (C01–C07, never released), 7 series in SI (S01–S07: 14 values), 23 single results (L01–L23), plus 8 raw-material items (R01–R08) and 8 figures (M01–M08). Every converted value keeps its printed value in its note (for example "Printed 9.9 and 6.8 g/dL").

## Hidden and pivotal facts

No fact is hidden behind a specific question. L19–L23 (the positive sequencing, second lavage smear, PCR and culture) are `reveals_dx` and `pivotal`, all on day 25. Before day 25 every mycobacterial result, article or curated, is negative. Figure 5 (M08) names the diagnosis and is debrief-only.

## Path analysis (curation/paths.json)

| Path | Kind | What the case must show |
| --- | --- | --- |
| P1 Disseminated mycobacterial infection, sampled widely, treated empirically | efficient | every early test negative; non-necrotising granulomas; the day-25 positives |
| P2 Sarcoidosis | trap | random nodules without hilar nodes; no eye, skin or joint features; calcium normal; ACE only mildly raised; no response to steroid |
| P3 Haemophagocytosis treated without its trigger | trap | the inputs of an H-score of 256 on day 14; marrow granulomas; EBV negative |
| P4 Disseminated fungal infection | alternative | every fungal test negative; Grocott negative; no exposure |
| P5 Lymphoma or metastatic malignancy | alternative | no nodes or mass; polyclonal immunoglobulins; normal flow cytometry |
| P6 HIV and other causes of chronic fever | alternative | HIV negative, normal CD4 %, malaria, brucella, syphilis, viral tests negative; normal echo |
| P7 Deterioration on day 18 | alternative | no embolus; cultures negative; lactic acidosis, AKI, coagulopathy |
| P8 Meningeal or brain involvement | alternative | no meningism; normal CSF and MRI |
| P9 Liver involvement and nutrition | alternative | infiltrative liver tests; granulomas on biopsy; low albumin |

Resolution: 357 hand-written `affected` rows plus 29 calculated from them (MCV, MCH, MCHC, reticulocyte %, TSAT, anion gap, non-HDL; 386 in all), 7 `rule` rows (gynaecological items for a man), 3126 `normal` rows for everything off the paths, 0 `reviewer` rows. Values change over the course in day buckets 0, 7, 8, 13, 17, 18 and 25. 22 reports (all `only`, final), 25 consult notes (17 authored, 8 generic `rule`, including dentistry added at the catalogue merge), 6 lay texts, 88 test-utility ratings.

## Curator's decisions

Atul delegated the open questions on 25 Sep 2026. Each is recorded here; values the article does not anchor are `affected` rows flagged as judgement calls (36 in all), so they lead the review pack.

**The questions of the first draft (Batch 1 answers).**

1. **Undated work-up (Q1, method).** Dated from the text and figure captions only, since the Figure 5 image is not available (timeline above). The first lavage, sequencing and PJP PCR are dated day 3; because a request before day 3 must also resolve, day-0 `affected` rows carry the same negative results (reasoning: same patient, same low bacillary load).
2. **Platelet range (Q2).** "139-36" read as 139–361 ×10⁹/L, now in `lab_profile`.
3. **Units (Q3, method).** SI throughout; `lab_profile` in SI; the printed values in each fact's note. sIL-2R and CXCL9 in ng/L (numerically equal to pg/mL).
4. **Two scans (Q4).** Kept: the CT angiogram of day 18 (R04) and the CT chest of day 29 (R05). Reports carry no day in the Case Vault, so the stored CT chest report describes the admission scan; R05 stays as raw material for Sambhasha's services.
5. **Vignette (Q5).** Kept, with one change: the triage temperature and heart rate are added. The article's two vital signs (E01, E02) are now vignette facts, because the check forbids a ledger row on an item an article fact already answers, and the full vital signs (with the curated blood pressure, respiratory rate and saturation) are one `EX.GEN.VITALS` row.
6. **Final diagnosis (Q6).** Both ids (`DX.MILIARY_TB`, `DX.HLH`) for the leak scan; ICD-10 D76.1 kept (the catalogue's code).
7. **Reverse causation (Q7).** The case follows the authors: tuberculosis was present from the start.
8. **Steroid without cover (Q8).** A must-not-do, with a condition (any high-dose steroid, prednisolone or dexamethasone in the plan without `RX.ANTITB.FIRST_LINE`).
9. **L04 (Q9, method).** Kept on Xpert MTB/RIF (`CMP.XPERT_MTB_RIF`); no generic sputum PCR item is proposed.

**Gaps the first draft left to the reviewer, now decided.**

10. **G14 urine, G15 marrow, G16 liver (not auto-generated before).** All negative for mycobacteria within the case: smears and stains negative, PCR not detected, cultures "no growth to date" (they would read out after the case ends). Reason: every early sample in the article was negative, so the bacillary load was low. Marrow PCR (confidence 0.45) is the closest call and is marked high priority. The liver biopsy shows non-necrotising granulomas.
11. **G21 dates.** As in the timeline.
12. **G11 H-score inputs.** Chosen so the H-score is exactly 256 on day 14: temperature 38.9 °C (33), splenomegaly without hepatomegaly (23), three cytopenias (34), ferritin 6400 µg/L on day 13 (50), triglycerides 3.4 mmol/L (44), fibrinogen 3.2 g/L (0), AST ≥30 (19), marrow haemophagocytes (35), on high-dose steroid (18).
13. **G04 fundoscopy.** No choroidal lesions (skill rule 2: no invented near-pathognomonic sign).
14. **G17 CNS.** Normal CSF and MRI; headache only with fevers.
15. **G05 contacts and migration.** No known contact; came from Haiti about four years ago; lives with his wife and her sister; BCG in childhood.
16. **G06, G07 social history and medicines.** Warehouse worker; no animal, bird or cave exposure; no antibiotics or regular medicines (paracetamol only). No recent fluoroquinolone is invented, although one would explain the negative early tests.
17. **G13 blood cultures.** Negative on day 0 and day 18; mycobacterial blood culture no growth to date.
18. **Blood group.** O RhD positive (the commonest group in people of Haitian origin).
19. **sIL-2R and CXCL9 on admission.** Raised (2450 and 3800 ng/L) by the infection itself, far below the day-13 values.
20. **Serum ACE.** Mildly raised (74 U/L), a non-specific rise that keeps the sarcoidosis trap open.
21. **First-lavage PCR.** Not reported; set "not detected" on day 3 (and day 0), consistent with the same fluid's negative smear, culture and sequencing.
22. **Weight.** 62 kg, BMI 19.6, about 10 kg lost (the article gives no amount).
23. **Leak rule in reports and notes.** The article's radiology impression named the infection; the stored reports give the radiologist's differential instead, and consult notes say "disseminated mycobacterial infection" until the day-25 results. The sick-contacts answer says "TB" because the question itself asks about it.
24. **Reviewer rows.** None: no value here must be left to Atul.
25. **After the lead curator's catalogue merge.** Brucella serology is now the standard agglutination test (`CMP.BRUCELLA_SAT`): L14 reads "titre less than 1:80". `CMP.SIL2R` is now in U/mL in the catalogue; the case keeps the reporting laboratory's ng/L values and range (175.3–858.2) in its `lab_profile`, because the two units are assay-dependent and have no fixed conversion.

**Known limits.** Reports have no day, so marrow, film and imaging reports read the same whenever they are requested (the marrow report shows haemophagocytes even if a player asks on day 2). A repeat lavage requested between days 3 and 24 returns the day-3 negative result.

## Ground truth (curation/ground_truth.json)

Final diagnosis `DX.MILIARY_TB` (A19.9); secondary haemophagocytic lymphohistiocytosis (`DX.HLH`, D76.1) is a secondary finding scored through the rubric (see the corrections below). Rubric: 5 miliary TB with HLH evidence cited (sIL-2R, CXCL9, day-17 ferritin or Hb, marrow report); 4 miliary, pulmonary or drug-resistant TB, or HLH with a positive TB result cited; 3 disseminated NTM or histoplasmosis; 2 sarcoidosis, lymphoma or HLH without its trigger; 1 anything else. Seven must-dos (keep TB high; empirical treatment before or with steroid; sample more than one site; recognise haemophagocytosis; isolate and involve infectious diseases; HIV test; notify public health) and three must-not-dos (steroid without cover; etoposide or escalated immunosuppression without treating the trigger; commit to sarcoidosis), each with a condition over catalogue ids.

## Catalogue needs (merged into catalogue/*.csv by the lead curator)

19 new tests (all `price_source` "estimate"), 24 new components, 2 findings, 1 action, 2 diagnoses:

- **Mycobacterial tests:** sputum mycobacterial culture; BAL panel (AFB smear, MTB PCR, culture); bone marrow panel (AFB stain, MTB PCR, culture); urine AFB and culture; mycobacterial blood culture.
- **Sequencing:** plasma microbial cell-free DNA (Karius); pathogen NGS on fluid or tissue (MicroGenDX).
- **Haemophagocytosis markers:** soluble IL-2 receptor (catalogue now U/mL, Tietz range; the case keeps ng/L in its lab profile); CXCL9 (the reporting laboratory's range as printed in the article).
- **Fungal and other:** cryptococcal antigen, histoplasma antigen, galactomannan, beta-D-glucan, Pneumocystis PCR, brucella serology (now the standard agglutination test, `CMP.BRUCELLA_SAT`), JC virus PCR, EBV DNA PCR, serum ACE.
- **Procedure:** transbronchial lung biopsy (`PROC.BIOPSY.LUNG`, with a normal report text).
- **Findings:** `FND.MILIARY_NODULES`, `FND.HAEMOPHAGOCYTOSIS`. **Action:** `RX.IMMUNO.ETOPOSIDE`. **Diagnoses:** `DX.DISSEMINATED_HISTOPLASMOSIS` (B39.3), `DX.DISSEMINATED_NTM` (A31.8), ICD-11 codes left for the code check.

## Case Reviewer checklist

- [ ] Every value in `series` and `single_results` matches Table 1 and the text; SI conversions correct
- [ ] Day mapping (day 0 = hospital day 1) and the curator's dates of the undated work-up agree with Figure 5
- [ ] The vignette (with triage vitals) and opening words reveal nothing diagnostic
- [ ] R01–R08 faithful; reports RP01–RP22 add nothing more diagnostic than real life
- [ ] Figure flags and `has_annotations` checked on the images; Figure 5 kept out of play
- [ ] The 36 judgement calls, first the marrow, urine and blood mycobacterial results (G14, G15) and the H-score inputs (G11)
- [ ] Consult notes: helpful, never more diagnostic than a colleague with the same Chart
- [ ] Ground truth, rubric, must-do and must-not-do agreed
- [ ] Catalogue needs merged with the other batch-1 cases (sIL-2R and CXCL9 ranges, prices, ICD-11 codes)

## Figure check (2026-09-26)

The images were downloaded from PMC and looked at one by one.

- M03: `has_annotations` set to true (one arrow).
- M08 (Figure 5, the timeline) names the diagnosis and the treatment; it stays unlinked and is debrief only.

## Corrections after the second review (2026-09-26)

The case was approved in bulk, then a second expert review found four problems. The corrections below are in the curation files and supersede the approved rows once Atul accepts them; ids are unchanged and every (target, day) with a ledger value still has one.

1. **Final-diagnosis ids (medium).** `ground_truth.json` `final_dx.ids` (and its twin `final_diagnosis.ids`): `["DX.MILIARY_TB", "DX.HLH"]` -> `["DX.MILIARY_TB"]`. Reason: if ids drive top-1 accuracy, an answer of HLH alone would count as correct, while the rubric scores "HLH without its trigger" at 2. The schema has no field for a secondary diagnosis id (other cases use `secondary_findings` text), so HLH stays in `secondary_findings` (now naming `DX.HLH` and D76.1 and saying it is scored through the rubric) and in the rubric anchors 5, 4 and 2. With it: `icd10` `["A19.9", "D76.1"]` -> `["A19.9"]` (the same top-1 reasoning); "secondary HLH" removed from `accepted_synonyms` (it names HLH without its trigger; the synonyms naming tuberculosis as the trigger stay); and a new `leak_terms` list (haemophagocytic and hemophagocytic lymphohistiocytosis, HLH, secondary HLH, haemophagocytic syndrome, macrophage activation syndrome) so the leak scan still covers every term it took from `DX.HLH` before. This replaces decision 6.
2. **Prothrombin activity (high, batch-wide).** `affected.json`: 26 new `CMP.PT_ACTIVITY` rows, days 0 to 25, replacing the independent `normal` values (80-109%) on the same days. Each follows the INR in effect that day (the latest curated INR on or before it) through the Case Library's common curve, activity % = round(100 x 0.59 / (INR - 1 + 0.59)), capped at 100: INR 1.15 -> 80% (days 0-12), 1.20 -> 75% (days 13-16), 1.30 -> 66% L (day 17), 1.45 -> 57% L (days 18-24), 1.60 -> 50% L (day 25). Range 70-120 (catalogue). Not judgement calls: the values follow from the approved INR rows by the curve. Hand-written `affected` rows 357 -> 383; the replay now counts 427 `affected`, 3667 `normal` and 7 `rule` ledger rows (26 more `affected`, 26 fewer `normal`).
3. **Must-do "anti-tuberculosis treatment before or with any steroid" (low).** `ground_truth.json` `must_do[1].if`: `not plan_before [RX.STEROID.*, RX.ANTITB.FIRST_LINE]` added as a third alternative beside `plan_before [RX.ANTITB.FIRST_LINE, RX.STEROID.*]`. SPEC §10.4 already defines `plan_before` as "before or together with", so the old condition matched the text under the SPEC; the added branch makes a simultaneous start pass even if an engine reads `plan_before` strictly (under the strict reading "steroid strictly before anti-TB" is false, so its negation holds), while a steroid planned first still fails under both readings. Only forms the ground truth already uses (`any`, `not`, `plan_before`). No evaluator exists in the repository yet to test it against.
4. **Film reports RP12 and RP13 (low).** Reports have no day in the Case Vault (no day column in `casevault.report`), so they cannot be given one without a schema change; they are reworded to fit every day they can be released on instead. `reports.json` RP12 (`LAB.HAEM.FILM`): "White cells reduced in number with lymphopenia ... Platelets adequate" -> lymphocytes reduced, neutrophils (where present) normal, platelets normal in appearance, "White cell and platelet numbers as in the accompanying full blood count"; impression now defers the counts to the blood count. RP13 (`LAB.HAEM.FILM_REVIEW`): "Platelets normal in number and appearance" -> "Platelets normal in appearance; their number as in the accompanying full blood count", and "Neutrophils, where present, without dysplasia". Reason: the white cell count is normal on day 0 (4.5) and platelets fall to 40 by day 17, so any count statement is wrong on some days; the morphology described (normocytic anaemia, rouleaux, lymphopenia, no dysplasia, no circulating haemophagocytes) holds throughout.

Not changed: the gold case file's own `ground_truth` copy still carries the old ids and condition; the replay and the patch use `curation/ground_truth.json`, which replaces it on import.
