# Sambhasha: implementation plan

How to use this file: work top to bottom. Pick the first unchecked task whose dependencies are done, restate its acceptance criteria, write the tests first, then build. When it passes, tick the box and add a one-line note (date, what changed). Tasks marked **[human]** need Dr Atul Tiwari. Prepare everything he needs, tell him, and move to the next task you can do.

Design: [SPEC.md](SPEC.md). Decisions: [DECISIONS.md](DECISIONS.md). Pilot: [`../../case-library/cases/PMC12949993/`](../../case-library/cases/PMC12949993/). Case curation now happens in the Case Library ([`../../case-library/docs/PLAN.md`](../../case-library/docs/PLAN.md), D-021); its milestone LM0 delivers the pilot bundle.

## Milestones

| Milestone | Done when |
| --- | --- |
| M0 | The pilot bundle `PMC12949993@v1.r1` from the Case Library (LM0) imports cleanly and passes the import-time leak scan (reached 26 Sep 2026, P0.6) |
| M1 | The pilot runs end to end with the fake model (deterministic) and with live models; every invariant test passes |
| M2 | The Phase 2 study protocol is pre-registered and the first scored batch has run in Inspect AI |
| M3 | Superseded: the teaching game is Nidana (D-027) |
| M4 | The paper is submitted, citing the DOI of the research release (umbrella task U1.1) |

---

## Phase 0: foundations and case import

- [x] **P0.1 Repository scaffold**
  - Done 26 Sep 2026: uv project (`uv_build`, Python 3.12) with `pydantic` and `typer`, a `sambhasha version` command, strict mypy with the pydantic plugin, pytest with an 80% coverage floor and integration tests deselected by default; Sambhasha hooks in the root pre-commit config; `.github/workflows/sambhasha.yml`. On a fresh clone `uv sync --locked`, `uv run pytest`, `uv run ruff check .`, `uv run mypy` and `pre-commit run --all-files` pass.
  - Build: inside the Clinical-Case-Sim monorepo (umbrella task U0.1), a uv project in `sambhasha/` with the package `sambhasha` in `src/`; ruff, mypy and pytest configured; its hooks in the root `.pre-commit-config.yaml`; `.env.example` with `OPENROUTER_API_KEY`, `OLLAMA_BASE_URL` and `SUPABASE_DB_URL`; `.env` and `data/` git-ignored (the root `.gitignore` already covers them); a short `README.md`; the part's GitHub Actions workflow running lint, type-check and unit tests, limited to `sambhasha/`.
  - Accept: `uv run pytest`, `uv run ruff check .` and `uv run mypy src` all pass on a fresh clone.
  - Depends on: U0.1.

- [x] **P0.2 Domain models and JSON schemas**
  - Done 26 Sep 2026: Pydantic models in `src/sambhasha/domain/` for the schema 0.3 bundle (strict parsing, every problem listed with its location), conditions (both layouts of `finding_released`), actions, events, orders, seat and service views, and scores; a parity test keeps them in step with the Case Library's JSON schema. The newest bundle of every case validates (all 17 exports parse); the pilot has 125 series points. Written against the real pilot bundle, so the 0.2 stand-in was not needed. The six bundles that first failed were fixed in the Case Library (L1.7 widened the schema, L1.8 re-exported them in one layout). 167 tests, 99% coverage.
  - Build: Pydantic models in `src/sambhasha/domain/` for the case bundle (schema 0.3, generated from `../case-library/schemas/case-bundle.v0.3.schema.json`; Case Library SPEC §10), actions (§6), events, orders, seat views and scores. Until the pilot bundle exists, copy the pilot draft (`../case-library/cases/PMC12949993/gold-case-file.draft.json`, schema 0.2) to `tests/fixtures/pilot/` as a stand-in. Closes the Sambhasha item of the 25 Sep 2026 entry in `../docs/CHANGELOG.md` together with P0.6.
  - Accept: the pilot bundle validates once LM0 is reached (the draft validates against the 0.2 models until then); series expand to 125 atomic facts; ids are unique; invalid files (a missing licence, an unknown `release` value or origin) are rejected with clear messages.
  - Depends on: P0.1.

