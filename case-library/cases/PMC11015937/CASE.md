# Case PMC11015937: a returned traveller whose blood picture looks like TTP

Case id `PMC11015937` · Case version `PMC11015937@v1` · Status: **draft, curation steps 1–9 done; the local replay is clean; waiting for the Case Reviewer** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json), [`curation/`](curation/), [`catalogue_needs.json`](catalogue_needs.json)

> Spoiler warning. This file and the JSON files name the diagnosis. They are for the Case Reviewer and for developers only. Never show them to a player or a seat. This is for education and research only; nothing here is clinical advice.

Curated on 25 Sep 2026 for Case Library task L1.3 (batch 1, shortlist section 1, row 4). Nothing has been written to the Case Vault. `uv run python -m scripts.case_replay cases/PMC11015937` reports `0 open problem(s)`.

## Source

Kunwar K, Karki S, Jain M, Edara S, Rixey JY, Schmidt F. *Plasmodium falciparum Malaria Presenting as a Thrombotic Thrombocytopenic Purpura (TTP) Mimic: A Case Report.* Cureus 16(3): e56181. Published 14 Mar 2024. doi:[10.7759/cureus.56181](https://doi.org/10.7759/cureus.56181) · [PMC11015937](https://pmc.ncbi.nlm.nih.gov/articles/PMC11015937/)

- **Licence:** CC BY 4.0, verified from the JATS `<license>` element (`cases/BATCH1.md`). `production_ok` and `public_release_ok` are both true. The figures have no separate credit line.
- **Figures:** two line charts (Figure 1: platelet trend; Figure 2: percentage of parasitised red cells). There is no image of the film. Both are listed as media with `has_annotations: true`: the captions don't mention annotations, but a chart always carries axis labels, and Figure 2's labels probably name the parasite. They need masking or cropping before a player sees them.
- **Cache:** `data/articles/PMC11015937/efetch.jats.xml`.
- **Setting:** Interfaith Medical Center, Brooklyn, New York, USA.

## The case in brief

A 55-year-old woman had 10 days of abdominal pain, loose stools, nausea, vomiting and fever. She had been seen in the emergency department a few days earlier and sent home on oral antibiotics. She had spent four weeks in Nigeria and came back to the United States two weeks before, without antimalarial prophylaxis. She looked ill, pale and dehydrated, and she was confused. Her abdomen was soft and non-tender.

On admission her Hb was 10.6 g/dL, with MCV 77.6 fL and MCH 25.8 pg. Her platelets were 125, lactate 2.3 mmol/L, INR 1.37, bilirubin 2.2 mg/dL and LDH 287 U/L. Haptoglobin was below 10 mg/dL, BUN 35 mg/dL and creatinine 1.7 mg/dL. Her platelets and Hb then fell (to 66 on day 2 and to an Hb of 6.0 on day 7). The PLASMIC score was 6. The ADAMTS13 antibody was raised at 22 U/mL (normal <12), with ADAMTS13 activity 49.1% (normal >66.8%). Thick and thin smears showed *P. falciparum* and occasional schistocytes. Blood culture, stool tests (culture, occult blood, Giardia antigen, leucocytes, C. difficile), chest X-ray and CT of the abdomen and pelvis were all negative.

She was treated with artemether-lumefantrine for four days and two units of red cells. She had no plasma exchange. She was afebrile after day 2, and her symptoms resolved by day 5. Her platelets normalised (444 on day 9) and her reticulocytes reached 7.78%. At one month she was well, with Hb 11.6 g/dL.

## What the players start with

> A 55-year-old woman comes to the emergency department with ten days of fever, abdominal pain, loose stools, nausea and vomiting. She was seen here a few days ago with the same complaints and sent home on oral antibiotics.

Opening words: *"I've had a fever and tummy pain for ten days, with diarrhoea and vomiting. They gave me antibiotics here the other day, but I'm getting worse."*

Display title: "Ten days of fever, abdominal pain and loose stools". Tags: fever, diarrhoea, thrombocytopenia, confusion. Specialty: haematology. Slug `c-r8tq2`.

## Timeline (day 0 = admission; the article gives no calendar date)

| Day | Events |
| --- | --- |
| About −42 to −14 | Four weeks in Nigeria, with no prophylaxis |
| About −4 | Emergency visit; sent home on oral antibiotics (curator: ciprofloxacin) |
| 0 | Admitted: confused and dehydrated; Hb 106 g/L, platelets 125, creatinine 150 µmol/L, haptoglobin undetectable; films positive for *P. falciparum* |
| 2 | Platelets 66 (the lowest), Hb 85; creatinine peaks (curator's value); **artemether-lumefantrine started, parasitaemia 5%** (Figure 2); afebrile from now on |
| 3 | Parasitaemia 1.6% (Figure 2) |
| 4 | Hb 68, reticulocytes 0.37%; parasitaemia 0.6% |
| 5 | Symptoms resolved; no parasites seen (Figure 2, also day 6); platelets about 157 (Figure 1) |
| 7 | Hb 60 (the lowest); two units of red cells about now; reticulocytes 2.58% |
| 9 | Hb 92, platelets 444, reticulocytes 7.78%; discharged around here |
| About +30 | Clinic: well, Hb 11.6 g/dL (kept out of play, in the ground truth's outcome) |

## Facts (article)

- **History (5):** H01 age and sex; H02 presenting complaints (vignette); H03 earlier emergency visit (vignette); **H04 travel to Nigeria (hidden, pivotal)**, released only by `HX.SOCIAL.TRAVEL`; H05 no prophylaxis, released by the new `HX.SOCIAL.TRAVEL_PROPHYLAXIS` or the travel question.
- **Examination (5):** looks ill, pale, dehydrated with dry mucous membranes, confused, abdomen soft and non-tender.
- **Series (10, 50 points):** days 0/2/4/7/9 from Table 1 (Hb, Hct, MCV, MCH, platelets, reticulocyte %, LDH, haptoglobin, in SI units); S09 parasitaemia days 2–6 from Figure 2 (5, 1.6, 0.6, 0, 0%); S10 platelets days 1/3/5/6/8 from Figure 1 (67, 80, 157, 235, 375). Both read from the figure images on 26 Sep 2026.
- **Single results (14):** lactate, PT, INR, bilirubin, urea (from BUN), creatinine, blood culture, stool occult blood, stool culture, Giardia antigen, stool leucocytes (no catalogue component), C. difficile, ADAMTS13 antibody 22 U/mL and activity 49.1% (both day `null`).
- **Interpretation (1):** X01, the PLASMIC score of 6, set to `release: never` because players calculate it themselves.
- **Raw material:** R01 smear (*P. falciparum*, occasional schistocytes), R02 Figure 2, R03 chest X-ray negative, R04 CT abdomen and pelvis negative.
- **Derived:** MCHC on the five table days (330, 339, 316, 333, 324 g/L).

## Hidden facts and how they are released

- **Travel (H04, H05)** appears only when the player asks about travel or prophylaxis. The first emergency visit missed it, and the ED discharge note (`HX.RECORDS.DISCHARGE_SUMMARIES`) is silent on travel.
- **Indirect routes** a real history would give: the bites question ("lots of mosquito bites on my trip") and the vaccination question (yellow fever vaccine) both hint at travel.
- **Parasites** show on any blood film the player orders (screening film, film review or malaria smear), as they would in a real laboratory.

## Path analysis (summary; full lists in `curation/paths.json`)

| Path | Kind | Point |
| --- | --- | --- |
| P1 Efficient | efficient | Travel history → thick and thin films and rapid test → severity (GCS, glucose, lactate, renal function, parasite count) → artemisinin treatment, fluids, transfusion, notification |
| P2 TTP | trap | PLASMIC 6, ADAMTS13 antibody raised, schistocytes, AKI, confusion → plasma exchange. Answered by: schistocytes only occasional, activity 49.1%, parasites on the film |
| P3 Gastroenteritis or sepsis | trap | Diarrhoea already treated with antibiotics; CRP and procalcitonin raised. All stool tests, cultures and imaging negative |
| P4 Other tropical fevers | alternative | Enteric fever, dengue, leptospirosis, hepatitis and HIV serology all negative; Widal titres not significant |
| P5 Encephalopathy | alternative | GCS 14 without focal signs; CT head, CSF, ammonia and glucose normal |
| P6 Microcytic anaemia | alternative | MCV 74–80 fL from admission; ferritin high (acute phase), HPLC normal, alpha-globin −α3.7/−α3.7 (a judgement call) |
| P7 Acute kidney injury | alternative | Prerenal pattern plus the infection; no obstruction, rhabdomyolysis or DIC; recovered by day 9 |

## Ground truth (short)

- **Final diagnosis:** `DX.FALCIPARUM_MALARIA` (and `DX.SEVERE_MALARIA` in `ids`), with microangiopathic haemolysis, thrombocytopenia, AKI and confusion mimicking TTP.
- **Rubric:** 5 = falciparum malaria (severe or not) with H04 cited; 4 = falciparum malaria without it; 3 = other or unspecified malaria species, or malarial haemolysis; 2 = TTP, another TMA, DIC, sepsis, enteric fever or gastroenteritis; 1 = anything else.
- **Must-do (8):** travel history; films or rapid test; grade severity (glucose plus a parasite count); artemisinin treatment (artesunate or artemether-lumefantrine); IV fluids; monitor parasites and counts; red cell transfusion; notify public health.
- **Must-not-do (5):** plasma exchange; high-dose steroids, rituximab or caplacizumab; sending her home or treating gastroenteritis without malaria tests; chloroquine; platelet transfusion without bleeding.

## Curator's decisions

Atul delegated these open questions. Every judgement call is also flagged in `curation/affected.json`, and they lead the review pack.

1. **Units.** Everything is in SI, with the printed values in each `note`. The text's "10.6 mg/dL" haemoglobin is a misprint for g/dL. Urea is BUN 35 mg/dL ÷ 2.8 = 12.5 mmol/L. Haptoglobin "<10 mg/dL" becomes <0.10 g/L. Hct values keep three decimals, so that MCHC and MCV agree.
2. **Day numbering.** Table 1's "Day 2/4/7/9" are kept as days 2, 4, 7 and 9, with admission as day 0. This matches the article's own labels. The alternative reading, with admission as day 1, would shift everything by one day.
3. **LDH on day 0.** The table's 287 U/L is used. The text's 289 is the table's day-2 value.
4. **Haptoglobin on day 0.** Table 1 says "NA", but the text reports <10 mg/dL at presentation, so day 0 is taken from the text.
5. **ADAMTS13 day.** Not dated, so day `null`. The catalogue's 3-day turnaround sets when players see it.
6. **Follow-up at one month.** Kept out of the facts (it would stretch the case days to about 40) and recorded in the ground truth's `outcome`, as for PMC12007988.
7. **Parasitaemia.** A new test, `LAB.HAEM.MALARIA_PARASITAEMIA`. Figure 2, read on 26 Sep 2026, gives days 2–6 as article facts (series S09; treatment started on day 2 at 5%). Days 0 and 1 are not plotted, so they are affected judgement calls at 5%, the first measured value, which smear report RP01 also quotes. The earlier reviewer row (2.8%) and the estimates for days 1–4 were removed. Figure 2 itself (M02) stays debrief only, unlinked from R02, because it names the parasite and marks the day treatment started.
8. **Severe or uncomplicated.** Confusion, AKI and a parasitaemia of 5% (the CDC threshold) meet CDC and WHO-style criteria for severe malaria, but the team gave oral artemether-lumefantrine. The rubric accepts both diagnosis ids at score 5, and the must-do accepts either artesunate or artemether-lumefantrine. The consult note recommends IV artesunate while she is confused or vomiting.
9. **GCS 14 and vital signs** (38.7 °C, pulse 114, BP 104/62, RR 22, SpO₂ 97%): judgement calls. A GCS of 11 or below would define cerebral malaria, which the article does not describe.
10. **The antibiotic** from the first visit is ciprofloxacin 500 mg twice daily, started four days earlier (a judgement call). The ED note records gastroenteritis with no blood tests (a judgement call) and says nothing about travel.
11. **Microcytosis.** MCV 74–80 fL and MCH about 25 pg are present from admission, but the article never explains them. Proposed: homozygous α⁺-thalassaemia (−α3.7/−α3.7), with a normal HPLC and high ferritin (an acute-phase response; low iron and a TSAT of 12% from inflammation). A family history of mild microcytic anaemia and a clinic count from two years earlier (MCV 78) support it. **All four are judgement calls**, and they imply West African ancestry, which the article does not state. The alternative is to leave the microcytosis unexplained, with a normal alpha-globin result.
12. **The white count** is not reported. It is set normal-to-low with lymphopenia, which is typical of falciparum malaria (a judgement call on day 0).
13. **The creatinine peak** (186 µmol/L on day 2) and its recovery to 80 by day 9 are a judgement call. The article says only "acute kidney injury".
14. **Procalcitonin** is 3.85 µg/L, raised without bacteraemia (a judgement call). It is realistic, and it sets up the sepsis trap.
15. **Dark urine**, "like strong tea", comes from concentration and a little free haemoglobin (dipstick trace blood, no red cells). This is a judgement call; it is not blackwater fever.
16. **Other patient details**, from rules 8–9: no rigors in the article, but rigors are set as present (a judgement call; common and non-specific); yellow fever vaccine (a judgement call); mosquito bites (a judgement call); a home health aide living in Brooklyn; postmenopausal; three pregnancies; blood group O RhD positive; height 162 cm and weight 71 kg.
17. **Films.** The screening film (RP02) shows ring forms and asks for thick and thin films, without naming the species. The haematopathologist review (RP03) names *P. falciparum* and says the schistocytes are too few to support a primary TMA. The smear (RP01) is the confirmatory test.
18. **Leak terms.** The accepted synonyms are specific ("falciparum malaria", "Pf malaria" and so on). Bare "malaria" is not a leak term, so a consultant can say "exclude malaria" and test names stay usable. Notes written after parasites are found say "Plasmodium falciparum infection" rather than "falciparum malaria".
19. **Birthplace (`HX.SOCIAL.RESIDENCE`, added to the catalogue in the merge):** born and brought up in Nigeria, in Brooklyn for over 20 years (a judgement call). It is consistent with decision 11 and a visiting-friends-and-relatives traveller, and it replaces the new template 'born locally', which would contradict both. The alternative is to leave her origin unstated.
20. **Reviewer rows:** none since the figure check (the day-0 parasitaemia row was replaced by Figure 2's values and an affected estimate).
21. **Platelets from Figure 1** fill days 1, 3, 5, 6 and 8 (series S10). On day 4 the figure (about 93) and Table 1 (102) differ; the table is kept.

## Counts (local replay, 25 Sep 2026)

- **Facts:** 75 article (11 history, examination and interpretation facts, 50 series points, 14 single results); 5 derived (MCHC).
- **Ledger (after the figure check):** 336 affected (306 written, the rest calculated from affected inputs), 0 reviewer, 2 rule, 1,552 normal.
- **Judgement calls:** 20.
- **Reports:** 8, all `only` and final (smear, screening film, film review, chest X-ray, CT abdomen and pelvis, ultrasound abdomen, ultrasound kidneys, CT head).
- **Consult notes:** 22. There are 9 `affected` notes: infectious diseases ×3 (before travel is known, after travel, after parasites), haematology ×2 (before and after parasites), gastroenterology, neurology, nephrology and general surgery. The other 13 are `rule` generic notes.
- **Test utility:** 78 tests.
- **Lay texts:** 57 in all: 4 for article facts in `lay_text.json`, and 53 on the affected history rows.

## Catalogue needs (`catalogue_needs.json`)

| Kind | Id | Why |
| --- | --- | --- |
| History | `HX.SOCIAL.TRAVEL_PROPHYLAXIS` | Prophylaxis question; normal template "No travel for which antimalarial prophylaxis would be needed." |
| Test | `LAB.HAEM.ADAMTS13` (`CMP.ADAMTS13_ACT`) and `LAB.HAEM.ADAMTS13_INHIBITOR` (`CMP.ADAMTS13_ANTIBODY`) | The TTP work-up; merged by the lead curator with the same tests from other cases (activity and inhibitor are now separate tests) |
| Test | `LAB.HAEM.MALARIA_PARASITAEMIA` (`CMP.MALARIA_PARASITAEMIA`, %) | Daily parasite counts; severity and response |
| Test | `LAB.GI.GIARDIA_AG` (`CMP.GIARDIA_AG`) | Article test; common in Indian practice |
| Action | `RX.ANTIMALARIAL.ARTEMETHER_LUMEFANTRINE` | The treatment given; oral ACT |
| Action | `RX.IMMUNO.CAPLACIZUMAB` | TTP-directed must-not-do; reusable for TTP cases |

That made 6 items (1 history, 3 tests, 2 actions), 4 components and 1 normal template. The lead curator has merged them into `catalogue/*.csv` and removed `catalogue_needs.json`; the activity component is now `CMP.ADAMTS13_ACT`, and the antibody has its own test. The tests are priced as `estimate` (INR 9,000, 150 and 1,200). The ranges come from Dacie and Lewis (ADAMTS13 activity), Tietz (antibody), WHO Basic Malaria Microscopy (parasitaemia) and Mackie and McCartney (Giardia antigen). **To verify:** the ADAMTS13 antibody range is assay-specific, and the source should be checked. The lead curator may merge the ADAMTS13 test with the same test proposed from other cases.

## Case Reviewer checklist

- [ ] Every fact against the article: Table 1 (40 points), the admission values in the text, and the negative tests.
- [ ] Day numbering (decision 2) and the LDH and haptoglobin choices on day 0 (decisions 3 and 4).
- [x] Figure 2 read (S09) and Figure 1 read (S10) on 26 Sep 2026; RP01 updated to 5%.
- [ ] Check the values read from both figures, and the 5% estimate for days 0 and 1.
- [ ] The microcytosis explanation (decision 11): accept α⁺-thalassaemia, or leave it unexplained.
- [ ] Severe or uncomplicated, and whether the rubric and must-do should prefer artesunate (decision 8).
- [ ] Judgement calls in `curation/affected.json` (20), especially GCS, vital signs, creatinine peak, ED note and antibiotic.
- [ ] Consult notes: infectious diseases and haematology before the travel history. Are they too leading?
- [ ] Figure flags: both charts are annotated; mask or crop the axis labels before production use.
- [ ] Catalogue needs: ids, prices, turnaround and the ADAMTS13 antibody range source.

## Figure check (2026-09-26)

The images were downloaded from PMC and looked at one by one.

- M02 (Figure 2, parasitaemia chart) unlinked from the parasitaemia result: its title names Plasmodium falciparum and it marks the day treatment started, so a player would see later days and the treatment. Debrief only.
- Done 26 Sep 2026: days 2–6 read from the chart into series S09 (5, 1.6, 0.6, 0, 0%); the reviewer row and the estimates for days 1–4 removed; days 0–1 set at 5% (affected); RP01 now quotes 5%. Figure 1 read into series S10 (days 1, 3, 5, 6, 8).
