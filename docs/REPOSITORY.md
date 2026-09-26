# Repository strategy

Decision (S-010, agreed 26 Sep 2026, superseding S-005): **one public monorepo holding development-only cases, and a separate public research repository generated from it when Sambhasha is submitted for publication.** Production and study cases are a new set, kept outside this repository. Day-to-day Git work (branches, commits, pushes and merges) follows the Git and GitHub section of [`../CLAUDE.md`](../CLAUDE.md).

## Why one monorepo

- **Shared-contract changes stay atomic.** A change to the bundle schema or the catalogue lands in one branch, and CI runs both projects' contract tests against it. With separate repositories the same change needs coordinated pull requests in three places.
- **Less machinery for one builder.** Two repositories need a third for what they share (the bundle schema, catalogues, the curation skill and the exported bundles), published as versioned releases that each project pins. That suits teams; for one person building through Claude Code it is mostly bookkeeping.
- **The protection you asked for still holds.** Separate folders, the umbrella rules in `CLAUDE.md`, the changelog with acknowledgements, and a CI guard give the "no change without acknowledgement" guarantee inside one repository.

## Why the monorepo is public, and what that means for cases

S-005 kept the monorepo private, because public case bundles and answers can be scraped into future models' training data, which would contaminate a benchmark that depends on models not having seen the cases. On 26 Sep 2026 GitHub Actions stopped running on the private repository (billing), and Atul made it public (S-010), accepting that trade-off for the cases already committed.

So:

- The committed cases (the pilot and batch 1) are **development-only**: they exist to build and test the apps. They never go into Nidana's store release, and they never count as held-out or primary-result cases in a Sambhasha study.
- **Production and study cases are a new set**, curated once the apps work. Before curating any, choose where they live (a separate private repository, or private storage read by the Case Vault) and record it here. They are never committed to this repository.
- A Sambhasha held-out set stays private even after publication.
- Every commit is public: secrets, `.env` files, player or tester data and review packs stay out of Git (`CLAUDE.md`), and the secret scanner runs in pre-commit and CI.

## Layout

```text
Clinical-Case-Sim/            one public Git repository (GitHub: clinical-case-sim)
├── CLAUDE.md  README.md  docs/
├── case-library/            Case Vault schema, catalogues, curation skill, Case Studio, exports
├── nidana/                  Expo player app, game server, engine
└── sambhasha/               research engine, configs, prompts, study scripts
```

- pnpm workspaces for the TypeScript parts (Nidana and the Case Studio); uv for the Python parts (Case Library scripts and Sambhasha).
- GitHub Actions: a contract workflow (umbrella task U0.1), plus one workflow per part, limited to that part's folder and added by its first build task.
- CI guards:
  - a change under `case-library/schemas/` or `case-library/catalogue/` fails unless `docs/CHANGELOG.md` changes too: in the same commit for the pre-commit hook, and in the same pull request for CI;
  - the contract workflow validates the current exports against the bundle schema and runs both engines' conformance playthroughs.
- The changelog guard also runs as a pre-commit hook, which blocks the commit on your machine. CI is the second signal. Now that the repository is public, GitHub Free can make checks required through branch protection; turning that on is a repository-settings change for Atul.

## The research release, at submission

`scripts/export_research_release.py` builds the public repository from an allow-list.

| Included | Excluded |
| --- | --- |
| Sambhasha's source, configs, prompts, tests and study scripts | Nidana, the game |
| The bundle schema and the slice of the catalogue that the study cases use | The Case Studio, review packs and internal notes |
| Frozen bundles of study cases whose licence allows public release (CC0, CC BY, CC BY-SA, CC BY-NC, CC BY-NC-SA), with only the figures whose own flags allow it | ND cases, held-out cases, and figures without `public_release_ok` |
| Synthetic ledgers, run logs, scores and anonymised rater data | Secrets and player data |
| README with reproduction steps, `CITATION.cff`, licences (code MIT or Apache-2.0; your annotations CC BY 4.0; each case keeps its article's licence) | |

Steps:

1. Before submission, run the export into a fresh folder.
2. Scan it for secrets, player data, licence flags (each case and each figure) and any path not on the allow-list.
3. Push it to a new public repository, `sambhasha`, and create a GitHub release with the paper version (Zenodo archives releases, not bare tags).
4. Let Zenodo archive the release and mint a DOI, and cite that DOI in the paper. If the repository must stay private until acceptance, reserve a DOI with a manual Zenodo upload instead and publish it on acceptance.

Updates flow one way, from the monorepo to the public repository, by re-running the export. The monorepo's development history is public (S-010); it holds only development-only cases, never held-out or study cases.

## If collaborators join

If someone should see Sambhasha but not the game, the same export can produce a private collaborator repository, or the monorepo can be split then: at that point the version pins and the changelog already describe the interfaces a split would need.
