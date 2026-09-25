# Case PMC12007988: B12 deficiency disguised as thrombotic microangiopathy

Case id `PMC12007988` · Case version `PMC12007988@v1` · Status: **draft, curation steps 1–9 prepared locally, awaiting Case Reviewer verification** · Case Library task L1.3

> **Spoiler warning.** This file, the gold case file and everything in `curation/` contain the answer. They are for the Case Reviewer and for developers, never for a player or a seat.

Educational and research use only. Nothing here is clinical advice.

Files: [`gold-case-file.draft.json`](gold-case-file.draft.json) (facts in SI units) · [`curation/`](curation/) (paths, affected rows, rules, reports, consult notes, lay text, test utility, ground truth) · [`catalogue_needs.json`](catalogue_needs.json). Nothing has been written to the Case Vault; `uv run python -m scripts.case_replay cases/PMC12007988` replays it on the local database and reports **0 open problems**.

## Source

Manabe M, Inano N, Hagiwara Y, Koh KR. *Vitamin B12 Deficiency-Induced Massive Schistocytosis and Hemolytic Anemia Due to Pseudo-Thrombotic Microangiopathy: A Case Report.* Cureus 17(3): e80855. Published 19 Mar 2025. doi:[10.7759/cureus.80855](https://doi.org/10.7759/cureus.80855) · [PMC12007988](https://pmc.ncbi.nlm.nih.gov/articles/PMC12007988/) · PMID 40255844

- **Licence:** CC BY 4.0, read from the `<license>` element of the cached JATS XML (`data/articles/PMC12007988/jats.xml`) on 25 Sep 2026. `production_ok` and `public_release_ok` are true for the article and for each figure (no separate credit line in the captions).
- **Attribution to reuse:** "Adapted from Manabe M, Inano N, Hagiwara Y, Koh KR, Cureus 17(3): e80855 (2025), CC BY 4.0. Restructured into atomic facts; diagnosis redacted from player-facing text; simulated findings added where marked."
- **Setting:** Osaka, Japan. The article prints conventional units (g/dL, mg/dL, µg/dL, ng/mL, pg/mL); every value is converted to the catalogue's SI unit, with the printed value in the fact's `note`.

## The case in brief

A 37-year-old man was referred with a month of fatigue, loss of appetite and weight loss. He was pale and icteric, with no palpable nodes, liver or spleen and a normal neurological examination. No past history, no medicines. Not vegan or strictly vegetarian, but he ate meat or seafood only about once a month.

Hb 62 g/L, MCV 117.4 fL, reticulocytes 44.8 ×10⁹/L (3.07%), platelets 105, WBC 4.0, LDH 3115 U/L, bilirubin 39 µmol/L (conjugated 14), haptoglobin <0.10 g/L. DAT and antibody screen negative. Renal function and coagulation normal apart from a D-dimer of 1.80 mg/L. Iron 45.7 µmol/L, ferritin 722 µg/L. Film: marked schistocytosis, nucleated red cells with megaloblastic and dysplastic features, hypersegmented neutrophils; a small peak around 10 fL on the red cell histogram. PLASMIC score 5 (intermediate). The marrow, done to exclude cancer-related TMA, was hypercellular and megaloblastic with trilineage dysplasia and a normal karyotype.

Day 1: Hb 58 g/L, platelets 64. Transfused for severe exertional breathlessness, then intramuscular cyanocobalamin. ADAMTS13 considered but not sent. Serum B12 reported on day 4: 56 pmol/L (172–675; printed 76 pg/mL, 233–914). Discharged on day 7 (Hb 88, platelets 48, WBC 3.2, LDH 1353, bilirubin 19) with advice to eat meat. By five weeks everything had normalised. The authors attribute the deficiency to diet; intrinsic factor antibodies were never tested.

**Final diagnosis (ground truth):** `DX.B12_DEFICIENCY_ANAEMIA`, dietary vitamin B12 deficiency presenting as pseudo-thrombotic microangiopathy (ICD-10 D51.3).

## What the players start with

> A 37-year-old man is referred to hospital with a one-month history of fatigue, loss of appetite and weight loss. He has no relevant past medical history and takes no regular medicines.

Opening words: "I've been tired all the time for about a month. I've gone off my food and I've been losing weight." · Display title "Tired, off his food and losing weight" · slug `c-ov0b4` · tags haematology, internal medicine.

## Timeline

Day 0 is the first hospital day. The playable admission runs from day 0 to discharge on day 7 (engine days 0–7).

| Day | Article | Curator's additions (affected) |
| --- | --- | --- |
| 0 | Hb 62, MCV 117.4, retics 44.8 (3.07%), plt 105, WBC 4.0, NRBC 6/100, LDH 3115, bilirubin 39/14, haptoglobin <0.10, DAT/IAT negative, renal, coagulation, iron studies, B12 sample; film, histograms; marrow and karyotype (undated, filed on day 0) | RBC 1.46, HCT 0.17 (so MCH 42.5, MCHC 365), RDW 24.8, differential, IRF, LFT, electrolytes, folate, holoTC, MMA, homocysteine, ADAMTS13 64% |
| 1 | Hb 58, plt 64; severe exertional breathlessness; transfusion, then IM cyanocobalamin | Full count before transfusion; LDH 3240; bilirubin 41 |
| 2 | — | After two units: Hb 76, plt 58; retics 42; LDH 2860; K 3.6; B12 now >1476 pmol/L |
| 4 | B12 result reported | Hb 82, retics 150 (response), plt 52, LDH 2150, K 3.3 (low) |
| 7 | Hb 88, plt 48, WBC 3.2, LDH 1353, bilirubin 19; symptoms better; discharged | Retics 260, differential, K 3.8, schistocytes 3.0% |
| 35 | Follow-up (outside play): Hb 131 g/L, MCV 91.5, plt 219, WBC 10.2, LDH 211, B12 277 pmol/L; no schistocytes | Kept under `follow_up` and in the outcome only |

## Facts

- **Article:** 11 history, 5 examination, 34 laboratory rows (20 single results and 14 series points in 7 series). **Derived:** 1 (transferrin saturation 91%).
- **Hidden and conditional:** H09 (diet: meat or seafood about once a month) is released only by `HX.SOCIAL.DIET` or `HX.SOCIAL.VEGETARIAN` (or by a dietetics referral, whose note takes a diet history). H08 (no GI surgery) by past surgical history. H10 (severe breathlessness) from day 1; day 0 has a milder affected answer.
- **Raw material:** R01 film and R03 marrow (day 0), R02 analyser histograms (day 0, under the full blood count). R04 and R05 (five-week film and histograms) are `release: never`.
- **Media:** M01–M06 from Figures 1–4, all with `has_annotations: true` (arrowheads, circles or panel letters in every figure), licence flags true, files `PMC12007988/F<n>.jpg` to be downloaded later.

## Path analysis (curation/paths.json)

| Path | Kind | Why a player goes there | What the case shows |
| --- | --- | --- | --- |
| P1 Megaloblastic picture from the indices and film | efficient | High MCV, poor reticulocyte response, leucopenia, very high LDH; reviewed film | Megaloblastic nucleated red cells and hypersegmented neutrophils on review; diet history; B12 56 pmol/L |
| P2 TTP | trap | Haemolysis + thrombocytopenia + massive schistocytosis, PLASMIC 5 | No fever or neurology, normal creatinine, urine, troponin and clotting; ADAMTS13 64% after three days |
| P3 Myelodysplastic neoplasm | trap | Dysplastic NRBCs, dysplastic hypercellular marrow, pancytopenia | Normal karyotype, FISH, NGS and flow; no excess blasts; no ring sideroblasts |
| P4 Cancer-related microangiopathy | alternative | Weight loss, anorexia, MAHA in an adult | No nodes or organomegaly; imaging, tumour markers, endoscopy and trephine normal |
| P5 DIC or sepsis | alternative | Schistocytes, low platelets, raised D-dimer | Afebrile; CRP, procalcitonin, cultures, fibrinogen and PT normal |
| P6 Immune haemolysis, PNH, CTD | alternative | Haemolysis with cytopenias | DAT, antibody screen, PNH flow, ANA, complement normal |
| P7 Cause: pernicious anaemia or malabsorption | alternative | Once B12 is low | IF and parietal cell antibodies negative; coeliac, thyroid, H. pylori, stool and OGD normal; no surgery or drugs |
| P8 Folate or alcohol | alternative | Macrocytosis | Folate 24.6 nmol/L; light alcohol; GGT normal |
| P9 Neurological involvement | alternative | B12 myelopathy and neuropathy | No symptoms or signs; MRI and nerve studies normal |
| P10 Infection or travel | alternative | Indian player tests malaria, dengue, viruses | No travel, no fever, all negative |
| P11 Hypertensive or renal TMA | alternative | Schistocytes + thrombocytopenia | Normal BP and fundi, bland urine, normal kidneys |

Every catalogue item on a path is an article fact, an `affected` row or an authored report/note; everything else is `normal` or `rule`.

## Resolution counts (local replay, 25 Sep 2026)

- **Ledger:** affected 277 (257 authored + 20 calculated by the value rules: MCH, MCHC, MCV and reticulocyte % on days 1–7, anion gap, non-HDL), normal 1027, rule 7 (menstrual, obstetric, contraceptive, menopausal, vaginal and pregnancy history and pelvic examination: not applicable for a man), **reviewer 0**.
- **Judgement calls:** 19 (listed below).
- **Reports:** 21, all `only`/final (screening film, haematopathologist film review, marrow aspirate, trephine, iron stain, marrow flow, FISH, NGS, blood flow, 8 imaging, OGD, colonoscopy, NCS/EMG, malaria smear).
- **Consult notes:** 21: haematology (3 variants: no condition; after megaloblastic film or marrow findings; after the B12 result), dietetics, gastroenterology, neurology, nephrology, oncology, rheumatology, infectious diseases, cardiology (affected); 10 generic `rule` notes.
- **Test utility:** 94 tests (6 essential, 32 supportive, 44 low-yield, 12 unnecessary).
- **Checks:** consistency, contradiction, leak scan, placeholder scan and coverage clean.

## Curator's decisions

Atul delegated the open questions on 25 Sep 2026; the method answers are in `cases/BATCH1-CURATOR-ANSWERS.md`.

**Questions from the draft**

1. **Units (method):** converted to SI; printed values in each `note`. B12 reference range 172–675 pmol/L in `lab_profile` (article 233–914 pg/mL); all other ranges from the catalogue (the article gives none).
2. **Flags:** set against the catalogue's adult male ranges (Q2 proposed "flags as set"; now decided). The reticulocyte count 44.8 ×10⁹/L is flagged low (range 50–100), which is the point. D-dimer 1.80 mg/L FEU flagged high (FEU assumed).
3. **B12 day (method):** day 0 with the catalogue's turnaround.
4. **Marrow day (method):** day 0.
5. **DAT split (method):** IgG and C3d both negative.
6. **Day-35 values:** outcome only. They are not imported as facts, because any fact on day 35 would stretch the engine's days to 35 even with `release: never`; they sit under `follow_up` in the gold file and in the ground truth's outcome. R04 and R05 are `release: never`. The playable admission is days 0–7.
7. **Hypersegmented (method)**, not "hyperfragmented".
8. **Cause of the deficiency:** kept "look for the cause, including intrinsic factor antibodies" as a must-do. **G13 decided:** intrinsic factor and parietal cell antibodies both negative (affected, judgement call), following the authors' dietary conclusion and the normalisation of B12 with diet alone; OGD and gastric biopsies normal. No reviewer placeholder.
9. **Teaching trap:** only starting plasma exchange (or rituximab) is penalised; skipping ADAMTS13 is not a must-do. ADAMTS13 is supportive in test utility and a teaching point.
10. **Figures (method):** `has_annotations` true for all; to be confirmed when the files are downloaded.

**Values the article does not give**

11. **Red cell count and haematocrit (G15, judgement call):** RBC 1.46 ×10¹²/L is back-calculated from the article's reticulocyte count and percentage; HCT 0.17 from MCV × RBC. The value rules then give MCH 42.5 pg and **MCHC 365 g/L (high)**. That MCHC is unavoidable if the article's Hb, MCV and reticulocyte figures are all kept; it is plausible as an analyser artefact of massive fragmentation. Alternative: treat the 3.07% as the analyser's own figure and relax the reticulocyte % rule, which the catalogue does not allow.
12. **Course between day 1 and day 7 (G17):** two units transfused on day 1 (Hb 58 → 76 → 82 → 88), reticulocyte response from day 3–4 (150 on day 4, 260 on day 7), platelets 58 → 52 → 48, white count 3.8 → 3.2, LDH and bilirubin falling to the article's day-7 values, NRBC falling.
13. **Hypokalaemia on day 4 (judgement call):** K 3.3 mmol/L, a recognised effect of treating severe B12 deficiency; recovers by day 7.
14. **B12 after treatment (judgement call):** >1476 pmol/L from day 2, so a sample sent after the first injection is uninterpretable.
15. **ADAMTS13 (G12, judgement call):** 64% (normal), three-day turnaround (new catalogue test).
16. **Schistocyte count (judgement call):** 6.5% on day 0, 3.0% on day 7 (new catalogue test; the article gives no number).
17. **Screening film vs review:** the screening film (`LAB.HAEM.FILM`) reports fragments, nucleated red cells and macrocytes; only the haematopathologist review (`LAB.HAEM.FILM_REVIEW`) describes the megaloblastic nuclei and hypersegmented neutrophils, following the article's point that a thorough film review finds them. Both are final reports; the screening report's status line says a review can be requested.
18. **Other judgement calls:** weight loss about 4 kg (G02; weight 62 kg, height 170 cm); urine perhaps a little darker; a colleague noticed yellow eyes; light alcohol; never smoked; vital signs (pulse 104, BP 118/64, afebrile); soft flow murmur; IRF raised on day 0; plasma free Hb mildly raised; urine haemosiderin negative; soluble transferrin receptor raised; blood group A RhD positive (commonest group in Japan; not a judgement call).
19. **Patient-dependent normals (SKILL rule 9):** pulse, ECG rate (sinus tachycardia 102/min), postural BP (postural tachycardia without hypotension), height and weight written as affected; gynaecological items as `rule` "not applicable"; neutral templates replaced where they would contradict the case (syncope/light-headedness, impact on daily life, exercise, home described as a house, general appearance). EPO set high (850 IU/L) because the generator's normal value would be wrong.
20. **H03 and H04** no longer answer `HX.GI.NAUSEA_APPETITE` and `HX.GEN.FEVER_SWEATS_WEIGHT`; affected rows answer the whole question (no nausea or vomiting; no fevers or sweats; about 4 kg lost). H04's player text drops "Amount not recorded".
21. **Dietetics referral** releases the diet history in its note (a dietitian takes one), so it counts towards the diet must-do.

## Catalogue needs (catalogue_needs.json)

| Kind | New ids |
| --- | --- |
| Tests (5) | `LAB.HAEM.ADAMTS13`, `LAB.HAEM.FDP`, `LAB.HAEM.SCHISTOCYTE_COUNT`, `LAB.CHEM.MMA`, `LAB.CHEM.HOMOCYSTEINE` (all `price_source` estimate) |
| Components (5) | `CMP.ADAMTS13_ACT` (%), `CMP.FDP` (mg/L), `CMP.SCHISTOCYTE_PCT` (%), `CMP.MMA` (µmol/L), `CMP.HOMOCYSTEINE` (µmol/L) |
| Findings (3) | `FND.NUCLEATED_RED_CELLS`, `FND.CIRCULATING_MEGALOBLASTS`, `FND.GIANT_METAMYELOCYTES` (with `shown_by`) |

Gaps from the draft resolved without new items: no `DX` for pseudo-TMA (the final diagnosis is `DX.B12_DEFICIENCY_ANAEMIA`; `DX.MAHA_OTHER` stays the mimic); intramuscular cyanocobalamin is covered by `RX.VITAMIN.B12`; the analyser histograms stay raw material under the full blood count, with the number in the new schistocyte count.

## Ground truth summary

- **Rubric:** 5 B12 deficiency with H09 cited; 4 B12 deficiency; 3 pernicious anaemia, megaloblastic anaemia unspecified or mixed nutritional anaemia; 2 TTP, HUS/aHUS, other MAHA, DIC, MDS, folate deficiency, warm AIHA or cancer; default 1.
- **Must-do (8):** diet history; B12 (or holoTC) and folate; film review showing megaloblasts or hypersegmented neutrophils; cite MCV, reticulocytes or LDH as evidence; parenteral B12; look for the cause incl. IF antibodies; dietary advice or dietetics; repeat bloods.
- **Must-not-do (4):** plasma exchange or rituximab; MDS as the diagnosis; folic acid without B12; platelet transfusion without bleeding.

## Case Reviewer checklist

- [ ] Every article value and its SI conversion (notes carry the printed values); BUN → urea conversion (L08).
- [ ] The day-35 decision (outcome only, not imported) and the day 0–7 admission.
- [ ] RBC 1.46 / HCT 0.17 and the resulting MCHC of 365 g/L (decision 11).
- [ ] The day 1–7 course (decision 12), including the day-4 potassium and the post-treatment B12.
- [ ] Negative IF and parietal cell antibodies (decision 8) and ADAMTS13 64%.
- [ ] Screening film vs haematopathologist review wording (RP01, RP02) and the marrow report (RP03).
- [ ] Consult notes: CN01–CN03 are helpful but never name the diagnosis.
- [ ] Judgement calls (19) and `has_annotations` once the figures are downloaded.
- [ ] New catalogue items and their prices, turnarounds and ranges.
