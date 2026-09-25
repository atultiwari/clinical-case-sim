# Case Library: implementation plan

How to use this file: work top to bottom. Pick the first unchecked task whose dependencies are done, restate its acceptance criteria, write the tests first, then build. When it passes, tick the box and add a one-line note (date, what changed). Tasks marked **[human]** need Dr Atul Tiwari: prepare everything he needs, tell him exactly what to check, and move on to the next task you can do.

Design: [SPEC.md](SPEC.md). Shared decisions: [`../../docs/DECISIONS.md`](../../docs/DECISIONS.md). Pilot: [`../cases/PMC12949993/`](../cases/PMC12949993/).

These tasks were in Nidana's plan (version 0.1) before the umbrella was created.

## Milestones

| Milestone | Done when |
| --- | --- |
| LM0 | The Case Vault runs; catalogue v1 is reviewed; the Case Studio shows the pilot; the pilot is frozen and exported as `PMC12949993@v1.r1` with 100% coverage |
| LM1 | Ten cases are frozen and exported |

---

## Phase 0: the Case Vault and the pilot

- [x] **L0.1 Case Library scaffold**
  - Done 2026-09-25: uv project (ruff, mypy, pytest-cov), `scripts/config.py`, `.env.example`, local Supabase on ports 553xx (543xx was taken by another project), pre-commit hooks and the `case-library` workflow; 26 tests pass.
  - Build: inside the monorepo (umbrella task U0.1), a uv project in `case-library/` with ruff, mypy and pytest; the Supabase CLI for a local database (`supabase start`) used by migration and integration tests; `.env.example` with `CASE_VAULT_DB_URL_READONLY`, `NCBI_API_KEY` and `NCBI_EMAIL`; `review/` and `data/` git-ignored (the root `.gitignore` already covers them); the Case Library's hooks in the root `.pre-commit-config.yaml` and its GitHub Actions workflow (lint, type-check, tests), limited to `case-library/`.
  - Accept: `uv run pytest`, run in `case-library/`, passes on a fresh clone; `supabase start` brings up the local database.
  - Depends on: U0.1.

- [x] **L0.2 [human] Case Vault project and MCP** (done 2026-09-25: connector limited to the Case Vault by hook and deny rules; see the last note)
  - Build: create the Supabase project `case-vault` on the Free plan, in any region (see CLAUDE.md, Stack). Atul creates it in the dashboard, or approves Claude creating it through the account-level connector. Add `case-library/.mcp.json` with the project-scoped URL (SPEC §4.1). Keep manual approval for `execute_sql` and `apply_migration`. If Claude Code can see the account-level Supabase connector, add `nidana/.claude/settings.json` and `sambhasha/.claude/settings.json` that deny its tools.
  - Accept: in Claude Code started in `case-library/`, the Supabase MCP lists tables for this project only, and no account tool can be used. Sessions started in `nidana/` or `sambhasha/` cannot use any Supabase tool. In terminal and IDE sessions the account-level connector is not loaded at all (`disableClaudeAiConnectors`). The desktop app delivers connectors itself and no project setting hides them, so there its tools are listed but every call is refused by the deny rules in each part's `.claude/settings.json`.
  - Note (2026-09-25): Atul accepted "listed but refused" for the desktop app, so the connector stays in claude.ai for reading cases in chat and Cowork (SPEC §4.1).
  - Note (2026-09-25): Atul created `case-vault` (ref `vxiymbaxsiavxuyxzhnt`, Tokyo) and deleted VRL-App-Demo, so the Free plan's two-project limit is not a concern.
  - Note (2026-09-25): Atul chose the account-level connector over the project-scoped `.mcp.json`, which needed a separate sign-in that the desktop app cannot run. `.mcp.json` is removed. In `case-library/` the connector is allowed but limited: the hook `.claude/hooks/case-vault-only.sh` refuses any project other than the Case Vault, deny rules block the account tools, and `execute_sql` and `apply_migration` ask for approval. `nidana/` and `sambhasha/` still deny the connector completely. Checked: `list_tables` on the Case Vault works (no tables yet); `pause_project` on another project is refused by the hook; `confirm_cost` is refused by the deny rule.
  - Depends on: L0.1.

