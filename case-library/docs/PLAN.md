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

- [ ] **L0.4 Catalogue v0**
  - Build: CSV files in `catalogue/` for history questions (about 120), examinations (about 70), tests with components (about 200 tests), actions (about 100), referrals (about 15), diagnoses (about 300, ICD-11 with ICD-10 cross-reference) and findings (about 60). Each item has at least two synonyms. Tests have route, specimen, INR price (CGHS where available, otherwise estimated and flagged), turnaround and components; components have units, conversion factors, decimals and reference ranges with their source. Normal templates for history, examination, imaging and consult notes. Load through the MCP.
  - Accept: the load succeeds; every test has at least one component; every component has a unit and a reference range; every item has at least two synonyms; every item on the pilot's paths (`ANALYSIS.md` §5–§6) exists.
  - Depends on: L0.3.

- [ ] **L0.5 [human] Catalogue review**
  - Build: a catalogue review pack (Excel) covering reference ranges and their sources, normal templates, prices and turnaround. Atul decides; Claude applies the decisions and records catalogue v1 in `../../docs/CHANGELOG.md`.
  - Accept: no undecided rows; catalogue version 1 recorded. Can run in parallel with L0.6–L0.9.
  - Depends on: L0.4.

- [ ] **L0.6 Curation skill v0.1**
  - Build: `.claude/skills/case-curate/` with `SKILL.md` (SPEC §4.3–§4.4 and §6), templates and SQL snippets; the review pack builder and reader in `scripts/`, which the skill calls.
  - Accept: invoking the skill on the pilot in dry-run mode lists every step and the SQL it would run without writing anything; the review pack builder produces a workbook from a fixture.
  - Depends on: L0.3.

- [ ] **L0.7 Case Studio v1 (read-only)**
  - Build: `studio/`, a Next.js app (package `@case-library/studio`) with the screens in SPEC §8, reading the Case Vault server-side through a read-only database role; licence badges on cases and figures; no Supabase Auth; a separate login and an allow-list if deployed.
  - Accept: the Studio lists the fixture case and the pilot once imported, shows every tab, and cannot write (the role has no write rights); an anonymous Nidana tester's session cannot open it. Runs locally with `pnpm --filter @case-library/studio dev`.
  - Depends on: L0.3.

- [ ] **L0.8 Pilot import**
  - Build: import `cases/PMC12949993/gold-case-file.draft.json` as `PMC12949993@v1` in `draft` status through `import_case_json`. Link facts to catalogue ids; set `released_by` for history facts (`ANALYSIS.md` §3); compute derived values; import every figure with its licence and annotation flag.
  - Accept: 164 imported facts and raw-material rows (10 history, 125 series values, 26 single results, 3 raw material) plus the derived rows; 4 media rows with `has_annotations = true`, their own licence flags and their files in `case-media`; the ground truth; 20 rows in `casevault.gap`. SQL tests: `HX.MEDS.CURRENT` releases H03 and H04 only; `HX.EXPOSURE.TOXINS` releases H09 only; `HX.MEDS.SUPPLEMENTS` releases H10. Leak scan clean.
  - Depends on: L0.4, L0.6.

- [ ] **L0.9 Pilot resolution**
  - Build: following the skill, record the path analysis (`ANALYSIS.md` §5); write the `affected` and reviewer-placeholder rows (`ANALYSIS.md` §6); run the normal generator; apply rules; write the patient's words, report variants with status lines (`ANALYSIS.md` §4), consult notes (`ANALYSIS.md` §8, including the generic note) and test utility; express the rubric, must-do and must-not-do as conditions (`ANALYSIS.md` §9); run all checks.
  - Accept: `coverage_report` is 100%; consistency, contradiction and leak checks pass; the summary shows counts per origin and the list of judgement calls; status `in_review`.
  - Depends on: L0.8.

- [ ] **L0.10 [human] Pilot review**
  - Build: build the pilot review pack; Atul reviews it with the Case Studio open, including the judgement calls in `ANALYSIS.md` §7 and the reviewer-set values (G14, G15); Claude shows a summary of his decisions and applies them after his go-ahead.
  - Accept: no `pending` rows for the pilot; every decision recorded in `review_decision`.
  - Depends on: L0.7, L0.9.

- [ ] **L0.11 Freeze and export**
  - Build: if catalogue v1 (L0.5) changed anything the pilot uses, re-run the resolution for those items and review the changed rows. Then, on Atul's word, freeze `PMC12949993@v1`, export bundle `PMC12949993@v1.r1` to `exports/` with its `.sha256` file, and mark it published for development.
  - Accept: coverage is 100% against catalogue v1; a second export gives byte-identical output; frozen rows cannot be changed; the bundle validates against `schemas/case-bundle.v0.3.schema.json`. Milestone LM0.
  - Depends on: L0.5, L0.10.

---

## Phase 1: the first ten cases

- [ ] **L1.1 Case sourcing**
  - Build: Claude proposes about 15 open-access haematology case reports, scored with the pilot's selection criteria (`cases/PMC12949993/PILOT_CASE.md`), with their licence flags, plus two or three common presentations (for example iron deficiency from menorrhagia, B12 deficiency in a vegetarian, thalassaemia trait against iron deficiency) as report-based or de novo cases.
  - Accept: a shortlist with licence, flags, reasons and a score for each.
  - Depends on: LM0.

- [ ] **L1.2 [human] Choose batch 1**
  - Build: Atul picks nine cases: Sambhasha's four starter cases (PMC11227049, PMC12007988, PMC11227436, PMC11890614) and five from the shortlist.
  - Accept: nine case ids recorded for the batch, each with its licence re-verified.
  - Depends on: L1.1.

- [ ] **L1.3 Curate batch 1**
  - Build: run the skill in batch mode on the nine cases; extend the catalogue where their paths need it (with a changelog entry).
  - Accept: nine cases `in_review` with 100% coverage and clean checks; one review pack for the batch.
  - Depends on: L1.2.

- [ ] **L1.4 [human] Review batch 1**
  - Build: Atul reviews the pack; Claude applies his decisions and regenerates rejected rows; freeze and export on his word.
  - Accept: nine new bundles exported; ten cases in total. Milestone LM1.
  - Depends on: L1.3.

- [ ] **L1.5 Case Studio v2 (optional)**
  - Build: review decisions and per-figure production decisions in the Studio, written by Atul through the Studio's server into `review_decision`, as an alternative to the Excel pack.
  - Accept: a decision made in the Studio appears in `review_decision` and in the next export; Claude's writes still go only through the MCP.
  - Depends on: L0.7; Atul's preference.

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