- [x] **P0.3 Database and repositories**
  - Done 26 Sep 2026: Sambhasha's own local Supabase project (ports 563xx) with migration `20260926180000_sambhasha_schema.sql`: the case registry, the bundle row tables (typed key columns plus each row as imported), eligibility kept apart, the synthetic ledger, runs, the Event Log, orders and scores. A trigger refuses any change to a sealed bundle's rows, another any update, delete or truncate of an event, and the case tables refuse truncate. `storage/repo.py` defines the interface; the in-memory and Postgres repositories pass the same contract suite (the pilot bundle round-trips unchanged). `supabase db reset` applies cleanly; CI gains a job that runs every test against the local database.
  - Build: `supabase init`, then migrations for the SPEC §12 tables; an immutability trigger for frozen cases; an insert-only `event` table. A repository interface with in-memory and Postgres implementations.
  - Accept: `supabase db reset` applies cleanly. The same contract test suite passes against both implementations. Updating a frozen case's fact fails. Updating or deleting an event fails.
  - Depends on: P0.2.

- **P0.4 PMC fetcher and licence gate — moved to the Case Library** (D-021; Case Library SPEC §4.4, steps 1–3). Nothing to do here.

- [x] **P0.5 Leak scanner and redaction**
  - Done 26 Sep 2026: `curation/leakscan.py` follows the Case Library's `leak_scan` rules. Terms are the ground truth's synonyms and leak terms plus the catalogue's names for the diagnosis. Allowed phrases are every catalogue test name and synonym and the case's own test names. Matching ignores case and spacing and respects word boundaries. `scan_bundle` covers every seat-facing text and skips the ground truth, `never` facts and confirmatory facts. `curation/redact.py` blanks leaked terms in text generated at run time; titles, keywords, captions and discussion are removed in the Case Library (D-021). The seeded pilot leaks are caught in a vignette, a caption and a narrative; "blood lead", "lead level" and "PNH flow cytometry" are not flagged; the newest bundle of every case scans clean. The importer (P0.6) calls `scan_bundle(bundle, Lexicon.from_bundle(bundle, CatalogueNames.load()))`.
  - Build: `curation/leakscan.py` scans text against the diagnosis, its synonyms and case-specific pathognomonic phrases; the importer runs it on every bundle as a second line of defence behind the Case Library's own scan. `curation/redact.py` strips titles, keywords, captions and discussion from seat-facing text.
  - Accept: seeded leaks are caught. For the pilot these include "lead poisoning", "plumbism", "saturnism" and "lead toxicity" in a vignette, a caption and a synthetic narrative. Test names such as "blood lead" are not flagged.
  - Depends on: P0.2.

- [x] **P0.6 Bundle importer**
  - Done 26 Sep 2026, milestone M0: `sambhasha case import` and `sambhasha case list` (`curation/importer.py`). The importer checks the `.sha256` file and the file's bytes, validates schema 0.3, refuses a file not named for its bundle, leak-scans (P0.5) and stores the bundle sealed, marked not eligible (S-010). `PMC12949993@v1.r1` imports with 191 facts (10 history, 125 series points, 35 single results, 21 derived; the PLAN's 26 single results came from the 0.2 draft, and the Case Library curated 35), 1,109 ledger rows, 16 reports, 22 consult notes, 3 raw material, 4 media and 20 gaps, with no leaks; the newest bundle of every case imports, and the primary analysis admits none. A wrong hash, a changed byte, a missing or foreign `.sha256`, schema 0.2, a leak and a second import are refused. Run by hand into the local database: imported, re-import refused, a fact update refused by the database.
  - Build: `sambhasha case import <bundle.json>` validates a Case Library bundle (schema 0.3), checks the SHA-256 of the file's bytes against its `.sha256` file, writes the case tables (facts, ledger rows, reports, consult notes, media, gaps, ground truth) and runs the leak scanner on all seat-facing text. It records the bundle revision; it never writes to the Case Vault. The case registry carries a `primary_eligible` flag that the primary analysis honours. Every case committed to this repository is development-only (S-010), so every bundle it imports today, the four starter cases included, is not eligible; only cases from the future private study set can be. Closes the Sambhasha items of the three 26 Sep 2026 eligibility notices in `../docs/CHANGELOG.md`.
  - Accept: every current bundle imports as not eligible, and the primary analysis admits none of them. Importing `PMC12949993@v1.r1` creates 164 imported fact and raw-material rows (10 history, 125 series points, 26 single results, 3 raw material) plus the derived rows, the approved ledger rows, 4 media rows and 20 gap rows, with no leaks; a bundle with a wrong hash or an unsupported schema version is refused.
  - Depends on: P0.3, P0.5; Case Library LM0.

