# CLAUDE.md: Sambhasha

Sambhasha (formerly the Virtual Diagnostic Team, VDT) is a research simulator. AI or human doctor "seats" work up real, open-access published case reports one question at a time, while a Gatekeeper holds the hidden case. It becomes a benchmark first, then a paper. The teaching game is Nidana, a separate part that uses the same cases (D-027).

The name comes from *sambhāṣā*, the Charaka Saṃhitā's term (Vimāna Sthāna 8) for structured discussion among physicians: friendly consultation (*sandhāya*) and challenging debate (*vigṛhya*), like Sambhasha's Consultants and its Challenger.

Sambhasha is one part of Clinical-Case-Sim. Its cases come from the shared Case Library (`../case-library/`) as frozen bundles; it never curates cases itself (D-021). Claude Code also loads the umbrella rules in `../CLAUDE.md`. Follow both.

Owner: Dr Atul Tiwari, a pathologist who builds by directing Claude Code. Explain choices in plain language and keep him in the loop on anything clinical.

This is an educational research tool. Nothing it produces is clinical advice.

## Pinned shared-contract versions

- Case bundle schema: **0.3** (P0.2 models, P0.6 importer). Bundles of any other version are refused.
- Catalogue: **v2** (the published bundles' catalogue; the leak scanner reads `../case-library/catalogue/`).

## Read before any work

1. `../docs/CHANGELOG.md`: deal with any open item for Sambhasha first.
2. `docs/DECISIONS.md`: the decisions. Do not change them without asking Atul. Shared decisions are in `../docs/DECISIONS.md`.
3. `docs/SPEC.md`: the design source of truth. Names are in §1 and invariants in §2.
4. `docs/PLAN.md`: tasks with acceptance criteria. Work in order.
5. `../case-library/cases/PMC12949993/`: the pilot case `PMC12949993`, its dossier, draft case file and analysis. It contains spoilers, so never place its contents in a seat's prompt.

## Invariants (never violate; tests in `tests/invariants/` enforce them)

1. The information barrier lives in data and code. No seat gets file, database, web or code-execution tools.
2. The Scheduler decides who acts next. A model never does.
3. Every seat implements `act(view) -> Action`. LLM and human seats get identical views.
4. The Gatekeeper releases stored text only. Its matcher model returns candidate catalogue ids, never prose (D-022).
5. One missing-fact rule: the likeliest result given the true diagnosis and the day. Results come from the case bundle, where they are pre-generated and reviewed (D-023). Only requests outside the catalogue reach the runtime Synthetic Findings Service, which caches and ledgers them and reports them to the Case Library; runs that used it are flagged and kept out of primary results. Never "not available", and never flagged as synthetic during play.
6. The Event Log is append-only, and every run starts clean.
7. Frozen case files are immutable. A change means a new version; every run records the bundle revision it used.
8. The ground truth never enters any seat's view.

## Names (exactly these, everywhere)

| Name | Code id |
| --- | --- |
| Attending Physician | `attending` |
| Challenger | `challenger` |
| Consultant | `consultant.<specialty>`, e.g. `consultant.haematology` |
| Diagnostic Service | `service.pathology`, `service.radiology`, `service.microbiology` |
| Gatekeeper | `gatekeeper` |
| Synthetic Findings Service | `synthetic` |
| Case Curator, Case Reviewer (both in the Case Library) | `curator`, `reviewer` |
| Evaluator | `evaluator` |
| Scheduler, Chart, Event Log, Case Vault | `scheduler`, `chart`, `event_log`, Case Vault |

Use British spelling in user-facing text ("haematology", "anaemia").

## Stack

- Python 3.12 with uv, Pydantic v2 and a Typer CLI (`sambhasha`).
- Postgres through Supabase for runs: `supabase start` locally, self-hosted on Coolify later. psycopg 3. Case data arrives as bundle files from `../case-library/exports/`; Sambhasha never writes to the Case Vault, and `.claude/settings.json` denies the account-level Supabase connector (set up in Case Library task L0.2).
- Models through one OpenAI-compatible client in `src/sambhasha/llm/`: OpenRouter for cloud, Ollama for local. Model ids live only in `configs/models.yaml`.
- Quality tools: ruff, mypy, pytest (with hypothesis), pre-commit.
- Later phases: Inspect AI (Phase 2).

## Commands (created in P0.1; until then they don't exist)

```bash
uv sync                       # install
uv run pytest                 # unit + invariant tests (offline)
uv run pytest -m integration  # needs `supabase start`
uv run ruff check . && uv run mypy src
supabase start && supabase db reset
uv run sambhasha case import ../case-library/exports/PMC12949993@v1.r1.json
uv run sambhasha run --config configs/pilot.yaml --fake
```

## Conventions

- Type everything. Domain objects are Pydantic models in `src/sambhasha/domain/`; no untyped dicts cross module boundaries.
- Only `src/sambhasha/llm/` imports the `openai` SDK. Every model call logs an `llm_call` event.
- Prefer configuration to code: permissions and model profiles live in `configs/*.yaml`. Prices (INR) and turnaround times are generated from the Case Library's catalogue export; never edit them by hand.
- Prompts live in `prompts/*.md` with a `version` in front matter. Editing a prompt bumps its version.
- SQL lives only in `src/sambhasha/storage/postgres.py` and `supabase/migrations/`. Never edit an applied migration; add a new one.
- Keep commits small, in conventional-commit style, one PLAN task per branch.

## Testing

- Write each task's acceptance tests first.
- Unit tests use the in-memory repositories and `FakeLLM`. There is no network access and no paid API call in any test or in CI.
- Integration tests are marked `@pytest.mark.integration` and need local Supabase.
- Never skip, weaken or delete an invariant test to make a change pass. Ask Atul instead.

## Working agreement

- **Start of a session:** check `../docs/CHANGELOG.md`; then open `docs/PLAN.md`, pick the first unchecked task whose dependencies are done, and state it with its acceptance criteria.
- **End of a task:** run lint, type-check and tests, tick the box in `PLAN.md` with a one-line note, and summarise for Atul in plain words.
- **Ask Atul before:**
  - changing a decision or invariant;
  - anything that needs a shared-contract change, such as the bundle `schema_version` (it happens in a Case Library session);
  - adding a dependency not listed in `docs/SPEC.md` §17;
  - any live model run or batch likely to cost more than US$5;
  - anything touching licences.
- **[human] tasks:** prepare the materials (transcripts, rating sheets), tell Atul exactly what to check, and continue with other tasks.
- **Secrets:** never commit them. `.env` is git-ignored; `.env.example` lists the keys.
- **Fixtures:** seat-facing fixtures come from released events only. Ground truth stays in Evaluator fixtures.

## Out of scope for now

- Hermes Agent, A2A and the MCP server. Hermes may later appear only as an ops helper, a Discord theatre display or a contestant (D-002).
- Curating cases (the Case Library does it, D-021).
- The teaching game (that is Nidana, D-027).
- Inspect AI, image mode and tracing (Phase 2).
- Voice, and simulated outcomes of alternative treatments.
