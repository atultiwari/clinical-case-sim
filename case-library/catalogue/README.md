# Catalogue

The global catalogue of the Case Library (SPEC §5): every history question, examination, test, component, action, referral, diagnosis and finding a player or a Sambhasha seat can ask for. Every case uses the same lists.

These CSV files are the source. Change the catalogue here, never in the database (CLAUDE.md), then:

```bash
uv run python -m scripts.catalogue check                 # validate every file
uv run python -m scripts.catalogue build --version 0     # write build/catalogue.v0.json
```

and load the JSON through the Supabase MCP with `select casevault.load_catalogue('<json>'::jsonb)`. A change to an active item is a shared-contract change (`../../docs/CHANGELOG.md`).

## Files

All files are UTF-8 CSV with a header row. Lists inside a cell are separated by `|`. Empty cells are empty strings.

| File | One row per | Columns |
| --- | --- | --- |
| `history.csv` | history question (`HX.<area>.<item>`) | `id,name,category,synonyms,specialty_scope` |
| `exam.csv` | examination (`EX.<system>.<item>`) | `id,name,category,synonyms,specialty_scope` |
| `tests.csv` | test (`LAB.*`, `IMG.*`, `PROC.*`) | `id,name,category,synonyms,specialty_scope,route,specimen,price_inr,price_source,tat_minutes,invasive,loinc,components` |
| `components.csv` | component (`CMP.<analyte>`) | `id,name,loinc,unit_si,unit_conv,conv_factor,decimals,normal_text` |
| `component_ranges.csv` | reference range | `component_id,sex,age_min,age_max,low,high,text,display,source` |
| `actions.csv` | action (`RX.<class>.<item>`, `ACT.<item>`) | `id,name,category,synonyms,specialty_scope` |
| `referrals.csv` | referral (`REF.<specialty>`) | `id,name,category,synonyms,specialty_scope` |
| `diagnoses.csv` | diagnosis (`DX.<slug>`) | `id,name,category,synonyms,specialty_scope,icd11,icd10,codes_verified` |
| `findings.csv` | finding (`FND.<finding>`) | `id,name,category,synonyms,specialty_scope,shown_by` |
| `normal_templates.csv` | normal reply for a history, examination or referral item | `item_id,template,review_status` |
| `value_rules.csv` | formula or physiology check (`casevault.value_rule`) | `id,kind,target,inputs,factor,tolerance_pct,formula` |

## Rules the checker enforces

- **Ids** follow the patterns above: capitals, digits, `_` and `.` only. Ids are unique across all files.
- **Synonyms:** at least two per item, none equal to the name, no duplicates. Include the words a student or an Indian clinician would type (abbreviations, brand-free lay terms, British and American spellings).
- **Specialty scope:** `attending`, `consultant.*`, `consultant.<specialty>` (the lower-case suffix of a `REF.*` id, for example `consultant.haematology`) or `service.pathology`, `service.radiology`, `service.microbiology`.
- **Tests:** `route` is `direct`, `service.pathology`, `service.radiology` or `service.microbiology`. `price_source` is `CGHS …` (naming the rate list: `CGHS 2025, Tier I NABH (OM 03.10.2025)`), `reviewer` (set by Atul) or `estimate` (flagged: not yet matched to a CGHS rate). `tat_minutes` follows Sambhasha's turnaround defaults (SPEC §10.4 there). `invasive` is `true` or `false`. `components` lists at least one component, in report order.
- **Interpretive tests** (films, imaging, endoscopy, marrow, histology, nerve studies) have one qualitative report component, `CMP.<TEST>_REPORT`, whose `normal_text` is the reviewed normal report. The normal generator uses it off the case's paths; on a path the case's own report resolves the test (SPEC §6.8). These are the imaging and report normal templates.
- **Components:** a numeric component has `unit_si`, `decimals` and at least one numeric range (`low` and `high`). A qualitative component has `normal_text` and at least one range whose `text` is the normal result (for example `Negative`); its unit may be empty. `conv_factor` converts SI to conventional: conventional = SI × factor.
- **Ranges:** `sex` is `F`, `M` or `any`; ages are in years (empty = no limit). `display` is how a laboratory prints the range when it differs from `low-high` (for example `<5`); one-sided ranges still carry a realistic `low` and `high` for the normal generator. `source` names the reference (the textbook per area, see below).
- **Diagnoses:** `icd10` and `icd11` codes. `codes_verified` is `false` until the codes have been checked against the WHO browsers (L0.5); ICD-11 is licensed CC BY-ND 3.0 IGO.
- **Findings:** `shown_by` lists the tests that can show the finding.
- **Normal templates:** one per history and examination item, and one generic consult note per referral. Written in the words a clinician would record, never naming a diagnosis. `review_status` is `pending` until Atul approves the template in a catalogue review, then `approved`; the normal generator uses approved templates only.
- **Value rules:** `kind` is `ratio`, `difference`, `not_above` or `sum_equals`, with `inputs` and `target` naming components (SPEC §10.2).

## Reference range sources

| Area | Source |
| --- | --- |
| Haematology | Bain BJ, Bates I, Laffan MA (eds). *Dacie and Lewis Practical Haematology*, 12th ed. Elsevier, 2017 |
| Chemistry, endocrinology, toxicology | Rifai N (ed). *Tietz Textbook of Laboratory Medicine*, 7th ed. Elsevier, 2022 |
| Immunology, serology, microbiology | *Tietz Textbook of Laboratory Medicine*, 7th ed., unless the result is qualitative |
| Bedside physiology and procedures (ECG, echocardiogram, spirometry, lumbar puncture, endoscopy) | Loscalzo J et al. (eds). *Harrison's Principles of Internal Medicine*, 21st ed. McGraw Hill, 2022 |

Drug and toxin levels for substances a person is not normally exposed to (paracetamol, salicylate, ethanol, digoxin, lithium) are qualitative with the normal result `Not detected`, so the normal generator never invents a level for a patient who is not taking them.

These are open item O-1 of SPEC §5.3: Atul reviews them once in L0.5.
