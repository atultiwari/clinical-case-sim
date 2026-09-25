# Case PMC11227049: an Indian sibling of the pilot

Case id `PMC11227049` · Status: **draft, curation steps 1–5 done; awaiting Case Reviewer verification** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json)

> Spoiler warning. This file and the JSON contain the answer. They are for the Case Reviewer and for developers. Never show them to a player or a seat.

Drafted on 25 Sep 2026 for Case Library task L1.3 (batch 1). The path analysis, `affected` values, reports and consult notes wait for the pilot review.

## Source

Thomas J, Sebastian R, Anil Kumar CR, Rafi AM. *Case of lead poisoning secondary to intake of herbal medicine for diabetes mellitus in a tertiary care hospital in Kerala.* Endocrinology, Diabetes & Metabolism Case Reports 2024(2): 23-0066. Published 10 Jun 2024. doi:[10.1530/EDM-23-0066](https://doi.org/10.1530/EDM-23-0066) · [PMC11227049](https://pmc.ncbi.nlm.nih.gov/articles/PMC11227049/) · PMID 38866062

- **Licence:** CC BY 4.0 (read from the `<license>` element of the cached JATS XML, `data/articles/PMC11227049/jats.xml`, SHA-256 `671ee106…79e2`). `production_ok` and `public_release_ok` are both true. The figure captions carry no separate credit line. Each figure's own flags are still false, because figure flags are Atul's decision.
- **Attribution:** "Adapted from Thomas J, Sebastian R, Anil Kumar CR, Rafi AM, Endocrinol Diabetes Metab Case Rep 2024(2): 23-0066 (2024), CC BY 4.0. Restructured into a simulation; diagnosis hidden until the debrief; simulated findings added where marked."
- **Setting:** Jubilee Mission Medical College, Thrissur, Kerala, India.

## The case in brief

A 58-year-old woman with type 2 diabetes and hypothyroidism had two weeks of generalised tiredness, reduced food intake and abdominal pain after eating. She had stopped metformin two months earlier and was on thyroxine. She was pale, with desquamation of the tongue and oral mucosa. Her vital signs and systemic examination were normal. Her Hb was 7.5 g/dL, with MCH 25.7 pg, RDW 15.3% and reticulocytes 7.94%. Her transaminases were raised (AST 139, ALT 146 U/L), as were her ALP (156 U/L) and bilirubin (1.4 mg/dL, direct 0.1). Serum iron was high (182 µg/dL), TIBC low (165 µg/dL) and HbA1c 9%.

A careful look at the film showed coarse basophilic stippling, normoblasts and polychromasia. The marrow showed erythroid hyperplasia and many ring sideroblasts, and its report raised both acquired sideroblastic anaemia (lead or zinc) and MDS with ring sideroblasts. The team then asked her again about heavy-metal exposure. She disclosed an Ayurvedic diabetes capsule she had bought online, taken for 1.5 months and stopped before admission. Blood lead was 121.20 µg/dL (reference <25) and random urine lead 400.2 (reference <80); blood zinc was normal. The capsules contained 40 657 ppm of lead. She was treated with BAL and then oral d-penicillamine for six weeks. Her Hb was 10.1 g/dL at discharge, and her blood and urine lead had returned to normal at follow-up.

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
| Not dated | Blood film examined carefully; bone marrow and iron stain; history revisited and capsules disclosed; blood and urine lead, blood zinc; ultrasound abdomen normal; capsules analysed; BAL started, then d-penicillamine |
| Discharge (not dated) | Hb 10.1 g/dL |
| About six weeks of d-penicillamine | Blood and urine lead normal; film shows mild normocytic normochromic anaemia only |

The case file treats every undated result as available whenever it is ordered during the admission (`day: null`). The outcome values (O01–O03) are `release: never`, for the debrief only.

## Facts

| Group | Ids | Count |
| --- | --- | --- |
| History | H01–H16 (6 in the vignette, 10 in the chart) | 16 |
| Examination | E01–E13 | 13 |
| Laboratory, day 0 | L01–L31 | 31 |
| Lead, zinc and product | L32–L35 | 4 |
| Outcome (never released) | O01–O03 | 3 |
| Raw material | R01 film, R02 marrow aspirate, R03 iron stain, R04 ultrasound | 4 |
| Figures | M01 (Figure 1), M02 (Figure 2) | 2 |
| Gaps | G01–G20 | 20 |

## Hidden and conditional facts

| Fact | Released when |
| --- | --- |
| H15 "She had been taking herbal capsules for her diabetes, bought over the internet, for about one and a half months, and stopped them before admission." | Only on a specific question about supplements, herbal, Ayurvedic or traditional remedies, or remedies bought online (`HX.MEDS.SUPPLEMENTS`, `HX.MEDS.SUPPLEMENT_DETAILS`) |
| H16 Product details (Ayurvedic diabetes capsule, bought online, 1.5 months) | `HX.MEDS.SUPPLEMENT_DETAILS` |
| L35 Lead content of the capsules | `ACT.TEST_PRODUCT` (the product is sent for analysis) |

This follows the article. The capsules came out only when the team went back to the history after the film and marrow findings. She had stopped them before admission, so a general medication question returns metformin (stopped) and thyroxine only.

## Raw material for the Pathology and Radiology Services

| Id | Test | Raw findings |
| --- | --- | --- |
| R01 | Peripheral blood film (day 0) | Normocytic normochromic anaemia. Coarse basophilic stippling of red cells. Normoblasts present. Polychromasia. |
| R02 | Bone marrow aspirate | Erythroid hyperplasia. |
| R03 | Bone marrow iron stain (Perls) | Many ring sideroblasts. |
| R04 | Ultrasound abdomen | No abnormality. |

The marrow report's impression (sideroblastic anaemia from lead or zinc, or MDS with ring sideroblasts) is an interpretation. It is kept in R02's note, not in the findings.

## Ground truth

**Final diagnosis:** lead poisoning from an Ayurvedic herbal diabetes capsule bought online (`DX.LEAD_POISONING`, T56.0, with D64.2). `DX.AYURVEDIC_METAL_TOXICITY` is listed in `ids` so that the leak scan also covers its names.

**Treatment given:** the capsules were stopped; BAL, then oral d-penicillamine for six weeks; the capsules went to the state drug analyst.

Rubric anchors, must-do and must-not-do are drafted as plain text in the JSON. Their conditions over catalogue ids come later.

## Catalogue items the case needs that the catalogue lacks

- Components for **globulin** (L16), **albumin/globulin ratio** (L17), **total T3** (L30) and **total T4** (L31). The catalogue has only free T3 and T4 (`LAB.ENDO.TFT`). These four facts have no `catalogue_ref`, so no player can reach them yet.
- A **product analysis result** (lead in a remedy). For now L35 hangs on the action `ACT.TEST_PRODUCT` through `released_by`, and has no component.
- The WBC differential is text only ("normal", L09). It has no component to link to.

## Open questions for Atul

1. **Units.** Facts keep the article's conventional units (g/dL, %, mg/dL, µg/dL), and the lab profile uses the same units. The value rules assume SI units, so `R.MCHC` will report a false formula failure (7.5 / 23.1 ≠ 32.3), and a derived TSAT would compare mixed units. Should we keep conventional units, which is realistic for an Indian laboratory, and teach the rules about units? Or should we convert to SI in the file?
2. **Unit misprints corrected in `unit`, each recorded in `note`:** MCHC printed "%" (g/dL meant); albumin printed "mg/dL" (g/dL); T4 printed "µg/mL" (µg/dL); blood lead given as "121.20 µg" in the text (µg/dL in Table 2). Urine lead is kept as printed, "µg/dL, <80". Is µg/L meant? The catalogue uses µg/L.
3. **Serum iron 182 exceeds TIBC 165 µg/dL.** That gives a transferrin saturation above 100%, which is impossible. It may be a misprint, or UIBC may have been reported as TIBC. Do we keep it as printed, or leave TSAT unresolved?
4. **Contradiction in the article.** The text says the liver function tests were "normal", but Table 1 shows AST 139, ALT 146, ALP 156 and bilirubin 1.4. I transcribed the table. Is the liver picture a red herring, or should gap G14 carry a cause?
5. **MCV.** None is reported, and MCH/MCHC gives about 80 fL, at the lower limit of "normocytic" (G02). Please set the value.
6. **Should the generic toxin question (`HX.EXPOSURE.TOXINS`) also release H15?** In the article, the question about heavy-metal exposure is what brought out the disclosure. I left it out, as in the pilot. This decision also covers G07 (the reason she stopped metformin).
7. **The product's brand name** is in the article. I kept it in H16's `note` and out of anything a player sees. Should it be named?
8. **Figures** were not downloaded, so `has_annotations` is set false without checking, and the stain for Figure 1 is not stated.
9. **Chelation.** The article used BAL then d-penicillamine; succimer is often unavailable in India. Should all three chelators count in must-do?
10. **Day mapping.** Everything after admission is undated (day null), so the case clock runs for day 0 only.

## Case Reviewer checklist

- [ ] Every value in `single_results` matches Tables 1 and 2 and the text
- [ ] The unit decisions (questions 1–3) are agreed
- [ ] The vignette and opening words reveal nothing diagnostic
- [ ] The H15 release condition is acceptable
- [ ] R01–R04 are faithful raw findings with no interpretation
- [ ] The redacted figure captions leak nothing; figure flags are set
- [ ] Ground truth, rubric anchors, must-do and must-not-do are agreed
- [ ] Gap guidance is agreed; values are set for G02, G16 and G17
