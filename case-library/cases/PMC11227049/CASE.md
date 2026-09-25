# Case PMC11227049: an Indian sibling of the pilot

Case id `PMC11227049` · Case version `PMC11227049@v1` · Status: **draft, curation steps 1–9 prepared; replay clean (0 open problems); awaiting the Case Reviewer** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json), [`curation/`](curation/), [`catalogue_needs.json`](catalogue_needs.json)

> Spoiler warning. This file, the JSON and `curation/` contain the answer. They are for the Case Reviewer and for developers. Never show them to a player or a seat.

Prepared on 25 Sep 2026 for Case Library task L1.3 (batch 1). Educational and research use only; nothing here is clinical advice. Atul delegated the open questions to the curator; every decision is recorded under **Curator's decisions** below and stays open for his case review (L1.4). Nothing has been written to the Case Vault: the replay (`uv run python -m scripts.case_replay cases/PMC11227049`) runs every step on the local database and rolls back.

## Source

Thomas J, Sebastian R, Anil Kumar CR, Rafi AM. *Case of lead poisoning secondary to intake of herbal medicine for diabetes mellitus in a tertiary care hospital in Kerala.* Endocrinology, Diabetes & Metabolism Case Reports 2024(2): 23-0066. Published 10 Jun 2024. doi:[10.1530/EDM-23-0066](https://doi.org/10.1530/EDM-23-0066) · [PMC11227049](https://pmc.ncbi.nlm.nih.gov/articles/PMC11227049/) · PMID 38866062

- **Licence:** CC BY 4.0 (read from the `<license>` element of the cached JATS XML, `data/articles/PMC11227049/jats.xml`, SHA-256 `671ee106…79e2`). `production_ok` and `public_release_ok` are both true, for the case and for each figure (the captions carry no separate credit line).
- **Attribution:** "Adapted from Thomas J, Sebastian R, Anil Kumar CR, Rafi AM, Endocrinol Diabetes Metab Case Rep 2024(2): 23-0066 (2024), CC BY 4.0. Restructured into a simulation; diagnosis hidden until the debrief; simulated findings added where marked."
- **Setting:** Jubilee Mission Medical College, Thrissur, Kerala, India.

## The case in brief

A 58-year-old woman with type 2 diabetes and hypothyroidism had two weeks of generalised tiredness, reduced food intake and abdominal pain after eating. She had stopped metformin two months earlier and was on thyroxine. She was pale, with desquamation of the tongue and oral mucosa. Her vital signs and systemic examination were normal. Hb 75 g/L (7.5 g/dL), MCH 25.7 pg, RDW 15.3%, reticulocytes 7.94%. AST 139, ALT 146 and ALP 156 U/L, bilirubin 24 µmol/L (direct 2). Serum iron 32.6 µmol/L (182 µg/dL), ferritin 264 µg/L, HbA1c 9%.

A careful look at the film showed coarse basophilic stippling, normoblasts and polychromasia. The marrow showed erythroid hyperplasia and many ring sideroblasts, and its report raised both an acquired sideroblastic anaemia (lead or zinc) and MDS with ring sideroblasts. The team then asked her again about heavy-metal exposure. She disclosed an Ayurvedic diabetes capsule she had bought online, taken for 1.5 months and stopped before admission. Blood lead 121.2 µg/dL (reference <25) and random urine lead 400.2 µg/L (reference <80); blood zinc normal. The capsules contained 40 657 ppm of lead. She was treated with BAL and then oral d-penicillamine for six weeks. Hb 101 g/L at discharge; blood and urine lead normal at follow-up.

## What the players start with

> A 58-year-old woman with type 2 diabetes and hypothyroidism presents with two weeks of generalised tiredness, reduced food intake and abdominal pain after eating.

Opening words: *"For the last two weeks I have been tired all the time and I have not been eating much. My stomach hurts after I eat."*

Display title: "Tired, off her food, with pain after meals". Tags: anaemia, abdominal pain, diabetes. Slug `c-tegc9`.

## Timeline in the article

Day 0 is presentation to the out-patient department and admission. The article gives no calendar dates.

| Day | Event |
| --- | --- |
| About −60 | Metformin stopped |
| About −45 to shortly before admission | Herbal capsules taken for about 1.5 months, then stopped |
| −14 | Tiredness, reduced food intake and post-prandial abdominal pain begin |
| 0 | Admission. Examination; Table 1 (blood count, reticulocytes, renal, liver, iron, glucose, HbA1c, thyroid) |
| Not dated | Film examined carefully; marrow and iron stain; history revisited and capsules disclosed; blood and urine lead, blood zinc; ultrasound abdomen normal; capsules analysed; BAL, then d-penicillamine |
| Discharge (not dated) | Hb 101 g/L |
| About six weeks of d-penicillamine | Blood and urine lead normal; film shows mild normocytic normochromic anaemia only |

Every undated result is available whenever it is ordered during the admission (`day: null`); the case clock runs for day 0 only (decision D13). The outcome values (O01–O03) are `release: never`, for the debrief only.

## Facts

All values are in the catalogue's SI units; each converted fact keeps the printed value and unit in its `note`.

| Group | Ids | Count |
| --- | --- | --- |
| History | H01–H16 (6 in the vignette, 10 in the chart) | 16 |
| Examination | E01–E13 | 13 |
| Laboratory, day 0 | L01–L31 (L25 held back, decision D3) | 31 |
| Lead, zinc and product | L32–L35 | 4 |
| Outcome (never released) | O01–O03 | 3 |
| Raw material | R01 film, R02 marrow aspirate, R03 iron stain, R04 ultrasound | 4 |
| Figures | M01 (Figure 1), M02 (Figure 2) | 2 |
| Gaps | G01–G20 (all resolved in `curation/affected.json`) | 20 |

## Hidden and conditional facts

| Fact | Released when |
| --- | --- |
| H15 "She had been taking herbal capsules for her diabetes, bought over the internet, for about one and a half months, and stopped them before admission." | Only on a specific question about supplements, herbal, Ayurvedic or traditional remedies, or remedies bought online (`HX.MEDS.SUPPLEMENTS`, `HX.MEDS.SUPPLEMENT_DETAILS`) |
| H16 Product details (Ayurvedic diabetes capsule, bought online, 1.5 months) | `HX.MEDS.SUPPLEMENT_DETAILS` |
| L35 Lead content of the capsules | `ACT.TEST_PRODUCT` (the product is sent for analysis) |

The general medication question returns metformin (stopped) and thyroxine only. The generic toxin question (D6) and the over-the-counter question (D7) do not release H15. The endocrinology and toxicology consultants, like a competent colleague, advise asking what she has used for her diabetes since stopping metformin.

## Raw material and reports

| Id | Test | Raw findings | Report |
| --- | --- | --- | --- |
| R01 | Peripheral blood film (day 0) | Normocytic normochromic anaemia. Coarse basophilic stippling. Normoblasts. Polychromasia. | RP01 screening film and RP02 haematopathologist review, both final (D1) |
| R02 | Bone marrow aspirate | Erythroid hyperplasia. | RP03, with mild dyserythropoiesis (D8) |
| R03 | Bone marrow iron stain (Perls) | Many ring sideroblasts. | RP04, about 30% of erythroblasts, stores increased, differential in the comment (D8) |
| R04 | Ultrasound abdomen | No abnormality. | RP10, normal organ by organ |

Other reports, not in the article (all `affected`): trephine, marrow flow, karyotype, MDS FISH, myeloid NGS (all normal apart from erythroid hyperplasia), abdominal X-ray, CT abdomen and pelvis, upper GI endoscopy (mild non-specific antral gastritis) and colonoscopy. 14 reports in all.

## Ground truth

**Final diagnosis:** lead poisoning from an Ayurvedic herbal diabetes capsule bought online (`DX.LEAD_POISONING`, T56.0, with D64.2). The leak scan also covers `leak_terms` for the traditional-medicine diagnosis (D16).

**Treatment given:** the capsules were stopped; BAL, then oral d-penicillamine for six weeks; the capsules went to the state drug analyst.

`curation/ground_truth.json` holds the rubric (5 lead with the capsules cited as evidence H15; 4 lead; 3 other or unspecified metal, traditional-medicine metal toxicity or toxic sideroblastic anaemia; 2 MDS-RS, haemolysis, thalassaemia trait, nutritional anaemia, acute porphyria or drug-induced liver injury; 1 otherwise), eight must-do and four must-not-do items, each as text plus a condition over catalogue ids (SPEC §10.4).

## Path analysis (`curation/paths.json`)

| Path | Kind | What the case must show |
| --- | --- | --- |
| P1 Efficient | efficient | Film shows stippling; H15 only on a specific remedy question; blood lead 121.2 µg/dL |
| P2 Myelodysplasia with ring sideroblasts | trap | Mild dyserythropoiesis only; normal karyotype, FISH and NGS; copper, B6 and zinc normal; no alcohol |
| P3 Haemolytic anaemia | trap | DAT negative; LDH moderately raised; haptoglobin low-normal; no spherocytes; no haemoglobinuria |
| P4 Liver disease | alternative | Viral and autoimmune markers negative; PT normal; ultrasound normal; enzymes unexplained |
| P5 Nutritional anaemia | alternative | B12 low-normal, active B12 and folate normal; no intrinsic factor antibodies |
| P6 Upper GI cause | alternative | Lipase normal; H. pylori negative; imaging normal; endoscopy non-specific |
| P7 Acute porphyria | alternative | PBG not in the acute range; ALA and coproporphyrin raised; faecal porphyrins normal |
| P8 Thalassaemia trait or enzyme disorder | alternative | HPLC normal; G6PD normal; P5N low because lead inhibits it |
| P9 Diabetes or thyroid disease | alternative | Thyroid normal on thyroxine; neither explains the anaemia |
| P10 Other metals in the remedy | alternative | Mercury, arsenic and cadmium within limits (D9) |
| P11 Blood loss | alternative | Postmenopausal, no bleeding, FIT negative, colonoscopy normal |

Consult notes: haematology (three variants: none, after stippling, after the blood lead), toxicology (two: none, after the blood lead), gastroenterology and endocrinology (one each), all `affected`; 15 off-path specialties carry the catalogue's generic note as `rule` rows. Test utility is set for all 66 tests on the paths.

## Curator's decisions

Atul delegated these on 25 Sep 2026. Each one is the curator's; each stays open for the case review.

| # | Question | Decision |
| --- | --- | --- |
| D1 | First film report? | The article describes one "careful examination" of the film and no earlier report that missed the stippling, so the screening film (RP01) carries all the article's findings and is final; the haematopathologist review (RP02) adds a comment suggesting a blood lead and haemoglobin studies. No provisional report is invented. |
| D2 | Urine lead unit (printed "µg/dL", reference <80) | Recorded as 400.2 µg/L, the catalogue's unit: 4002 µg/L would be implausible beside a blood lead of 121 µg/dL, and <80 fits µg/L. Flagged for review in L33's note. |
| D3 | Serum iron 182 exceeds "TIBC" 165 µg/dL (saturation 110%) | The printed "TIBC" is read as the unsaturated iron-binding capacity, which analysers measure directly: TIBC = 182 + 165 = 347 µg/dL = 62 µmol/L (affected, judgement call); transferrin 2.47 g/L; saturation calculates to 53%. The printed value stays in L25 with `release: never`. This drops the article's "low TIBC" but keeps its "elevated serum iron", and fits iron loading with ring sideroblasts. The alternative (a misprinted iron) was rejected because the text and the flag both call the iron high. |
| D4 | Text calls the liver tests normal; Table 1 shows AST 139, ALT 146, ALP 156 | Table transcribed. No cause is given: hepatitis A, B, C and E markers and liver autoantibodies negative, PT normal, ultrasound normal, GGT mildly raised (58 U/L, judgement call). The enzymes stay an unexplained finding (red herring, P4). |
| D5 | MCV not reported | Red cell count 2.92 ×10¹²/L as an affected row (Hb/MCH = 75/25.7); the MCV then calculates to 79.1 fL (formula row). The case's laboratory profile uses an MCV range of 76–96 fL, common on Indian analysers, so the anaemia reads normocytic as the article says. MCH/MCHC would give 79.6 fL; either is at the lower limit. |
| D6 | Does the generic toxin question release H15? Reason for stopping metformin (G07)? | No, as in the pilot: the toxin question returns "no known exposure" (judgement call). No answer about metformin (H13, adherence) mentions the capsules. |
| D7 | Does `HX.MEDS.OTC` release H15? | No. That item asks about painkillers and chemist medicines; the catalogue routes remedy and online-product questions (including the synonyms "OTC" and "over-the-counter") to `HX.MEDS.SUPPLEMENTS`, which does release it. |
| D8 | Marrow detail (G16) | Mild dyserythropoiesis only; blasts 1%; ring sideroblasts about 30% of erythroblasts ("many"); storage iron increased (grade 4); trephine hypercellular with erythroid hyperplasia; normal flow, karyotype 46,XX, MDS FISH and myeloid NGS (no SF3B1 variant). The iron stain comment gives the pathologist's differential (acquired sideroblastic anaemia or a myelodysplastic neoplasm) and suggests a blood lead, copper and cytogenetics. |
| D9 | Mercury, arsenic and cadmium (G17) | Within reference limits, as affected judgement calls (confidence 0.45): the article reports no features of those metals and tested the capsules for lead only. No reviewer placeholder rows were needed in this case. |
| D10 | Which chelators count for must-do? | Any appropriate chelator: dimercaprol, calcium disodium EDTA, d-penicillamine or oral succimer, with toxicology or haematology input (referral or plan). |
| D11 | Product brand name | Stays in H16's `note`, out of anything a player sees. |
| D12 | Figures | Licence flags true (the article's CC BY 4.0; no separate credit line). `has_annotations` false: neither caption mentions arrows or labels. Files (`PMC11227049/F1.jpg`, `F2.jpg`) are downloaded later; check annotations then. |
| D13 | Day mapping | Everything after admission is undated (`day: null`); the clock runs for day 0 only. |
| D14 | Blood group | Group O, RhD positive (the commonest in Kerala; affected, ABO a judgement call). |
| D15 | Patient-dependent normals | Written as affected rows: postmenopausal menstrual, menopause, contraception, pregnancy and discharge answers; obstetric history (two normal deliveries); pelvic examination; pulse 90/min, matching ECG rate and postural BP; height 154 cm, weight 63 kg; peak flow 350 L/min; capillary glucose 142 mg/dL (7.9 mmol/L), matching the point-of-care test; general appearance and hands (pallor); daily impact and exercise (tiredness); calcium pair consistent with albumin. |
| D16 | `DX.AYURVEDIC_METAL_TOXICITY` in `final_dx.ids` | Removed: its name is generic ("heavy metal toxicity from traditional medicine"), so it scores 3 in the rubric, not 4 or 5. Its synonyms that name lead ("Ayurvedic lead poisoning" and others) are `leak_terms` instead, so the leak scan still covers them. |
| D17 | Must-do "restart effective diabetes treatment" | Condition over insulin or the new action `RX.ENDO.ORAL_HYPOGLYCAEMIC` (catalogue needs). |
| D18 | Other judgement calls | 33 affected rows are judgement calls (see the checklist). The tongue and mouth feel sore (fits E13); B12 low-normal after years of metformin; anti-TPO raised (autoimmune hypothyroidism likeliest); ESR mildly raised; urobilinogen increased; P5N low; urinary coproporphyrin raised; soluble transferrin receptor raised; haptoglobin low-normal; well water. |

## Catalogue needs (`catalogue_needs.json`)

| Kind | New ids | Why |
| --- | --- | --- |
| Tests (2) | `LAB.CHEM.SERUM_PROTEINS`, `LAB.ENDO.THYROID_TOTAL` | Table 1 reports globulin, A/G ratio and total T3 and T4, which no catalogue test holds |
| Components (4) | `CMP.GLOBULIN`, `CMP.AG_RATIO`, `CMP.T3_TOTAL`, `CMP.T4_TOTAL` | L16, L17, L30 and L31 now link to them |
| Action (1) | `RX.ENDO.ORAL_HYPOGLYCAEMIC` | Restarting metformin; the catalogue has insulin only |
| Value rules (2) | `R.GLOBULIN`, `R.AG_RATIO` | Keep calculated globulin and the ratio consistent |

Not added: the product analysis result (L35) stays released by the action `ACT.TEST_PRODUCT`, because it is not a patient test; the WBC differential needs no new item (the existing components carry affected counts). No new diagnosis, finding or normal template is needed.

## Counts (from the replay)

- Facts: 67, all `article` (6 vignette, 57 chart, 4 never released).
- Ledger: 138 `affected` (135 written by the curator and 3 formula rows the derived pass calculates from them: MCV, transferrin saturation and anion gap), 365 `normal`, 1 `rule` (PSA not applicable), 0 `reviewer`. 33 judgement calls.
- Reports 14; consult notes 22 (7 affected, 15 rule); lay texts 10; test utility 66.
- Replay: `== PMC11227049@v1: 0 open problem(s)`.

## Case Reviewer checklist

- [ ] Every value in `single_results` matches Tables 1 and 2 and the text, and each SI conversion in its `note` is right
- [ ] D2 (urine lead as µg/L) and D3 (the printed TIBC read as UIBC) are agreed
- [ ] D5: red cell count 2.92, MCV 79.1 fL and the profile's MCV range 76–96 fL
- [ ] The vignette and opening words reveal nothing diagnostic
- [ ] The H15 release condition, D6 and D7 are acceptable
- [ ] R01–R04 are faithful raw findings; RP01–RP04 are fair reports (D1, D8)
- [ ] The redacted figure captions leak nothing; figure flags and `has_annotations` are confirmed when the files are downloaded
- [ ] Ground truth, rubric, must-do and must-not-do conditions are agreed (D10, D16, D17)
- [ ] The 33 judgement calls in `curation/affected.json`, especially TIBC, GGT, B12, anti-TPO, the other metals and the gums
- [ ] The consult notes help without naming the diagnosis
- [ ] The catalogue needs are merged into the CSV catalogue by the lead curator
