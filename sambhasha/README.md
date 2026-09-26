# Sambhasha

Sambhasha is a research simulator. AI or human doctor seats (an Attending Physician, a Challenger, Consultants and Diagnostic Services) work up real, open-access published case reports one question at a time, while a Gatekeeper holds the hidden case. It is built to become a benchmark and then a paper.

It is one part of Clinical-Case-Sim. Its cases come as frozen bundles from the shared Case Library (`../case-library/`); the teaching game that uses the same cases is Nidana (`../nidana/`).

This is an educational research tool. Nothing it produces is clinical advice.

## Set up

Needs [uv](https://docs.astral.sh/uv/) (it fetches Python 3.12 itself).

```bash
uv sync
cp .env.example .env   # then fill in the keys; .env is never committed
```

## Check

```bash
uv run pytest                                 # unit and invariant tests, offline
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run sambhasha --help
```

Tests marked `integration` need Sambhasha's own local database (ports 563xx, so it runs beside the Case Vault's 553xx):

```bash
supabase db start                                   # Postgres only, with every migration
uv run pytest -m "integration or not integration"  # every test, the database ones included
supabase db reset                                   # start again from the migrations
```

## Documents

- [docs/SPEC.md](docs/SPEC.md): the design
- [docs/PLAN.md](docs/PLAN.md): tasks and acceptance criteria
- [docs/DECISIONS.md](docs/DECISIONS.md): decisions
- [CLAUDE.md](CLAUDE.md): working rules for Claude Code sessions
