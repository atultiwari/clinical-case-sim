# Case PMC12007988: B12 deficiency disguised as thrombotic microangiopathy

Case id `PMC12007988` · Status: **draft, awaiting Case Reviewer verification** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json) · Case Library task L1.3, curation steps 1–5

> Spoiler warning. This file and the JSON contain the answer. They are for the Case Reviewer and for developers, never for a player or a seat.

Educational and research use only. Nothing here is clinical advice.

## Source

Manabe M, Inano N, Hagiwara Y, Koh KR. *Vitamin B12 Deficiency-Induced Massive Schistocytosis and Hemolytic Anemia Due to Pseudo-Thrombotic Microangiopathy: A Case Report.* Cureus 17(3): e80855. Published 19 Mar 2025. doi:[10.7759/cureus.80855](https://doi.org/10.7759/cureus.80855) · [PMC12007988](https://pmc.ncbi.nlm.nih.gov/articles/PMC12007988/) · PMID 40255844

- **Licence:** CC BY 4.0, read from the `<license>` element of the cached JATS XML (`data/articles/PMC12007988/jats.xml`) on 25 Sep 2026. `production_ok` and `public_release_ok` are true. The figure captions carry no separate credit line. Each figure's own flags are set to false until Atul decides (SPEC §9).
- **Attribution to reuse:** "Adapted from Manabe M, Inano N, Hagiwara Y, Koh KR, Cureus 17(3): e80855 (2025), CC BY 4.0. Restructured into atomic facts; diagnosis redacted from player-facing text; simulated findings added where marked."
- **Setting:** Osaka, Japan (Osaka General Hospital of West Japan Railway Company). Laboratory values are in conventional units (g/dL, mg/dL, pg/mL).

## The case in brief

A 37-year-old man was referred with a month of fatigue, loss of appetite and weight loss. He was pale and icteric, with no palpable nodes, liver or spleen and a normal neurological examination. He had no past history and took no medicines. He was not vegan or strictly vegetarian but ate meat or seafood only about once a month.

Haemoglobin was 6.2 g/dL with MCV 117.4 fL, reticulocytes 44.8 ×10⁹/L (3.07%), platelets 105 ×10⁹/L, WBC 4.0 ×10⁹/L, LDH 3115 U/L, bilirubin 2.3 mg/dL (direct 0.8) and haptoglobin <10 mg/dL. Direct and indirect antiglobulin tests were negative. Renal function and coagulation were normal, apart from a slightly raised D-dimer. Iron and ferritin were high. The film showed marked schistocytosis, with nucleated red cells that included megaloblasts, and hypersegmented neutrophils. The analyser's red cell histogram had a small peak around 10 fL. TTP was considered (PLASMIC score 5, intermediate). A marrow, done to exclude cancer-related TMA, was hypercellular and megaloblastic, with dysplastic features and a normal karyotype.

On day 1 haemoglobin fell to 5.8 g/dL and platelets to 64 ×10⁹/L. He was transfused for severe breathlessness on exertion and started on intramuscular cyanocobalamin. ADAMTS13 was considered but not sent. Serum B12 came back on day 4 at 76 pg/mL (233–914). He went home on day 7 with injections stopped and advice to eat meat. By five weeks his counts and LDH had normalised, B12 was 375 pg/mL and the schistocytes had gone. The authors attribute the deficiency to diet. Intrinsic factor antibodies were never tested.

**Final diagnosis (ground truth):** `DX.B12_DEFICIENCY_ANAEMIA`. Dietary vitamin B12 deficiency presenting as pseudo-thrombotic microangiopathy (ICD-10 D51.3).

## What the players start with

> A 37-year-old man is referred to hospital with a one-month history of fatigue, loss of appetite and weight loss. He has no relevant past medical history and takes no regular medicines.

Opening words: "I've been tired all the time for about a month. I've gone off my food and I've been losing weight."

Display title: "Tired, off his food and losing weight" · slug `c-ov0b4`

## Timeline in the article

Day 0 is the first hospital day. The article gives no calendar dates (`clock.day_0` is null).

| Day | Event |
| --- | --- |
| 0 | Referral. Pallor and icterus. Hb 6.2 g/dL, MCV 117.4 fL, retics 44.8 ×10⁹/L, platelets 105, LDH 3115, haptoglobin <10 mg/dL, DAT and IAT negative. Renal function, coagulation and iron studies. Film: schistocytes, megaloblastic NRBCs. Histograms. Serum B12 sent |
| 0 (undated) | Bone marrow: megaloblastic, dysplastic, normal karyotype |
| 1 | Hb 5.8 g/dL, platelets 64. Severe breathlessness on exertion, so red cell transfusion given, then IM cyanocobalamin started. ADAMTS13 not sent |
| 4 | Serum B12 reported: 76 pg/mL |
| 7 | Hb 8.8, platelets 48, WBC 3.2, LDH 1353, bilirubin 1.1. Symptoms better. Injections stopped; discharged with dietary advice |
| 35 | Hb 13.1, MCV 91.5, platelets 219, WBC 10.2, LDH 211, B12 375 pg/mL. No schistocytes; histograms normal |

## Hidden and conditional facts

| Fact | Released when |
| --- | --- |
| H09 "Not vegan or a strict vegetarian, but eats meat or seafood only about once a month." | Only a question about diet or vegetarianism (`HX.SOCIAL.DIET`, `HX.SOCIAL.VEGETARIAN`) |
| H08 "No previous gastrointestinal surgery." | Past surgical history |
| H10 Severe breathlessness on exertion | Day 1 onwards |

## Raw material for the Pathology Service

| Id | Test | Day | Raw findings |
| --- | --- | --- | --- |
| R01 | Blood film | 0 | Marked schistocytosis; NRBCs (6/100 WBC) with nuclear fragmentation, megaloblasts and atypia; hypersegmented neutrophils (>6 lobes) |
| R02 | Analyser histograms (under the FBC) | 0 | Red cell histogram: small peak around 10 fL; platelet histogram: abnormal distribution |
| R03 | Bone marrow aspirate | 0 | Hypercellular; marked megaloblastic change; hypersegmented and giant neutrophils; multinucleated erythroblasts; separated multinucleated megakaryocytes |
| R04 | Blood film | 35 | No schistocytes |
| R05 | Analyser histograms | 35 | Normal distributions |

Figures M01–M06 (F1–F4, not downloaded) are kept as published, with the arrows, circles and panel letters (`has_annotations: true` for all). Their captions are redacted to specimen, stain and timing.

## Counts

- Facts: 11 history, 5 examination, 7 series (20 points), 20 single results (the DAT is split into IgG and C3d), 5 raw material, 6 media.
- Gaps: G01–G22.

## Catalogue items the case needs that the catalogue lacks

- ADAMTS13 activity (test and component). This is the pivotal TTP test: the article chose not to send it.
- Fibrin degradation products (L14 has no `catalogue_ref`).
- Analyser red cell and platelet histograms, or a schistocyte (fragmented red cell) count. R02 and R05 are filed under `LAB.HAEM.CBC`.
- Methylmalonic acid and homocysteine.
- Diagnosis: no `DX.*` item for pseudo-thrombotic microangiopathy. `DX.MAHA_OTHER` lists "thrombotic microangiopathy" as a synonym, so it is the mimic, not the answer.
- Action: intramuscular cyanocobalamin specifically. `RX.VITAMIN.B12` covers it generically.

## Open questions for Atul

1. **Units.** Facts keep the article's conventional units (g/dL, mg/dL, µg/dL, ng/mL, pg/mL). The engine does not convert units, so generated values (for example sodium or AST) will come out in the catalogue's SI units. Should I convert the article values to SI (Hb 62 g/L and so on), or add conventional-unit ranges to `lab_profile`? Only B12 has an article range.
2. **Flags.** The article gives no reference ranges except for B12. I set H/L flags only where it is unambiguous or where the article says so (D-dimer "slightly elevated"). Please check them.
3. **B12 day.** Reported on day 4, but the sample must predate the day-1 cyanocobalamin, so it is filed on day 0. Is a four-day turnaround acceptable in play?
4. **Marrow day.** The marrow is undated. It is filed on day 0 so that its megaloblastic picture is not shown after treatment has started.
5. **DAT split.** "Direct Coombs negative" is split into IgG negative and C3d negative, assuming a polyspecific test.
6. **Follow-up at day 35.** Including these values stretches `case_days` to 35. Should they be `release: never` (outcome only)?
7. **Figure 1B** says "hyperfragmented neutrophils", but the Discussion says hypersegmented. I recorded hypersegmented.
8. **Cause of the deficiency.** The dietary attribution rests on a B12 of 375 pg/mL after a week of IM cyanocobalamin, with pernicious anaemia never tested. I made "look for the cause, including IF antibodies" a must-do. G13 (IF antibodies) needs your values.
9. **Teaching trap.** The authors decided against ADAMTS13 because of the marrow. Should a player who skips ADAMTS13 be penalised, or only one who starts plasma exchange?
10. **has_annotations** is true for F2 and F4 only because of their panel letters (their captions mention no arrows). Please confirm when you look at the figures.