- **P0.7 Case Curator — moved to the Case Library.** Claude curates through the Supabase MCP under the `case-curate` skill (D-021).
- **P0.8 Review and freeze — moved to the Case Library** (Case Library SPEC §7).
- **P0.9 [human] Verify the pilot case — moved to the Case Library** (task L0.10). When the pilot bundle is exported (LM0), import it with P0.6: Milestone M0.
- **P0.10 Curate the starter set — moved to the Case Library** (tasks L1.1–L1.4, batch 1).

---

## Phase 1: prototype engine (text only)

- [x] **P1.1 LLM gateway**
  - Done 26 Sep 2026: `sambhasha.llm`, with the pieces below. 72 tests, none touching the network.
    - `configs/models.yaml`: providers (OpenRouter, Ollama) and a profile per role. The API keys are read from the environment only when an endpoint is needed. The model ids are placeholders until the pilot's models are chosen (P1.11); synthetic and evaluator are another family from the doctor seats (D-010), and a test checks it.
    - `backend.py`: the one `openai`-SDK client; OpenRouter's cost comes back per call, and Ollama costs nothing.
    - `gateway.py`: structured output as a JSON schema (or in the prompt, for providers without schema support). An invalid reply is retried up to twice, with the error. Every attempt is reported as an `LlmCallRecord`, which `call_event` turns into an `llm_call` event.
    - `cache.py`: record and replay in `data/llm-cache/`, keyed by the request's SHA-256; a replay costs nothing, and `replay_only` refuses any call.
    - `fake.py`: the scripted `FakeLLM`.
    - An invariant test keeps the `openai` import inside `llm/`. PyYAML added with Atul's approval.
  - Build: `sambhasha.llm` implements SPEC §11. One `openai`-SDK client with OpenRouter and Ollama profiles from `configs/models.yaml`. Structured output with validation and up to two retries. Record-and-replay cache in `data/llm-cache/`. An `llm_call` event per call with tokens and cost. A scripted `FakeLLM`.
  - Accept: unit tests cover schema retry, cache hits (a second identical request makes no network call) and cost logging. No test touches the network.
  - Depends on: P0.2.

- [x] **P1.2 Coding and synonyms**
  - Done 26 Sep 2026: `catalogue.py` reads all eight catalogue files. `gatekeeper/coding.py` codes text in three steps: an exact name or synonym, or the same words in any order; otherwise ranked candidates for the matcher model (P1.3); otherwise unmatched, which is logged as a missing request.
    - Normalisation is applied to requests and names alike: case, accents, punctuation, word order, plurals, British and American spelling, filler words, a leading article and "Pb"; "%" reads as "percent". A test checks it adds no ambiguity the catalogue lacks.
    - Results: "CBC", "hemogram" and "complete blood count" give `LAB.HAEM.CBC`; "blood lead", "lead level" and "Pb level" give `LAB.TOX.BLOOD_LEAD`. Over 99% of catalogue names code to their own item, and genuine catalogue overlaps ("PT", "FDP") go to the matcher.
    - Missing requests export as CSV in the Case Vault's `missing_request` columns. LOINC codes come with each item (empty in catalogue v2).
    - No local `synonyms.csv` (SPEC §17 layout): the catalogue stays the one vocabulary (D-022), and new synonyms reach it through the missing-request export.
  - Build: `gatekeeper/coding.py` maps request text to catalogue ids using the synonyms in the Case Library's catalogue export (D-022); LOINC codes come from the catalogue.
  - Accept: "CBC", "hemogram" and "complete blood count" resolve to one catalogue id; "blood lead", "lead level" and "Pb level" resolve to one catalogue id; unmatched text is logged for the Case Library's missing-request export.
  - Depends on: P0.2.

