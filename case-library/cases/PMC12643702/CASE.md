# Case PMC12643702: long-acting anticoagulant rodenticide poisoning from food eaten abroad

> **Spoiler warning.** This file, the gold case file, `curation/` and `catalogue_needs.json` contain the answer. They are for the Case Reviewer and for developers, never for a player or a seat. Educational and research use only; nothing here is clinical advice.

Case id `PMC12643702` · version `PMC12643702@v1` · Batch 1 (task L1.3) · Shortlist #3 · Status: **draft; curation steps 1-9 prepared locally, awaiting the Case Reviewer**

Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json) · [`curation/`](curation/)

Curated on 25 Sep 2026 by the Case Curator (Claude), with the open questions decided on Atul's behalf (he delegated them). Nothing has been written to the Case Vault. The local replay (`uv run python -m scripts.case_replay cases/PMC12643702`) reports **0 open problems**.

## Source

Sadek B, Dasmarinas C, Patel I, Bowman L, Xie P, Irons E, Jang A. *Superwarfarin Rodenticide Poisoning due to Consumption of Exotic Animals: A Case Report.* Case Reports in Hematology 2025: 9981550. Published 17 Nov 2025. doi:[10.1155/crh/9981550](https://doi.org/10.1155/crh/9981550) · [PMC12643702](https://pmc.ncbi.nlm.nih.gov/articles/PMC12643702/) · PMID 41293559

- **Licence:** CC BY 4.0, verified in `../BATCH1.md` from the JATS `<license>` element (`data/articles/PMC12643702/efetch.jats.xml`). `production_ok` and `public_release_ok` are true for the article and both figures.
- **Setting:** Cleveland, Ohio (US laboratory units). Every value is converted to the catalogue's SI unit, with the printed value in the fact's `note`.
- **Figures:** two charts, not specimen images, downloaded by the lead curator on 26 Sep 2026 and read by the Case Curator (see "Figure check" below). Figure 2 plots 18 INR results with data labels; Figure 1 plots the times those results were reported. `has_annotations` is true for both (text labels on the image).

## The case in brief

A 37-year-old Chinese-born chef in the US, with poorly controlled type 2 diabetes and chronic hepatitis B on tenofovir, had two weeks of gum and nose bleeding. His doctor sent him for an upper GI endoscopy (no source; blood in the mouth), then to a dentist (tranexamic acid, no effect). Two days of haematuria brought him to hospital. Hb 72 g/L, platelets 226, PT 112 s with an INR too high to calculate, APTT 112 s, fibrinogen 4.35 g/L, D-dimer < 0.20. Factors II 4%, VII < 1%, IX 5%, X 1%; factor V 75%. He took no anticoagulant. Vitamin K 10 mg IV (four doses over 48 h, then 13 more) gave a partial, unstable response, and the bleeding stopped. With no warfarin and a firm denial of rat poison at home or work, an anticoagulant poisoning panel was sent: brodifacoum positive. On further questioning he recalled eating rodents and other exotic animals at a street market during a month-long trip to China, two months earlier. Discharged on day 11 on oral vitamin K 100 mg daily with INR 2.04; INR labile (1.00-1.91) for three months, 0.94 at four months; no further bleeding.

## What the players start with

> A 37-year-old man with poorly controlled type 2 diabetes and chronic hepatitis B on tenofovir presents with two weeks of intermittent bleeding from the gums and nose and two days of blood in his urine.

Opening words: "For two weeks my gums and my nose keep bleeding, on and off, and for the last two days there's been blood in my urine. The tablets the dentist gave me didn't help."

Display title: "Two weeks of bleeding gums and nosebleeds" · tags bleeding gums, nosebleeds, haematuria · specialty haematology · slug `c-6e52g`.

## Timeline

No calendar dates (`day_0` null). Day 0 is admission; the case runs from day 0 to discharge on day 11 (Figure 2's last point).

| Day | Event |
| --- | --- |
| About -90 to -60 | Month-long trip to China; street-market food (H19) |
| About -14 | Gum and nose bleeding begin; GP; urgent gastroenterology; endoscopy (no source); dentist; tranexamic acid 2 days |
| -2 | Haematuria begins |
| 0 | Admission; examination; blood count, coagulation tests, factor assays; IV vitamin K 10 mg begins (4 doses over 48 h) |
| 1-10 | INR from Figure 2 (S02): 8.57, 3.37, 6.31, 3.28, 7.11, 2.51, 2.37, 2.27, 2.03, 1.91 (last reading of each day); 13 more 10 mg IV doses; bleeding stops; APTT normal from day 9 (affected) |
| Undated (null) | Anticoagulant rodenticide panel: brodifacoum positive (L13) |
| 11 | Discharge, INR 2.04 (text and Figure 2); oral vitamin K 100 mg daily |
| Months 1-4 after | INR 1.00-1.91, then 0.94 (outcome text only, not results) |

## Facts (all origin `article`)

| Group | Count | Notes |
| --- | --- | --- |
| History | 19 | H01-H04 in the vignette; H05-H18 on questioning; H19 hidden (below) |
| Examination | 2 | E01 blood at lips and left nostril (released by the oral cavity and the new nose examination); E02 vital signs |
| Laboratory | 13 single + 12 series points | L01-L12 on day 0 (count, PT, APTT, fibrinogen, D-dimer, factors II, V, VII, IX, X); L13 the rodenticide panel (`reveals_dx`, `pivotal`, day null); S01 INR on day 0 ("too high to calculate") and day 11 (2.04); S02 INR days 1-10 read from Figure 2 |
| Raw material | 0 | No film, marrow or imaging in the article |
| Figures | 2 | M01 Figure 1, M02 Figure 2 (charts) |
| Gaps | 9 | G01-G09; G01 now covers PT and APTT only, G02 the discharge day |

Unit conversions: Hb 7.2 g/dL → 72 g/L; WBC 6.6 K/µL → 6.6 x10^9/L; platelets 226 K/µL → 226 x10^9/L; fibrinogen 435 mg/dL → 4.35 g/L; D-dimer < 200 ng/mL → < 0.20 mg/L FEU (FEU assumed); factor activities in % → IU/dL (same number).

## Hidden facts

- **H19 (pivotal):** he ate rodents and other exotic animals bought at a street market in China. Released only by `HX.EXPOSURE.FOOD` (unusual foods), with a `release_condition` asking for questions about exotic or wild-animal meat, food eaten abroad or market meat. A general diet question gets H13 (leftover meats, few vegetables); the toxin and rat-poison questions get H18 (firm denial); the animals question gets an affected answer about contact only (no pets; handles raw meat at work).
- **L13:** the confirmatory panel. It is the only player-visible text that names the poison.

## Ground truth

**Final diagnosis:** long-acting anticoagulant rodenticide (brodifacoum) poisoning, most likely from eating rodents or other animals bought at a street market in China, causing an acquired vitamin K-dependent coagulopathy with mucosal bleeding and haematuria. `DX.SUPERWARFARIN_POISONING` (new), ICD-10 T60.4 and D68.4.

- **Rubric:** 5 `DX.SUPERWARFARIN_POISONING` with H19 cited; 4 the same without the source; 3 `DX.VITAMIN_K_DEFICIENCY`; 2 liver-disease coagulopathy (new `DX.COAGULOPATHY_LIVER_DISEASE`), cirrhosis, DIC, acquired haemophilia, warfarin over-anticoagulation or deliberate self-poisoning; 1 anything else.
- **Must do (with conditions):** vitamin K in the plan; factor assays with factor V (or a mixing study); ask about anticoagulants and rat poison; order the rodenticide panel; ask about unusual food and travel; plan long-term high-dose oral vitamin K with INR monitoring; involve haematology.
- **Must not do:** tranexamic acid without vitamin K; discharge without long-term high-dose vitamin K; liver or kidney biopsy; anticoagulant, antiplatelet or pharmacological thromboprophylaxis; deliberate self-poisoning concluded without the food history.
- **Leak terms:** the synonyms (superwarfarin, brodifacoum, long-acting anticoagulant rodenticide, LAAR and rodenticide-induced coagulopathy phrasings) plus the single words superwarfarin, brodifacoum, bromadiolone and difenacoum. The test name "anticoagulant rodenticide panel" is allowed. The leak scan is clean.

## Path analysis (`curation/paths.json`)

| Path | Kind | What the case must show |
| --- | --- | --- |
| P1 Coagulation work-up to the rodenticide panel | efficient | Normal platelets, fibrinogen and D-dimer; mix corrects; II, VII, IX, X low with V normal; partial, unstable response to 10 mg vitamin K; warfarin not detected; panel positive; H19 on a specific question |
| P2 Liver disease from hepatitis B | trap | Factor V and fibrinogen normal; near-normal liver tests, albumin 36; no stigmata; suppressed HBV; no cirrhosis on ultrasound or elastography; biopsy is a must-not-do |
| P3 A local bleeding source | trap | Endoscopy found no source; bleeding from several sites; tranexamic acid failed; colonoscopy and FIT normal |
| P4 Alcohol | trap | Occasional drinking; ethanol not detected; MCV 84; GGT 58 |
| P5 Haematuria from the urinary tract | alternative | Isomorphic red cells, no casts, sterile urine, normal renal function and imaging; clears by day 5 |
| P6 Other coagulopathies | alternative | Mix corrects; normal thrombin time, factor VIII and VWF; no personal or family bleeding history; protein C and S low with the other vitamin K-dependent proteins |
| P7 Dietary or malabsorptive vitamin K deficiency | alternative | No antibiotics, diarrhoea or weight loss; normal coeliac serology and faecal elastase |
| P8 Deliberate or concealed ingestion | alternative | No self-harm thoughts or drug use; warfarin not detected; psychiatry finds no intent |
| P9 Autoimmune disease | alternative | No lupus features; ANA, dsDNA, complement and lupus anticoagulant negative |
| P10 Diabetes | alternative | Glucose 13.4, HbA1c 8.6, dyslipidaemia; explains glycosuria, not bleeding |
| P11 Dangerous bleeding | alternative | No headache, GCS 15, normal fundi and CT head |
| P12 Travel infection | alternative | Afebrile; dengue, leptospira, scrub typhus, malaria and blood cultures negative |

## Rows written (local replay)

- **Facts:** 46 article (21 history and examination, 13 single results, 12 series points); derived 0 from the article alone.
- **Ledger:** affected 252 (232 written, 20 calculated by the value rules from affected inputs: MCV, MCH, MCHC, reticulocyte %, TSAT, anion gap, non-HDL), of which 37 are judgement calls; reviewer 0; normal 1,956; rule 9 (six gynaecological history items, pelvic examination, urine pregnancy test and Kleihauer test "Not applicable" for a man).
- **Series as affected rows:** PT days 1-11 (from Figure 2's INR, ISI 1.2), APTT days 1-11, fibrinogen days 3, 8 and 10, factors II, V, VII, IX and X on days 3 and 10, full blood count on days 3, 7 and 11, reticulocytes on day 7, urinalysis on day 5.
- **Reports:** 10, all `only` and final (no revised report in the article): blood film, film review, OGD (article plus affected), colonoscopy, ultrasound abdomen, elastography, liver biopsy, ultrasound kidneys, CT KUB, CT head.
- **Consult notes:** 23. Affected 14: haematology (3 variants: none; after factors II/VII/IX/X and V are released; after L13), toxicology (2: none; after L13), gastroenterology, dentistry, ENT, nephrology, psychiatry, rheumatology, endocrinology, infectious diseases, dietetics. Rule 9 for the referrals off the paths. Notes without a condition speak conditionally ("if the platelets are normal ...") so they reveal no result the player has not ordered, and no note names the poison.
- **Lay text:** H05-H19; every affected history row carries its own `lay_text`.
- **Test utility:** 62 (essential 8, supportive 19, low-yield 25, unnecessary 9, risky 1: liver biopsy).

## Figure check (26 Sep 2026)

- **Figure 2** ("INR values during stay") plots 18 INR results against "Day N at time", each with a data label: Day 1 12:00 p.m. 7; Day 1 7:00 p.m. 8.57; Day 2 2:00 a.m. 3.37; Day 3 4:00 a.m. 6.31; Day 4 1:00 p.m. 5.36; Day 4 7:00 p.m. 3.28; Day 5 1:00 a.m. 2.37; Day 5 2:00 a.m. 7.11; Day 6 3:00 a.m. 7.23; Day 6 7:00 p.m. 2.51; Day 7 3:30 a.m. 4.34; Day 7 10:30 3.96; Day 7 8:30 p.m. 2.37; Day 8 1:30 a.m. 1.9; Day 8 3:00 p.m. 2.27; Day 9 2:00 a.m. 2.03; Day 10 5:30 a.m. 1.91; Day 11 5:00 2.04. All labels were legible; none needed an estimate. The 1-hour jump on day 5 (2.37 to 7.11) is transcribed as printed.
- **Figure 1** is titled "Time resulted vs. day", not vitamin K dose times as the caption says. It plots 17 result times against a sequence number (1-17) whose times match Figure 2's labels, so it adds no dated values and was not used. Its redacted caption now reads "Times at which results were reported, by sequence number."
- The vitamin K dose times are therefore not shown in either figure; the text's four doses over 48 h and 13 further doses stand.

## Curator's decisions

| # | Question | Decision |
| --- | --- | --- |
| D1 | Units | SI at extraction; printed value in `note`; `lab_profile` in SI, with the catalogue's male ranges (the article gives none) |
| D2 | The in-hospital INR series (revised 26 Sep 2026) | Read from Figure 2's data labels (Atul's instruction via the lead curator) and added as article facts S02.d1-d10, source "Figure 2", note "read from the figure image". The 14 estimated INR rows are removed. Figure "Day N" is taken as case day N: admission (day 0) carries the text's incalculable INR, which the figure does not plot |
| D2a | Several INR readings on one day | The series holds one point per day, so each day carries its **last** reading (what the engine's latest-result rule shows at the end of that day); all 18 readings with their times are in S02's note. Days 1, 4, 5, 6 and 7 had 2-3 readings (for example day 5: 2.37 at 1:00, 7.11 at 2:00) |
| D3 | Discharge day | Day 11 (was day 15): Figure 2's last point, "Day 11 at 5:00", is the discharge INR of 2.04; S01's discharge point moved to day 11. The day-15 blood count moved to day 11 (Hb 85 g/L), the day-14 fibrinogen to day 10, and the PT and APTT rows for days 12-15 were removed |
| D4 | PT and APTT between admission and discharge | PT from each day's Figure 2 INR (ISI 1.2, mean normal PT 12.3 s); APTT rises and falls with the INR and is normal from day 9 ("aPTT normalized"). Not judgement calls |
| D5 | INR "incalculably high" on day 0 | Text value "Too high to calculate", flag H; no number invented |
| D6 | D-dimer units | < 200 ng/mL read as FEU → < 0.20 mg/L FEU |
| D7 | Day of the rodenticide panel | Day null (valid whenever ordered); its new catalogue test has a 5-day send-out turnaround, so timing comes from the test |
| D8 | Factor assays | Day 0, as "initial workup". Follow-up factors on days 3 (INR 6.31: II 7, VII 5, IX 9, X 5) and 10 (INR 1.91: 34, 38, 40, 30) are affected judgement calls re-set to Figure 2's INR |
| D9 | Transfusion | None reported; none assumed. Hb 72 → 70 (day 3) → 78 (day 7) → 85 (day 11) without transfusion (judgement calls) |
| D10 | Diabetes treatment | Not reported. Metformin with poor adherence (judgement call), glucose 13.4, HbA1c 8.6 (lowered by blood loss), glycosuria, diabetic dyslipidaemia. The lipid profile is affected because independent normal draws broke the non-HDL formula (replay finding) |
| D11 | Hepatitis B status | HBsAg and anti-HBc reactive, suppressed on tenofovir, no cirrhosis: near-normal liver tests, mild steatosis on ultrasound, liver stiffness 6.2 kPa |
| D12 | "Denied anticoagulant use" and "no family members using warfarin" | One fact (H10) released by a new item, `HX.MEDS.ANTICOAGULANTS`, so the current-medicines question can carry the affected tenofovir and metformin answer without a fact-ledger clash |
| D13 | The rat-poison denial (H18) | Released by the new `HX.EXPOSURE.RODENTICIDE` and by the general toxins question: the article records it as his answer about pesticides at home and work, so a general toxins question returns it too |
| D14 | Where the market food is released | Only `HX.EXPOSURE.FOOD`, as in the article (recalled on further questioning). The animals question answers contact only (SPEC §6.4 rule 8) |
| D15 | Examination beyond the lips and nose (G07) | Pallor; oozing gum margins; no petechiae but bruising at venepuncture sites (platelets normal; no spontaneous ecchymoses added); pulse 86 regular; small postural drop; no stigmata of liver disease; no haemarthrosis; GCS 15; normal fundi |
| D16 | Blood group | Group B RhD positive (judgement call: common in people of Chinese origin; RhD negative under 1%) |
| D17 | Haematuria | Isomorphic, no casts; clears to 4 red cells/HPF with trace blood by day 5 ("resolution of all bleeding"); normal kidneys; bladder debris on imaging |
| D18 | Lupus anticoagulant and protein C/S | dRVVT ratio 1.08, LA not detected with a caution comment; protein C 12 and free protein S 24 (vitamin K-dependent), antithrombin normal |
| D19 | Consultants | V1 notes are conditional and name tests, not the diagnosis. Haematology V2 (after the factor pattern) recommends the rodenticide panel, as the article's team did. Toxicology V2 (after L13) points to the food chain and to a sensitive assessment for intentional exposure, as the article did. Psychiatry finds no intent |
| D20 | Must-do on the source | Asking about food and travel is a must-do; notifying public health is not (the article did not) |
| D21 | Reviewer placeholders | None: no value here is one Claude must not guess |
| D22 | Male patient | Gynaecological items, pelvic examination, urine pregnancy and Kleihauer tests are rule rows "Not applicable"; transfusion history drops the pregnancy wording |

### Judgement calls, most important first

1. **Factors II, VII, IX, X on days 3 and 10** (partial rise; alternative: not repeated, so the admission values stand).
3. **CMP.HB days 3-15** without transfusion (alternative: transfused on admission at 72 g/L with active bleeding).
4. **HX.MEDS.CURRENT / HX.MEDS.ADHERENCE**: metformin, often missed (alternative: insulin or another agent).
5. **HX.EXPOSURE.ANIMALS**: contact only, market not mentioned (alternative: mention the market, which would release the source without the food question).
6. **EX.SKIN.PURPURA**: venepuncture bruising only (alternative: no bruising, or spontaneous ecchymoses).
7. **EX.ORAL.GUMS**: oozing gum margins without dental disease.
8. **HX.GI.BLEEDING**: spits blood, no haematemesis or melaena.
9. **CMP.ABO_GROUP** group B.
10. The rest: glucose, HbA1c, cholesterol, UACR, FIT, iron, dRVVT, protein C and S, urinary blood on day 5, postural BP, height and weight, capillary glucose, syncope, thirst, nocturia, aggravating factors, pain on passing clots.

## Catalogue needs

11 new items, proposed in `catalogue_needs.json` and since merged into `catalogue/*.csv` by the lead curator (the file is gone):

| Kind | Items |
| --- | --- |
| History (2) | `HX.MEDS.ANTICOAGULANTS`, `HX.EXPOSURE.RODENTICIDE` |
| Examination (1) | `EX.ENT.NOSE` (anterior rhinoscopy) |
| Tests (2) | `LAB.TOX.ANTICOAGULANT_RODENTICIDE_PANEL` (INR 6,500, estimate, 5 days), `LAB.TOX.WARFARIN_LEVEL` (INR 3,500, estimate, 3 days) |
| Components (2) | `CMP.ANTICOAG_RODENTICIDE_SCREEN`, `CMP.WARFARIN` (qualitative, "Not detected", Tietz) |
| Actions (3) | `RX.VITAMIN.K_HIGH_DOSE_ORAL`, `RX.HAEM.PCC`, `ACT.INR_MONITORING` |
| Referral (1) | `REF.DENTISTRY` |
| Diagnoses (2) | `DX.SUPERWARFARIN_POISONING` (T60.4), `DX.COAGULOPATHY_LIVER_DISEASE` (D68.4); ICD-11 codes left empty to verify |
| Normal templates (4) | the two history items, the nose examination and the dentistry note |

The shortlist's other suggestions already exist: factor II, V, VII, IX, X assays, the mixing study, `RX.VITAMIN.K`, `RX.TRANSFUSION.FFP`, `RX.HAEM.TRANEXAMIC`, `HX.SOCIAL.TRAVEL`, `HX.EXPOSURE.FOOD`, `HX.PSYCH.SELF_HARM`, `REF.PSYCHIATRY`, `DX.VITAMIN_K_DEFICIENCY`.

## Case Reviewer checklist

- [ ] Verify every article fact (H01-H19, E01-E02, L01-L13, S01) against the article, including the unit conversions.
- [ ] Check S02 against Figure 2 (values, the day mapping in D2 and the last-reading rule in D2a).
- [ ] Confirm the discharge day (D3, day 11).
- [ ] Review the 37 judgement calls, starting with the list above.
- [ ] Check H19's release condition and that the food is not released by any other question.
- [ ] Check the rubric (especially 3 for vitamin K deficiency and 2 for deliberate self-poisoning) and the must-do and must-not-do conditions.
- [ ] Read the consult notes for leaks and for being no more diagnostic than a colleague would be (haematology V2, toxicology V1 and V2).
- [ ] Approve or edit the new catalogue items, their synonyms, prices and turnaround, and verify the ICD codes.

## Figure check (2026-09-26)

The images were downloaded from PMC and looked at one by one.

- M01 and M02: `has_annotations` set to true (axes, legend and INR data labels).
- Figure 1's article caption says vitamin K dose times, but the chart's title and legend read "Time resulted" (result times). The caption is kept as the article gives it; check at review.
- Figure 2 shows the article's INR values as data labels. The INR series in the ledger was estimated before the figure was seen and should be replaced from it at review.

## Corrections after the second review (2026-09-26)

The case was approved in bulk; a second expert review found three problems. All changes are in `curation/`; the replay reports 0 open problems (ledger: affected 276, normal 1,932, rule 9; 24 normal rows replaced by affected rows on the same targets and days).

| # | Finding | File, key | Change | Reason |
| --- | --- | --- | --- | --- |
| C1 | HIGH: prothrombin activity (Quick %) was a normal value (82-106%) on days 0-11 | `affected.json`, `CMP.PT_ACTIVITY` days 0-11 (new affected rows, gap G01, not judgement calls) | Normal 87, 94, 95, 96, 106, 87, 106, 82, 100, 91, 104, 92 % → affected 7, 7, 20, 10, 21, 9, 28, 30, 32, 36, 39, 36 %, flag L | Follows each day's INR (Figure 2, days 1-10; 2.04 on day 11) with the Case Library's common curve, activity % = round(100 x 0.59 / (INR - 1 + 0.59)), capped at 100, floored at 1 (0.59 calibrated to 44% at INR 1.75 in another batch case). Day 0 has only PT 112 s: INR estimated as 112 / 12.3 (the case's mean normal PT, ISI ~1) = 9.11, giving 7%. Consistent with factors II 4, VII < 1, X 1 on day 0 |
| C2 | MEDIUM: toxicology CN05 pointed straight at H19 ("meat bought at markets abroad") | `consult_notes.json`, CN05 `note_text` and first recommendation | "These agents concentrate in rodents and in the animals that eat them, so a history of unusual meats, including food bought abroad ..." → "Exposure can be indirect, through contaminated food or other products or through contact at work, so a careful exposure history covering unusual foods or products, including while abroad ..."; "Take a detailed food history, including meat bought at markets abroad" → "Take a detailed exposure history: unusual foods or products, including while abroad, and contact at work" | A consultant who does not know the source names exposure routes, not market meat. The note stays gated on L13 |
| C3 | LOW: a normal EPO did not fit Hb 72 g/L after two weeks of bleeding | `affected.json`, `CMP.EPO` days 0-11 (new affected rows, gap G03, judgement calls) | Normal 8.4-22.1 IU/L → affected 88.0, 90.0, 94.0, 98.0, 92.0, 85.0, 77.0, 70.0, 64.0, 58.0, 53.0, 48.0 IU/L, flag H | Moderately raised, as expected for anaemia from blood loss with normal kidneys (creatinine 84): highest at the day-3 nadir (Hb 70), easing as Hb recovers to 78 (day 7) and 85 (day 11) without transfusion. Judgement call: the article gives no EPO (alternative: a smaller rise if diabetes blunts it) |
