# Path analysis: <PMCID>

Written before anything is generated (SPEC §6.3). Every catalogue item on any path is resolved as `affected` or checked explicitly; the rest goes to the normal generator. Stored with `sql/07_path_analysis.sql` as JSON: `[{"path_id", "kind", "name", "rationale", "items"}]`.

| Path | Kind | Why a player goes there | What the case must show | Items |
| --- | --- | --- | --- | --- |
| P1 <name> | efficient | <what a strong clinician would do> | <the findings that confirm it> | `HX...`, `LAB...` |
| P2 <name> | trap | <what the case invites> | <what argues against it> | |
| P3 <name> | alternative | <a reasonable line of enquiry> | <how it resolves> | |

Checklist:

- [ ] Every comorbidity and medicine has a path or a note on why it needs none.
- [ ] Every must-do and must-not-do condition names only items that exist in the catalogue.
- [ ] Items whose normal depends on the case (sex, vital signs, blood group) are on a path or resolved by hand.
