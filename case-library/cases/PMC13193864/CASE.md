# Case PMC13193864: dark urine, a positive DAT and kidneys that fail

Case id `PMC13193864` · Status: **draft, curation steps 1–9 done locally; replay clean (0 open problems); awaiting Case Reviewer verification** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json), [`curation/`](curation/), [`catalogue_needs.json`](catalogue_needs.json)

> Spoiler warning. This file and the JSON contain the answer. They are for the Case Reviewer and for developers. Never show them to a player or a seat. Educational and research use only; nothing here is clinical advice.

Drafted on 25 Sep 2026 for Case Library task L1.3 (batch 1, shortlist section 1 row 2). Nothing has been written to the Case Vault; the curation was replayed on the local database only (`uv run python -m scripts.case_replay cases/PMC13193864`, always rolled back).

## Source

Jiang L, Chen T, Xu L, Shi M, Huang W. *Paroxysmal nocturnal hemoglobinuria with a positive Coombs test presenting as acute kidney injury: a case report.* Frontiers in Medicine 13: 1778834. Published 8 May 2026. doi:[10.3389/fmed.2026.1778834](https://doi.org/10.3389/fmed.2026.1778834) · [PMC13193864](https://pmc.ncbi.nlm.nih.gov/articles/PMC13193864/) · PMID 42180722

- **Licence:** CC BY 4.0, verified (`cases/BATCH1.md`). `production_ok` and `public_release_ok` true. JATS cached at `data/articles/PMC13193864/efetch.jats.xml`, SHA-256 `67d86f5e…e731`. No figure-level credit line.
- **Setting:** Department of Nephrology, The First People's Hospital of Yongkang, Zhejiang, China.

## The case in brief

A 60-year-old woman had fatigue, anorexia, loose watery stools and dark tea-coloured urine after influenza A in February 2025. Outpatient tests showed mild anaemia, creatinine 123.7 µmol/L, bilirubin 76.4 µmol/L and LDH 1,868 U/L. She was admitted on 11 March. She was afebrile (BP 144/89, HR 86), pale, with mild bilateral pitting oedema. On 12 March her creatinine was 2,065 µmol/L, Hb 69 g/L, LDH 685 U/L and absolute reticulocytes 12.8 ×10⁹/L (low). Urine showed blood 2+ with few red cells. ADAMTS13 was 53.2%, CK 33 U/L, and ANA, anti-dsDNA and ANCA were negative. She was oliguric (200 mL over 13 h), so haemodialysis was started, and she received four units of washed red cells. On 13 March the DAT was positive for IgG and C3d, with no schistocytes on the film. The kidneys were enlarged, and the renal vessels were patent on Doppler. On further questioning she described recurring episodes of dark urine since 2016, each settling in 2–3 days; earlier evaluations had found no cause.

Her urine output recovered and dialysis stopped on 16 March. Her platelets fell from 233 to 98 ×10⁹/L by 18 March, and methylprednisolone was started empirically for possible AIHA on 19 March. After LMWH was started the platelets fell again, to a nadir of 45 on 24 and 26 March (Figure 1). The kidney biopsy (18 March, reported 20 March) showed haemoglobin cast nephropathy, tubular haemosiderin on Prussian blue and intrarenal venous thrombi. A leg vein ultrasound found a right iliac vein thrombosis, and a small perirenal haematoma from the biopsy was also seen. Prophylactic LMWH began on 23 March and rivaroxaban on 2 April. **Conventional CD55/CD59 flow cytometry on 24 March was normal.** Bone marrow flow showed partial loss of CD16 on granulocytes and CD14 on monocytes. **High-sensitivity FLAER flow cytometry on 28 March found a granulocyte clone of 98.46% and a red cell clone of 3.06%.** PIGA sequencing found c.548G>A (VAF 3.27%). She had meningococcal vaccination, then eculizumab from 21 April, and steroids were stopped. She went into haematological remission with renal recovery over 7 months.

## What the players start with

> A 60-year-old woman is admitted with tiredness and poor appetite that began after influenza A in February 2025. Outpatient blood tests suggested severe kidney impairment.

Opening words: *"Ever since I had the flu last month I've felt completely worn out, and I don't feel like eating. My doctor did some blood tests and said my kidneys aren't working properly, so they sent me in."*

Display title: "Tired and off her food after the flu, with failing kidneys". Tags: acute kidney injury, anaemia, fatigue. Specialty: nephrology. Slug `c-q7m2k`.

## Timeline (day 0 = 12 March 2025)

| Day | Event |
| --- | --- |
| before 0 | Influenza A (February); outpatient tests (H11) |
| 0 | Admitted (11 March, evening); Table 1 results; oliguria; haemodialysis; four units of washed red cells |
| 1 | DAT IgG and C3d positive; film without schistocytes; kidney ultrasound and renal Doppler (recorded on day 0 for the DAT, see decision 3) |
| 4 | Urine output 2,300 mL/day; dialysis stopped |
| 6 | Kidney biopsy (reported day 8) |
| 7 | Methylprednisolone started (platelets 109, Figure 1) |
| about 9 | Leg ultrasound: right iliac vein thrombosis; small perirenal haematoma |
| 11 | Prophylactic LMWH |
| 12 | Conventional CD55/CD59 flow cytometry normal (Table 2); platelet nadir 45 (Figure 1; again 45 on day 14) |
| not dated | Bone marrow flow cytometry (R06); PIGA sequencing (L60) |
| 16 | High-sensitivity FLAER flow cytometry (Table 3). The case's clock ends here |
| 21, 40 | Rivaroxaban; eculizumab after vaccination (ground truth only) |

## Facts

| Group | Ids | Count |
| --- | --- | --- |
| History | H01–H11 (3 in the vignette, 8 in the chart) | 11 |
| Examination | E01–E03, E04 (release `never`, documentation) | 4 |
| Laboratory, day 0 (Table 1, SI) | L01–L39 | 38 |
| Conventional flow, day 12 (Table 2) | L40–L43 | 4 |
| High-sensitivity flow, day 16 (Table 3) | L50, L51 (`reveals_dx`) | 2 |
| PIGA (undated, `reveals_dx`) | L60 | 1 |
| Series (Figure 1 read from the image) | S01 platelets (day 0 from Table 1, days 1–14), S02 Hb (days 1–14), S03 creatinine (days 1–14), S04 LDH (days 11–14) | 10 + 9 + 8 + 3 points |
| Raw material | R01 film, R02 kidney US, R03 renal Doppler, R04 biopsy, R05 leg US, R06 marrow flow, R07 FLAER | 7 |
| Figures | M01–M08 (F1; F2 A–D; F3; F4 A–B) | 8 |
| Gaps | G01–G09 | 9 |

In the replay (26 Sep 2026, after the Figure 1 reading): 91 article facts, 3 derived, 245 affected ledger rows (23 judgement calls), 1,979 normal, 2 rule, 0 reviewer; 18 reports (all final), 22 consult notes (7 affected, 15 rule).

## Hidden and conditional facts

- **H06 (pivotal):** recurring dark urine since 2016. Released only by `HX.PC.PREVIOUS_EPISODES` on a specific question; the urine colour question returns H05 (dark urine now) only.
- **L51 (pivotal, `reveals_dx`):** granulocyte clone 98.46% on the high-sensitivity test. L50, L51 and L60 are the confirmatory results and are excluded from the leak scan.

## Path analysis (summary)

| Path | Kind | What the case shows |
| --- | --- | --- |
| P1 Efficient | efficient | Dialysis; intravascular haemolysis with a low reticulocyte response; no fragments, ADAMTS13 53%, CK 33; biopsy; H06 on a specific question; high-sensitivity flow |
| P2 Warm AIHA | trap | DAT IgG + C3d; no spherocytes; eluate non-reactive; low reticulocytes |
| P3 Normal conventional CD55/CD59 | trap | Conventional assay normal whenever ordered; red cell acetylcholinesterase only slightly low; high-sensitivity result clearly positive |
| P4 TMA / HIT | alternative | No schistocytes, ADAMTS13 53%, stool culture negative, HIT antibody negative |
| P5 Rhabdomyolysis | alternative | CK 33, no urine myoglobin |
| P6 GN, lupus, vasculitis | alternative | Serology negative, anti-GBM negative, no red cell casts, normal glomeruli |
| P7 Myeloma cast nephropathy | alternative | No paraprotein, normal FLC ratio, low calcium, no light-chain restriction on biopsy |
| P8 Infection after influenza | alternative | Afebrile, PCT normal, cultures and tropical serology negative |
| P9 Marrow failure | alternative | Mildly hypocellular marrow, no dysplasia, normal cytogenetics and NGS |
| P10 Venous thrombosis | alternative | Iliac thrombus; thrombophilia, lupus anticoagulant and HIT negative; renal veins patent |
| P11 Gastrointestinal | alternative | Abdomen normal; stool culture negative |
| P12 Other effects of kidney failure | alternative | Raised osmolality, PTH and natriuretic peptides; tubular urine indices; low-normal HbA1c |

## Curator's decisions

Atul delegated these open questions (brief, 25 Sep 2026). Each is recorded here; the judgement calls lead the review pack.

1. **Clock.** Day 0 is 12 March (the first laboratory results), not 11 March (the evening admission), so that Table 1 is day 0. Vital signs and examination are placed on day 0.
2. **Outpatient results** (creatinine 123.7, bilirubin 76.4, LDH 1,868, "mild anaemia") are a history fact (H11), released by the referral letter or previous records, not lab facts on a negative day. The article gives no date.
3. **DAT.** Table 1 lists it with the admission results, but the text dates it to 13 March. It is recorded on day 0 (note on L25) so that a DAT ordered on admission has an answer.
4. **Platelet nadir.** Superseded on 26 Sep 2026 by Figure 1: the nadir of 45 is on 24 March (day 12) and again on 26 March (day 14), not on day 7 (109 on 19 March). The first draft's day-7 point is removed from S01.
5. **Serial values (G03).** Revised on 26 Sep 2026: Figure 1's labelled points were read from the image and added as article facts (series S01–S04, source_locator "Figure 1", note "read from the figure image"): platelets, Hb and creatinine on days 1, 4, 6, 7, 8, 11, (12), 13, 14 and LDH on days 11, 13, 14. The x-axis shows 18 March twice; the second 18 March point is not used. Points after day 16 (29 March onwards) are outside the case's clock and not added. The estimated rows these facts answer were removed. The remaining in-between days are affected values interpolated between figure points, no longer judgement calls (confidence 0.7): Hb and platelets on days 2 and 16; creatinine on days 2, 12 and 16; LDH on days 7, 12 and 16. Urea (not in the figure) and eGFR were recomputed to follow the figure's creatinine. Pre-admission values on 27 February (Hb 130, platelets 148, creatinine 123.7, LDH shown as 1,888 against 1,868 in the text) stay in H11 only.
6. **Units.** SI throughout, printed values in notes: BUN 65.9 mmol/L recorded as urea 65.9; uACR 235.0 → 26.6 mg/mmol; uPCR 558.19 → 63 mg/mmol; urine RBC 13.3/µL → 2/HPF and WBC 2.3/µL → 0/HPF (at about 5.5/µL per HPF); ferritin ng/mL = µg/L; PCT 0.051 → 0.05 µg/L (the catalogue's decimals). The case `lab_profile` carries the article's reference ranges in SI.
7. **Two flow cytometry tests.** The catalogue's `LAB.HAEM.PNH_FLOW` has FLAER clone-size components, so it stands for the high-sensitivity test (Table 3). A new test, `LAB.HAEM.PNH_CD55_CD59`, carries the conventional assay (Table 2). Both need day-0 answers (carry-forward starts at the first value):
   - conventional: 99.99% for all four populations (the authors blame the method, so it is normal whenever it is ordered);
   - high-sensitivity on day 0 (G08, **judgement call**): granulocytes 98.4%, red cells 7.8% (before transfusion). The monocyte clone of 97.9% (not reported) is used for every day.
8. **Transient jaundice** (HX.GEN.JAUNDICE, **judgement call**): the family noticed yellow eyes for a few days in February. This fits bilirubin 76.4 as an outpatient and 7.1 on admission.
9. **Painkillers** (HX.MEDS.OTC, **judgement call**): paracetamol only, during the flu. An NSAID would add an unsupported AKI red herring.
10. **Obstetric and transfusion history** (G09, **judgement call**): two pregnancies; no transfusion before this admission. This is an affected row, not a reviewer placeholder.
11. **Blood group** (G07, **judgement call**): group A, RhD positive.
12. **Eluate** (**judgement call**): non-reactive. The authors attribute the DAT to complement deposition, not an autoantibody.
13. **HIT antibody** (**judgement call**): negative. It is a fair question, because the platelets fell during dialysis with heparin.
14. **Urine casts** (**judgement call**): occasional pigmented granular casts, no red cell casts. **Urine haemosiderin:** positive, because the biopsy shows tubular haemosiderin (confidence 0.85, not a judgement call). **Plasma free Hb** 380 mg/L (**judgement call**).
15. **Bone marrow morphology** (G06): the article reports only an "evaluation" and marrow flow. Aspirate and trephine are written as mildly hypocellular with an inadequate erythroid response and no dysplasia. Karyotype, FISH and myeloid NGS are normal.
16. **Kidney biopsy report:** from the text and the Figure 2 caption. Added sentence (affected): immunofluorescence shows no glomerular deposits and no light-chain restriction in the casts, to answer the myeloma path.
17. **Leg ultrasound** reports the iliac thrombus whenever ordered. D-dimer 8.82 on day 0 supports the clot already being present. The post-biopsy perirenal haematoma is kept in the ground truth, not in any report, because reports are not dated.
18. **Other judgement calls:** flow murmur on auscultation; symmetrical calves; JVP; MCV 96 fL; IRF 7.5%; serum iron; EPO inappropriately low (26.5 IU/L); NT-proBNP 3,850 and troponin T 38 from AKI; HbA1c 4.1%; ESR 48; red cell acetylcholinesterase 25.1 U/g Hb (slightly low; GPI-anchored); influenza cough; previous admissions (H06's evaluations were outpatient).
19. **Patient-dependent normals (rule 9):** menstrual history, pregnancy and contraception written for a postmenopausal 60-year-old. Pulse is written from HR 86. The vital-signs fact has no respiratory rate or SpO₂ (G01).
20. **Consultants.** Nephrology: 2 variants (the second after `FND.HAEMOGLOBIN_CASTS`). Haematology: 3 variants (after the biopsy findings; after L51). Rheumatology and infectious diseases: 1 each. The other 15 specialties get rule notes. The first haematology note already suggests high-sensitivity flow among several tests, as a competent haematologist would. Notes use "PNH flow cytometry" and "PNH clone" only as the catalogue's test name and synonym, which the leak scan allows.
21. **Rubric:** 5 = DX.PNH with the biopsy (RP05 cited, or its findings released). 4 = DX.PNH. 3 = pigment nephropathy or ATN. 2 = AIHA, TMA (TTP, HUS, aHUS), rhabdomyolysis or aplastic anaemia. 1 = anything else. Steroids are **not** a must-not-do (the authors used them empirically). Escalating to rituximab, cytotoxics or splenectomy is.
22. **Figures.** The machine-generated alt texts in the JATS appear shifted by one figure: F1's alt describes the biopsy, F2's describes a table of marrow populations, and F3's describes the trend chart. At download, check which image file is which. All eight media rows have `has_annotations: true`, pending that check (F4's caption says it demonstrates the clone, so its plots are probably labelled). M01 (trend chart) shows treatment and outcome and has no raw material, so it is never shown to a player.

## Catalogue needs (`catalogue_needs.json`)

| Kind | New ids |
| --- | --- |
| History | `HX.PMH.THROMBOSIS` (with a normal template, `pending`) |
| Tests | `LAB.HAEM.ADAMTS13` (₹8,000 estimate, 3 days), `LAB.HAEM.PNH_CD55_CD59` (₹2,500 estimate, 1 day), `LAB.MOL.PIGA` (₹15,000 estimate, 7 days), `IMG.US.DOPPLER_RENAL` (₹1,500 estimate, 4 h) |
| Components | `CMP.ADAMTS13_ACT`, `CMP.CD55_RBC`, `CMP.CD59_RBC`, `CMP.CD55_NEUT`, `CMP.CD59_NEUT`, `CMP.PIGA_REPORT`, `CMP.DOPPLER_RENAL_REPORT` |
| Actions | `RX.COMPLEMENT.ECULIZUMAB`, `RX.VACCINE.MENINGOCOCCAL` |
| Findings | `FND.HAEMOGLOBIN_CASTS`, `FND.TUBULAR_HAEMOSIDERIN`, `FND.TUBULAR_NECROSIS`, `FND.INTRARENAL_VENOUS_THROMBI` (all `shown_by` `PROC.BIOPSY.KIDNEY`; the build document has no `shown_by` field, so add it in `findings.csv`) |

Notes for the lead curator:

- `LAB.HAEM.PNH_FLOW` lists "CD55 CD59" as a synonym. With the new conventional test, that synonym should move to `LAB.HAEM.PNH_CD55_CD59`, and `PNH_FLOW` could be renamed "High-sensitivity PNH flow cytometry (FLAER)".
- The shortlist suggested `HX.GU.DARK_URINE_EPISODES`, `LAB.HAEM.PNH_FLAER_HS`, `IMG.US.DOPPLER_LEG_VEINS` and `REF.VASCULAR`. They are not needed: `HX.PC.PREVIOUS_EPISODES`, `LAB.HAEM.PNH_FLOW` and `IMG.US.DOPPLER_LEGS` exist, and the article has no vascular consultation.
- Anticoagulation uses the existing `RX.CARDIO.ANTICOAGULATION` and `ACT.VTE_PROPHYLAXIS`.

## Case Reviewer checklist

- [ ] Every article fact (H01–H11, E01–E03, L01–L60, S01–S04) against the article and Figure 1; the SI conversions in the notes (decision 6).
- [ ] The clock and the DAT day (decisions 1, 3); the Figure 1 readings (decisions 4 and 5).
- [ ] The 23 judgement calls, most important first: the day-0 high-sensitivity result (7), the eluate (12), plasma free Hb and urine casts (14), transient jaundice (8), red cell acetylcholinesterase, HIT antibody (13).
- [ ] The marrow reports (15) and the added immunofluorescence sentence in the biopsy report (16).
- [ ] The consult notes, especially haematology V1: is suggesting high-sensitivity flow before the biopsy too helpful?
- [ ] The rubric and the must-do and must-not-do conditions (decision 21); whether starting steroids should be penalised.
- [ ] The figures after download: which file is which, annotations, and the licence flags (decision 22).
- [ ] The new catalogue items and their prices and ranges (all price_source `estimate`).

## Figure check (2026-09-26)

The images were downloaded from PMC and looked at one by one.

- M07 and M08 (Figure 4, FLAER flow plots) unlinked from the PNH flow result until masked: the plot headers appear to show the patient's name. Production decision: mask (crop the headers) or exclude.
- Figure 4B's header reads "+1" with a later date, so it looks like a second patient sample, not the "laboratory negative control" the article's caption states.
- M01 (Figure 1, timeline) names eculizumab and meningococcal vaccination; it has no link and stays debrief only.
- Figure 1 has labelled, dated values for creatinine, LDH, Hb and platelets. Those up to 26 March (day 14) were read from the image into series S01–S04 (decision 5). The chart also marks a negative DAT around April, after the case's clock. The x-axis repeats 20250318; the second point is ignored.