- [x] **P1.3 Gatekeeper**
  - Done 27 Sep 2026: `gatekeeper/resolver.py` (with `lookup.py`, `matcher.py`, `policy.py`, `configs/permissions.yaml`, `prompts/matcher.md` v1 and `prompts.py`).
    - Permissions: the action matrix in `configs/permissions.yaml`, plus each catalogue item's `specialty_scope` as the manoeuvre catalogue.
    - Refusals: a request for the diagnosis, the article or its source (a protocol violation), and vague requests.
    - Coding (P1.2): candidates are ranked by how much of a catalogue phrase the question covers, so whole-sentence history questions reach the matcher, which must pick one of them.
    - Release: stored text only, by day, with carry-forward marked. Release conditions are checked against the seat's own words or the order's indication. A held-back fact is never replaced by a ledger reply. A fact that reveals the diagnosis comes only with its own test (§7, rule 4).
    - Routing: report components of `service.*` tests go to that service as raw material (the article's, else the ledger's report text), and a test-level rule ("Not applicable") answers the whole test.
    - Pilot: H09 alone for a toxin question, H10 for a supplement question, blood lead 77.8 ug/dL (stored in ug), film to `service.pathology` with R01, a Consultant's order refused, diagnosis and source requests refused as violations, and every released line is stored text. A leak review found four gaps, not reachable with today's data; all fixed and tested.
  - Build: `configs/permissions.yaml` with the permission matrix and manoeuvre catalogue. The resolver implements SPEC §7: it returns stored text only, handles direct and interpretive routing, day semantics and `release_condition`, and refuses with a reason. The matcher model picks only from candidate catalogue ids (D-022).
  - Accept (pilot):
    - A generic toxin question returns H09 only; a supplement question returns H10.
    - Ordering a blood lead returns 77.8 µg/dL.
    - A film order sends R01 to `service.pathology` and nothing raw to the Chart.
    - A Consultant who orders a test is refused.
    - "What is the diagnosis?" is refused and logged.
    - Every released text equals stored text.
    - A result ordered on a day with no value returns the latest earlier value, marked with its day (changelog, 25 Sep 2026: carry-forward).
  - Depends on: P0.6, P1.1, P1.2.

- [x] **P1.4 Synthetic Findings Service (fallback)**
  - Done 27 Sep 2026: `synthetic/service.py`, `checks.py` and `route.py`, with `prompts/synthetic.md` v1.
    - Routing: `respond` sends a request to the service only when the Gatekeeper finds it outside the catalogue, and flags the run (`used_fallback`, D-023).
    - The model: the synthetic role (another family, D-010), given the ground truth, the patient's profile, the day, what is already released and any matched gap's guidance.
    - Checks: leaks (P0.5 scanner), any form of "not available", and numbers that contradict a stored value. A failed check is regenerated with the reasons, up to twice; otherwise nothing is stored.
    - Storage: rows go to `synthetic_ledger`, keyed by (bundle, normalised request, day for tests), pending review; migration `20260927090000` adds the request, kind, gap and result columns.
    - Gaps marked `auto_generate: false` are held for the Case Reviewer (G14 matched by "hair mercury and arsenic").
    - The missing-request export lists each distinct request once.
  - Build: the generator (prompt `prompts/synthetic.md`) for requests outside the catalogue only (D-023), conditioned on the ground truth, the patient's state and the gap guidance. It has consistency and leak checks and a cache keyed by (case, code, day bucket), respects `auto_generate: false`, and writes every request it answers to a missing-request export (CSV) for the Case Library.
  - Accept: a request for a catalogue item is answered from the bundle and never reaches the service; a repeated out-of-catalogue request returns the same ledger row; a result contradicting a stored fact is rejected and regenerated; G14 is never auto-generated; no output contains "not available"; the export lists every generated request.
  - Depends on: P1.1, P1.3.

- [ ] **P1.5 Clock, costs and Chart**
  - Build: `configs/turnaround.yaml` and `configs/prices_inr.yaml`, generated from the Case Library's catalogue export (D-022; closes the Sambhasha item of the catalogue v1 entry in `../docs/CHANGELOG.md`, using the catalogue version pinned in `CLAUDE.md` at the time, now v2 exists); a simulated clock in minutes; the Chart projection; the `SeatView` builder.
  - Accept: a result becomes visible only after its turnaround; costs add up per order; a Consultant sees the Chart only after referral; a service view holds only its order and raw material.
  - Depends on: P0.3.

