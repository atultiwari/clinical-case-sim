# What Claude did on Atul's behalf, 25 Sep 2026

Case Library · a record of the decisions and actions Atul delegated ("take decisions & actions on my behalf and document", 25 Sep 2026), and of what is still his. No diagnoses appear in this file.

## Where things live now

- **One folder:** `~/Projects/research/Clinical-Case-Sim`. The four extra worktree folders (`-L0.7`, `-L1.1`, `-L1.3`, `-L1.5`) were removed after checking they were clean and pushed; their cached articles were moved into `case-library/data/articles/`.
- **On `main`:** L0.1–L0.7, L1.1, L1.2, L1.5 and catalogue v1, merged through pull requests #7–#11.
- **Open branches:** `case-library/L0.8-pilot-import` → `L0.9-pilot-resolution` → `L1.3-batch1`, stacked, each up to date with `main`. They merge once the pilot is finished in the Case Vault and reviewed.

## Decisions taken for Atul

| Decision | What was chosen | Where recorded |
| --- | --- | --- |
| Catalogue review (L0.5) | Atul approved it himself ("I approve it for now"). Claude filled the pack from that: all rows approved, the 54 suggested normal texts taken, and the nine questions answered with Claude's recommendations (Q1: neutral texts for v1). Four suggestions carried authoring notes in player-visible text; they were removed the same day and a test now forbids them | `docs/CHANGELOG.md` (catalogue v1), PLAN L0.5 |
| Recheck the catalogue | A reminder is saved for when Nidana goes to production | Claude's project memory |
| v0 load | Skipped at Atul's word; v1 loaded instead | PLAN L0.4 |
| Pilot redaction | Neutral title "Three weeks of abdominal pain and growing tiredness", tags anaemia, abdominal pain, myositis; slug `c-6gizm`; the patient's opening words | the pilot's gold file |
| Batch 1 (L1.2) | The four starter cases plus shortlist #1–#5, all CC BY 4.0; no NC-ND or de novo cases | `cases/BATCH1.md` |
| Starter-case questions (L1.3) | Units are converted to SI at extraction, with the printed value in a note. Other method questions decided; value questions only *proposed*, for Atul's review | `cases/BATCH1-CURATOR-ANSWERS.md` (branch `L1.3-batch1`) |
| Curation rule | Patient-dependent normals (pulse, ECG rate, menses and others) are written per case where the neutral text would be wrong; every case records its blood group | the skill's `SKILL.md`, rule 9 |

## What was written to the Case Vault

| What | How | Checked |
| --- | --- | --- |
| Migration `casevault_studio_writer` | MCP `apply_migration` | 12 policies; security advisors clean |
| Catalogue v1, in full | Four pastes into the dashboard SQL editor in Atul's Chrome (too large for the connector). Five rows with ° or α were mangled by the clipboard and were reloaded through the MCP; four rows with authoring notes were corrected through the MCP | All seven catalogue tables match the local build's fingerprints |
| The pilot, steps 4–8 | Two dashboard pastes, each one transaction | 191 facts, 3 raw material, 4 media, 20 gaps, 12 paths; ledger 109 affected, 993 normal, 6 reviewer, 1 rule; the JATS snapshot's SHA-256 matches |

**Not done: a refusal.** The permission system refused the third dashboard paste, the pilot's reports, consult notes, the patient's words, test utility and ground truth, as a security-weakening action (writes outside the MCP's guard). Claude stopped all further writes through the dashboard, including the figure upload. The pilot is in `draft`, so no player can see it.

**Deviation from the rules.** CLAUDE.md says Claude writes to the Case Vault only through the MCP. The dashboard pastes were Atul's explicit instruction (Chrome allowed) for loads too large for the connector. Future bulk loads need either Atul running the file himself or a decision on a supported path.

## What still needs Atul, step by step

### 1. Finish the pilot in the Case Vault (about 5 minutes)

1. Supabase → project **case-vault** → **SQL Editor** → **New query**.
2. Open `case-library/build/pilot/C_author.sql` (on this Mac; git-ignored) in a text editor, copy all of it and paste it into the editor. Run it. If the dashboard warns about Row Level Security, choose **Run without RLS**: the warning misreads the words "into atomic" inside a quoted licence note, and nothing creates a table.
3. Tell Claude. Claude then runs the checks (step 10) and the hand-over to `in_review` (step 11) through the MCP, which are small.

### 2. Upload the pilot's three figures

1. Supabase → case-vault → **Storage** → bucket **case-media**.
2. Create a folder `PMC12949993` and upload `F1.jpg`, `F2.jpg` and `F3.jpg` from `case-library/data/figures/PMC12949993/`, keeping the names exactly.

### 3. Create the Studio's database logins (to see the cases in the Case Studio)

1. Supabase → case-vault → SQL Editor. Run this with two new passwords of your own (never paste them to Claude):
   ```sql
   create role studio_reader login password '<password 1>' in role casevault_reader;
   create role studio_writer login password '<password 2>' in role casevault_studio_writer;
   ```
2. Click **Connect** (top of the dashboard) and copy the **Session pooler** connection string's host.
3. Create `case-library/studio/.env.local` with:
   ```
   CASE_VAULT_DB_URL_READONLY=postgresql://studio_reader.vxiymbaxsiavxuyxzhnt:<password 1>@<pooler host>:5432/postgres
   CASE_VAULT_DB_URL_STUDIO_WRITER=postgresql://studio_writer.vxiymbaxsiavxuyxzhnt:<password 2>@<pooler host>:5432/postgres
   ```
4. From `case-library/`, run `pnpm --filter @case-library/studio dev` and open http://localhost:3000. With `STUDIO_USERS` unset there is no login page, and it only listens on this Mac.

### 4. Review the pilot (L0.10) in the Studio

Once steps 1–3 are done, the pilot shows in the Studio. Review it there (or ask Claude for the Excel pack): the 21 judgement calls, the reviewer-set values (G14, G15), and reject the `CMP.US_PELVIS_REPORT` normal row, which carries an authoring note. Then say "freeze" when you are satisfied (L0.11).

### 5. Later

- The starter cases' proposed answers (`cases/BATCH1-CURATOR-ANSWERS.md`) at the batch 1 review (L1.4).
- The catalogue recheck before Nidana's production release.
- For the VPS deployment of the Studio: `STUDIO_USERS` and `STUDIO_SESSION_SECRET` (see `studio/README.md`).
