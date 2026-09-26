# Clinical-Case-Sim

Diagnostic simulation built from real, open-access case reports. Dr Atul Tiwari, Vedant Research Labs.

- **Case Library** (`case-library/`): one shared library of cases. Claude curates each case from an open-access report into the Case Vault (Supabase); Atul reviews it; it is frozen and exported as a case bundle.
- **Nidana** (`nidana/`): the teaching game. Students take the history, examine, order tests and commit to a diagnosis; Nidana scores and debriefs them. Planned for the App Store and Play Store.
- **Sambhasha** (`sambhasha/`): the research simulator. A team of AI doctor seats works up the same hidden cases; the results become a benchmark and a paper. Named after *sambhāṣā*, the structured discussion among physicians described in the Charaka Saṃhitā (Vimāna Sthāna 8).

```mermaid
flowchart LR
  A["Open-access case report"] --> L["Case Library<br/>curate, review, freeze"]
  L -->|"case bundles"| N["Nidana<br/>students play"]
  L -->|"case bundles"| S["Sambhasha<br/>AI doctors play"]
  N -.->|"missing requests"| L
  S -.->|"out-of-catalogue requests"| L
```

## Status (26 Sep 2026)

The GitHub repository is public (S-010), and the cases in it are for development only. Production and study cases will be a new set, kept outside this repository.

## Setting up a clone

You need Node 22 or later with pnpm, [pre-commit](https://pre-commit.com) and [gitleaks](https://github.com/gitleaks/gitleaks). On a Mac: `uv tool install pre-commit` and `brew install gitleaks`. Then, in the clone:

```bash
pnpm install
pre-commit install
```

The hooks block a change to `case-library/schemas/` or `case-library/catalogue/` without a `docs/CHANGELOG.md` entry, as well as secrets, files over 20 MB and merge-conflict markers. The `contract` workflow repeats these checks on every pull request.

## Documents

| Where | What |
| --- | --- |
| `CLAUDE.md` | Rules for Claude in every part |
| `docs/DECISIONS.md` | Shared decisions |
| `docs/REPOSITORY.md` | Repository strategy and the research release |
| `docs/CHANGELOG.md` | Shared-contract changes and acknowledgements |
| `docs/PLAN.md` | Umbrella tasks and the order of milestones |
| `docs/SESSION_PROMPTS.md` | Prompts for starting Claude Code sessions |
| `case-library/docs/` | Case Library SPEC and PLAN |
| `case-library/cases/PMC12949993/` | The pilot case: dossier, draft case file, analysis (spoilers) |
| `nidana/docs/` | Nidana DECISIONS, SPEC and PLAN |
| `sambhasha/docs/` | Sambhasha DECISIONS, SPEC and PLAN |