- [ ] **P1.6 Seats and role cards**
  - Build: the `Seat` protocol; `LLMSeat` and a CLI `HumanSeat`. Role cards in `prompts/` for the Attending Physician, the Challenger, Consultants (one template with specialty variables) and the Pathology and Radiology Services. Each card states the seat's scope and allowed actions.
  - Accept: each seat produces a valid action from a fixture view with `FakeLLM`; a `HumanSeat` receives a view identical to an `LLMSeat`'s.
  - Depends on: P1.1, P1.5.

- [ ] **P1.7 Scheduler**
  - Build: the SPEC §10.2 state machine; consultant sessions of up to K actions ending in a ConsultNote; the Challenger before commit (and every N turns if configured); turn, referral and budget limits with a forced commit; `configs/pilot.yaml`.
  - Accept: a scripted `FakeLLM` run of the pilot's efficient path produces the expected sequence of event types; the limits force a commit; the same config gives an identical event hash on rerun.
  - Depends on: P1.3, P1.4, P1.5, P1.6.

- [ ] **P1.8 Evaluator**
  - Build: the matcher's mapping of the Commit and of each service report to catalogue ids (D-022); the diagnosis rubric using the case's anchors and their conditions (Case Library SPEC §10.4); plan scoring from must-do and must-not-do; process metrics; synthetic dependence; the fallback flag (D-023); `sambhasha evaluate`.
  - Accept (pilot fixtures):
    - A commit naming lead poisoning and the supplement scores 5.
    - "Warm AIHA" scores 2.
    - A plan with steroid escalation registers a must-not-do violation.
    - Synthetic dependence is computed from `Commit.evidence`.
    - The film-review must-do is met when the Pathology Service's film report mentions coarse stippling (mapped to `FND.COARSE_BASOPHILIC_STIPPLING`).
  - Depends on: P1.7.

- [ ] **P1.9 CLI and transcript viewer**
  - Build: `sambhasha run --config configs/pilot.yaml [--fake]`; `sambhasha transcript <run_id>` in the terminal with an `--html` export; a budget cap for live runs set in the config.
  - Accept: a fake run and its transcript work offline; a live run refuses to start without a budget cap.
  - Depends on: P1.7, P1.8.

- [ ] **P1.10 Invariant test suite**
  - Build: `tests/invariants/` covering SPEC §2, including a property-based test (hypothesis) of random action sequences on the pilot.
  - Accept: tests exist and pass for I1–I8. Examples: no view contains an unreleased fact id; no view contains ground-truth text; reruns are identical; released text is always stored text; frozen cases and events are immutable.
  - Depends on: P1.7.

- [ ] **P1.11 [human] Live pilot runs**
  - Build: run the pilot with two model profiles (for example two different families for the doctor seats), three repeats each. Prepare transcripts, scores and a short findings note for Atul.
  - Accept: six completed runs; Atul has read at least two transcripts; any leaks or rule breaks found are fixed and re-tested. Milestone M1.
  - Depends on: M0, P1.9, P1.10.

---

## Phase 2: study (outline, detail later)

- Inspect AI task wrapping the engine: cases as the dataset, seats as model roles, cost limits, epochs, caching, publishable logs.
- Grow to 50–100 cases from the Case Library, published after the models' cutoffs, with `public_release_ok` for the study set (D-025) and a held-out set kept private (S-005); memorisation probe; perturbation of non-essential details.
- Human raters and agreement statistics; arms A–E (SPEC §15); pre-registration; TRIPOD-LLM reporting.
- Image mode for the Diagnostic Services; tracing with Arize Phoenix or Langfuse.

## Phase 3: extras (outline)

- The teaching game is Nidana (D-027); Sambhasha's matcher and Evaluator calibration protocol may be reused by Nidana's voice mode.
- Theatre mode through Discord webhooks; later, an optional MCP server for outside agents (a Hermes agent may play as a contestant).
- The research release: umbrella task U1.1 exports the public repository at submission (`../../docs/REPOSITORY.md`).