- [x] **L0.3 Schema 0.3** (done 2026-09-25: schema applied locally and to the Case Vault; nightly dump running from the LaunchAgent)
  - Build: migration files in `supabase/migrations/` for the `casevault` tables in SPEC §10.2, applied through `apply_migration`. The schema is not exposed to the Data API; RLS is on with no client policies. The immutability trigger for frozen case versions (with the figure-decision exception); the ledger trigger (insert-only, review fields once, supersession); the live-row index with `nulls not distinct`; the check that an `original` report is provisional and has a status line; the private storage bucket `case-media`. SQL functions: `import_case_json`, `compute_derived`, `resolve_normals`, `check_consistency`, `leak_scan`, `coverage_report` and `export_bundle`. The bundle JSON Schema `schemas/case-bundle.v0.3.schema.json`. A nightly dump of the `casevault` schema only, through the session pooler with a Postgres 17 client, run by a scheduled job on the VPS or Atul's machine.
  - Accept: `supabase db reset` applies the migrations cleanly on the local database, and they apply on the Case Vault project. SQL tests on the local database show that updating a fact of a frozen case fails; that a second live ledger row for the same target and day fails, including when `day_bucket` is null; that an approved ledger row can change only to `superseded`; and that exporting a fixture case twice gives byte-identical files with the same SHA-256. `get_advisors` reports no security warnings for the `casevault` schema. The first nightly dump exists.
  - Note (2026-09-25): applied to the Case Vault through the connector as seven migrations (tables, integrity, import, resolve, export, the `case-media` bucket, foreign-key indexes). Local file names carry the versions the Case Vault recorded, so both histories match. A structural fingerprint (functions, columns, constraints, triggers, indexes) is identical locally and in the Case Vault. `get_advisors` security: no warnings; only the intended INFO notice that RLS is on with no client policies. Performance: only "index not yet used" on the empty database. Still open: the nightly dump (on Atul's Mac for now).
  - Note (2026-09-25): nightly dump built: `scripts/backup_case_vault.py` (casevault schema only, via `supabase db dump` so pg_dump matches Postgres 17; password passed in PGPASSWORD, never on the command line; keeps 14; refuses a dump holding `play`) and a LaunchAgent in `scripts/launchd/` (02:30 daily, on Atul's Mac for now). A manual run succeeded and restored cleanly into a scratch database (24 tables, 38 functions, 13 triggers). The LaunchAgent could not run from `~/Downloads` (macOS privacy protection), so Atul is moving the project to `~/Projects`. After the move: run `scripts/launchd/install_backup_agent.sh`, then `launchctl kickstart gui/$(id -u)/local.clinical-case-sim.casevault-backup`, and check `~/CaseVaultBackups/backup.log`. That first scheduled dump closes L0.3.
  - Note (2026-09-25): after the move to `~/Projects/research`, the LaunchAgent was installed and started with `launchctl kickstart`; it exited 0 and `~/CaseVaultBackups/backup.log` records `backup ok` (schema.sql 83,468 bytes, data.sql 7,827 bytes). Scheduled runs follow at 02:30.
  - Depends on: L0.2.

- [x] **L0.4 Catalogue v0** (done 2026-09-25: loaded into the Case Vault as the reviewed v1; see the notes)
  - Build: CSV files in `catalogue/` for history questions (about 120), examinations (about 70), tests with components (about 200 tests), actions (about 100), referrals (about 15), diagnoses (about 300, ICD-11 with ICD-10 cross-reference) and findings (about 60). Each item has at least two synonyms. Tests have route, specimen, INR price (CGHS where available, otherwise estimated and flagged), turnaround and components; components have units, conversion factors, decimals and reference ranges with their source. Normal templates for history, examination, imaging and consult notes. Load through the MCP.
  - Accept: the load succeeds; every test has at least one component; every component has a unit and a reference range; every item has at least two synonyms; every item on the pilot's paths (`ANALYSIS.md` §5–§6) exists.
  - Note (2026-09-25): built on branch `case-library/L0.4-catalogue-v0`. CSV files in `catalogue/` (formats and rules in its README): 141 history questions, 68 examinations, 251 tests, 371 components with 397 reference ranges, 116 actions, 19 referrals, 492 diagnoses, 60 findings, 228 normal templates, 13 value rules. `scripts/catalogue.py check` enforces the acceptance rules; `tests/test_catalogue_content.py` checks every id in `ANALYSIS.md` and every laboratory result in the pilot. Interpretive tests carry one qualitative report component whose normal text is the imaging or report template. A qualitative component has normal text and a text range in place of a unit. Prices are all estimates, and 460 of 492 diagnoses have no ICD-11 code yet (left blank rather than guessed); both go to L0.5. `casevault.load_catalogue` is applied to the Case Vault, and the whole catalogue loads into the local database. At over 450 KB the data is too large to type through the connector, so Atul chose to hold the Case Vault load until the reviewed catalogue v1 (L0.5); L0.4 closes then.
  - Note (2026-09-25): closed with L0.5; catalogue v1 is in the Case Vault (see L0.5).
  - Depends on: L0.3.

- [x] **L0.5 [human] Catalogue review** (done 2026-09-25: Atul approved the pack as a whole; recheck before the production release)
  - Build: a catalogue review pack (Excel) covering reference ranges and their sources, normal templates, prices and turnaround. Atul decides; Claude applies the decisions and records catalogue v1 in `../../docs/CHANGELOG.md`.
  - Accept: no undecided rows; catalogue version 1 recorded. Can run in parallel with L0.6–L0.9.
  - Note (2026-09-25): Atul approved the catalogue in chat ("I approve it for now"), to be checked again before Nidana's production release. On his instruction Claude filled every row of the pack (`review/catalogue-v1/catalogue-review-v1.decided.xlsx`, not in Git): ranges, prices, turnaround and diagnosis codes approved as proposed; the 54 normal texts with an audit suggestion take it; the nine questions take Claude's recommendation, except Q1 (neutral texts for v1 rather than a new column). Catalogue v1 is recorded in `../../docs/CHANGELOG.md`. Atul chose to skip the v0 load: v1 was loaded into the Case Vault in four parts through the dashboard's SQL editor (Claude, in Atul's Chrome, with his permission), and five rows with non-ASCII text that the clipboard had mangled were reloaded through the MCP. All seven catalogue tables then matched the local build's fingerprints exactly. 801 items keep `since_version = 0` from the earlier partial v0 load; the other 346 show 1.
  - Depends on: L0.4.

- [x] **L0.6 Curation skill v0.1** (done 2026-09-25: skill, 17 SQL snippets, dry-run planner and case review pack; see the note)
  - Build: `.claude/skills/case-curate/` with `SKILL.md` (SPEC §4.3–§4.4 and §6), templates and SQL snippets; the review pack builder and reader in `scripts/`, which the skill calls.
  - Accept: invoking the skill on the pilot in dry-run mode lists every step and the SQL it would run without writing anything; the review pack builder produces a workbook from a fixture.
  - Note (2026-09-25): `.claude/skills/case-curate/` holds `SKILL.md` (protocol, affected-value rules, never-do list), `sql/` (one snippet per writing call, with step, writes and params headers) and `templates/`. `python -m scripts.curate_plan cases/PMC12949993` prints the 11 steps and 15 writing calls without connecting; an integration test runs every snippet in order on the local database. `python -m scripts.review_pack build|read` builds the SPEC §7.2 workbook through a read-only connection and reads the returned decisions into JSON; `tests/integration/test_review_pack.py` builds it from the fixture case. It needs the read-only role from L0.7 to run `leak_scan` and `reference_range` on the Case Vault. Branched from L0.5, so it merges after L0.4 and L0.5.
  - Depends on: L0.3.

- [ ] **L0.7 Case Studio v1 (read-only)**
  - Build: `studio/`, a Next.js app (package `@case-library/studio`) with the screens in SPEC §8, reading the Case Vault server-side through a read-only database role; licence badges on cases and figures; no Supabase Auth; a separate login and an allow-list if deployed.
  - Accept: the Studio lists the fixture case and the pilot once imported, shows every tab, and cannot write (the role has no write rights); an anonymous Nidana tester's session cannot open it. Runs locally with `pnpm --filter @case-library/studio dev`.
  - Note (2026-09-25): built on branch `case-library/L0.7-case-studio` (from main). `casevault_reader` (migration `20260925132542`, applied to the Case Vault; the security advisor is now clean) reads every table and runs only the read functions; tests show it cannot write and that Nidana's `anon` and `authenticated` roles see nothing. The Studio (`studio/`, `@case-library/studio`) has every SPEC §8 screen; each query runs in a read-only transaction as `casevault_reader`. Checked locally on the fixture case; the pilot appears once L0.8 imports it. Waiting on Atul: create the `studio_reader` login role in the Supabase SQL editor (command in `studio/README.md`) and put its URL in `studio/.env.local`, never in Git or a chat.
  - Depends on: L0.3.

- [x] **L0.8 Pilot import** (done 2026-09-25: in the Case Vault with its figures; see the notes)
  - Build: import `cases/PMC12949993/gold-case-file.draft.json` as `PMC12949993@v1` in `draft` status through `import_case_json`. Link facts to catalogue ids; set `released_by` for history facts (`ANALYSIS.md` §3); compute derived values; import every figure with its licence and annotation flag.
  - Accept: 164 imported facts and raw-material rows (10 history, 125 series values, 26 single results, 3 raw material) plus the derived rows; 4 media rows with `has_annotations = true`, their own licence flags and their files in `case-media`; the ground truth; 20 rows in `casevault.gap`. SQL tests: `HX.MEDS.CURRENT` releases H03 and H04 only; `HX.EXPOSURE.TOXINS` releases H09 only; `HX.MEDS.SUPPLEMENTS` releases H10. Leak scan clean.
  - Note (2026-09-25): prepared on branch `case-library/L0.8-pilot-import` (from L0.6). The gold file now links every history fact to the questions that release it, every result to its component and every raw-material row to its test; figures carry `has_annotations` and a `case-media` path. Composite results are split into one article fact per component (values unchanged), so there are 35 single results rather than 26 and 170 facts in all. `tests/integration/test_pilot_import.py` imports the pilot on catalogue v0 locally and meets every acceptance check except the Case Vault ones. Still open: (1) the Case Vault import, which needs the catalogue loaded there (held until catalogue v1, L0.5), because `raw_material.test_item_id` references catalogue items; (2) uploading the figure files to `case-media`: the article has three figure images (Figure 2 holds panels A and B), downloaded with Atul's permission to `data/figures/PMC12949993/F1-F3.jpg` (750 px, SHA-256 in the session log); the connector cannot upload files, so Atul uploads them in the dashboard. Atul set the figures' own flags on 2026-09-25: `production_ok` and `public_release_ok` true (CC BY 4.0, no separate credit); all four carry arrows (`has_annotations`), so each still needs his use, mask or exclude decision before the store release.
  - Note (2026-09-25, later): imported into the Case Vault as `PMC12949993@v1` (draft) on Atul's instruction, through the dashboard's SQL editor in his Chrome: 191 facts (170 imported, 21 derived), 3 raw-material rows, 4 media rows, 20 gaps, the ground truth, and the article's JATS snapshot (SHA-256 verified in the database). The gold file gained the neutral title, tags, slug `c-6gizm` and the patient's opening words (step 5). Still open: the figure files in `case-media` (Atul uploads them; see `docs/DELEGATED-2026-09-25.md` on main).
  - Depends on: L0.4, L0.6.

- [x] **L0.9 Pilot resolution** (done 2026-09-25: `in_review`, coverage 100%, checks clean)
  - Build: following the skill, record the path analysis (`ANALYSIS.md` §5); write the `affected` and reviewer-placeholder rows (`ANALYSIS.md` §6); run the normal generator; apply rules; write the patient's words, report variants with status lines (`ANALYSIS.md` §4), consult notes (`ANALYSIS.md` §8, including the generic note) and test utility; express the rubric, must-do and must-not-do as conditions (`ANALYSIS.md` §9); run all checks.
  - Accept: `coverage_report` is 100%; consistency, contradiction and leak checks pass; the summary shows counts per origin and the list of judgement calls; status `in_review`.
  - Note (2026-09-25): prepared on branch `case-library/L0.9-pilot-resolution` (from L0.8). `cases/PMC12949993/curation/` holds the skill's inputs: 12 paths (124 items), 115 ledger rows (88 affected, 21 judgement calls, 6 reviewer placeholders), 1 rule, 16 reports (1 provisional), 22 consult notes (8 case-specific, 14 generic), 77 test utility ratings, the patient's words and the ground truth with conditions. The gold file gained the case's laboratory profile. Atul decided that a day without a result returns the latest earlier result (changelog entry; coverage and the normal generator follow it). `tests/integration/test_pilot_resolution.py` replays steps 4–11 locally: coverage 100%, consistency and leak checks clean, status `in_review`, with 993 normal and 21 derived rows. On the Case Vault this waits for the catalogue load (after L0.5) and Atul's approval of the normal templates.
  - Note (2026-09-25, later): in the Case Vault, steps 7–8 ran (12 paths; ledger 109 affected, 993 normal, 6 reviewer, 1 rule). The permission system refused the third dashboard paste (reports, consult notes, lay text, test utility, ground truth), so it waits for Atul: `build/pilot/C_author.sql`, then checks and hand-over. One generated normal row, `CMP.US_PELVIS_REPORT`, carries an authoring note from catalogue v1 (since removed from the catalogue); reject it in the pilot review.
  - Note (2026-09-25, final): Atul ran `build/pilot/C_author.sql` and uploaded F1–F3 to `case-media/PMC12949993/` (sizes match the local files). Claude then ran step 10 through the MCP (consistency, leak, coverage and export checks all empty) and step 11: status `in_review`. Summary: 170 article and 21 derived facts; ledger 88 affected, 21 judgement calls, 6 reviewer placeholders, 1 rule, 993 normal; 16 reports (1 provisional), 22 consult notes, 77 test utility ratings.
  - Depends on: L0.8.

- [x] **L0.10 [human] Pilot review** (done 2026-09-25: blanket approval by Atul, not reviewed item by item; see the note)
  - Build: build the pilot review pack; Atul reviews it with the Case Studio open, including the judgement calls in `ANALYSIS.md` §7 and the reviewer-set values (G14, G15); Claude shows a summary of his decisions and applies them after his go-ahead.
  - Accept: no `pending` rows for the pilot; every decision recorded in `review_decision`.
  - Note (2026-09-25): Atul chose a recorded blanket approval ("approve everything and proceed further for now"), after Claude explained that approving its own curation removes the human check. Applied through the MCP as batch `chat-2026-09-25-atul-blanket`: 1,338 decisions (1,328 approve, 10 edit), every row noted "blanket approval ... not reviewed item by item". The edits are Claude's proposals, accepted in that approval: the six reviewer placeholders (anti-cN1A not detected; anti-HBc non-reactive; urine arsenic 21 ug/L, urine mercury 6 ug/L, blood mercury 4 ug/L for G14; two pregnancies and no transfusions), the G15 marrow values in RP03-RP05 (cellularity about 60%, blasts 2%, ring sideroblasts 12%), whose report text still held "[to be set by the reviewer]", and the pelvic ultrasound normal (authoring note removed, female text). The curation files carry the same values, and `tests/test_curation_placeholders.py` now catches placeholder text in anything a player sees. **Because it was not reviewed item by item, the pilot must not count in a Sambhasha study's primary results** (invariant 1) until Atul reviews it properly; tell Sambhasha when it imports the bundle.
  - Note (2026-09-25): a separate session added `casevault.placeholder_scan` (migration `20260925165040_casevault_placeholder_scan`, applied to the Case Vault with Atul's approval; pull request #14): step 10 and `export_blockers` now refuse placeholder text and authoring notes in anything a player sees. On the pilot it finds nothing. Security advisors clean.
  - Depends on: L0.7, L0.9.

- [ ] **L0.11 Freeze and export**
  - Build: if catalogue v1 (L0.5) changed anything the pilot uses, re-run the resolution for those items and review the changed rows. Then, on Atul's word, freeze `PMC12949993@v1`, export bundle `PMC12949993@v1.r1` to `exports/` with its `.sha256` file, and mark it published for development.
  - Accept: coverage is 100% against catalogue v1; a second export gives byte-identical output; frozen rows cannot be changed; the bundle validates against `schemas/case-bundle.v0.3.schema.json`. Milestone LM0.
  - Depends on: L0.5, L0.10.

---

## Phase 1: the first ten cases

- [x] **L1.1 Case sourcing** (done 2026-09-25, ahead of LM0 at Atul's request: `cases/SHORTLIST-batch1.md`)
  - Build: Claude proposes about 15 open-access haematology case reports, scored with the pilot's selection criteria (`cases/PMC12949993/PILOT_CASE.md`), with their licence flags, plus two or three common presentations (for example iron deficiency from menorrhagia, B12 deficiency in a vegetarian, thalassaemia trait against iron deficiency) as report-based or de novo cases.
  - Accept: a shortlist with licence, flags, reasons and a score for each.
  - Note (2026-09-25): 25 E-utilities queries, 923 records screened, 39 full texts cached in `data/articles/`. About 15 CC-licensed candidates scored against the pilot's ten criteria (top: PMC12364935, visceral leishmaniasis misdiagnosed as SLE, 9/10), three common presentations (a von Willebrand report for menorrhagia; de novo NID-0001, B12 deficiency in a vegetarian, and NID-0002, thalassaemia trait at antenatal booking), and the catalogue areas the top five would add. Licences were read from each article's JATS `<license>` element because PMC's OA service returned 404; they are re-verified at L1.2. Scores may shift after the pilot review.
  - Depends on: LM0.

- [x] **L1.2 [human] Choose batch 1** (done 2026-09-25 by Claude on Atul's behalf: `cases/BATCH1.md`)
  - Build: Atul picks nine cases: Sambhasha's four starter cases (PMC11227049, PMC12007988, PMC11227436, PMC11890614) and five from the shortlist.
  - Accept: nine case ids recorded for the batch, each with its licence re-verified.
  - Note (2026-09-25): Atul delegated the choice. The four starter cases plus shortlist #1–#5 (PMC12364935, PMC13193864, PMC12643702, PMC11015937, PMC13400839), all CC BY 4.0, re-verified from the JATS licence element because PMC's OA service was still down. No CC BY-NC-ND reports and no de novo cases in batch 1. Atul can swap cases before L1.3 writes anything.
  - Depends on: L1.1.

- [ ] **L1.3 Curate batch 1**
  - Build: run the skill in batch mode on the nine cases; extend the catalogue where their paths need it (with a changelog entry).
  - Accept: nine cases `in_review` with 100% coverage and clean checks; one review pack for the batch.
  - Note (2026-09-25): started early at Atul's request, on branch `case-library/L1.3-batch1` (from L0.9). Steps 1–5 only for Sambhasha's four starter cases: `cases/<PMCID>/gold-case-file.draft.json` and `CASE.md` (with open questions for Atul). All import on catalogue v0 and pass `tests/integration/test_gold_files.py` (links, laboratory profile, leak scan). Paths and values wait for the pilot review (SPEC §7.1). Found across the four: the articles report conventional units (g/dL, mg/dL) while the catalogue and its formulas use SI, which needs one decision for every case; and each case needs catalogue items the catalogue lacks (listed in each CASE.md).
  - Depends on: L1.2.

- [ ] **L1.4 [human] Review batch 1**
  - Build: Atul reviews the pack; Claude applies his decisions and regenerates rejected rows; freeze and export on his word.
  - Accept: nine new bundles exported; ten cases in total. Milestone LM1.
  - Depends on: L1.3.

- [ ] **L1.5 Case Studio v2 (optional)**
  - Build: review decisions and per-figure production decisions in the Studio, written by Atul through the Studio's server into `review_decision`, as an alternative to the Excel pack.
  - Accept: a decision made in the Studio appears in `review_decision` and in the next export; Claude's writes still go only through the MCP.
  - Depends on: L0.7; Atul's preference.
  - Note (2026-09-25): Atul chose to build it, deployable to his VPS, with an in-app login (username and password for an allow-list in `STUDIO_USERS`, signed session cookie, rate limiting) instead of a login at the proxy; never Supabase Auth. Writes go through the role `casevault_studio_writer` (migration `20260925143811`), which can only insert Studio batches and review decisions and set the four figure-decision columns of `media`. Before use on the cloud Case Vault: apply that migration through the MCP, and Atul creates the `studio_writer` login role himself (`studio/README.md`).
  - Note (2026-09-25): the writer's row-level security now also checks case status: a review decision needs a target row that exists, in a case version listed in its batch, whose status is `draft` or `in_review`; a figure decision is refused once the version is retired (still allowed when frozen, SPEC §9).
  - Note (2026-09-25): migration `20260925143811_casevault_studio_writer` applied to the Case Vault through the MCP; security advisors clean. The `studio_writer` login role is still Atul's to create.

- [ ] **L1.6 Extension runs (recurring)**
  - Build: process missing requests from Nidana and out-of-catalogue requests from Sambhasha: add catalogue items, resolve them for every published case, review the `affected` rows, activate the items, record the catalogue version in the changelog and export new bundle revisions.
  - Accept: every missing request is mapped, added or ignored with a reason; revisions `r2` and later exist where coverage grew.
  - Depends on: LM1.

---

## Phase 2: release support

- [ ] **L2.1 Figure decisions and the publish job for the store release**
  - Build: first, a figure review pack (or the Studio v2, if L1.5 was built) for every production case; Atul decides use, mask or exclude for each figure; masking crops or covers marks with ordinary image editing, never AI; recording the decisions exports a new bundle revision. Then `scripts/publish.py` copies bundles with `production_ok = true`, and only figures with `production_ok` and a use or mask decision, plus the catalogue export, into Nidana's production database; it also exports new missing requests from production as a CSV.
  - Accept: publishing is idempotent (the same hash is a no-op); a development-only case, a figure without its flag and a figure still `pending` are each refused with a clear message.
  - Depends on: Nidana's store-release phase.
