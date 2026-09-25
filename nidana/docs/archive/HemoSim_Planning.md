# HemoSim — Virtual Patient Simulation Platform
### Full Planning & Architecture Document

> **Project owner:** Practicing MD (Pathology) — serves as clinician-reviewer for all medical content
> **Starting specialty:** Hematology
> **Model reference:** InSimu Pro (algorithmic virtual patients) + Full Code (curated cases + Patient AI)
> **Core non-negotiable:** Medical accuracy. Every case clinician-validated before going live.
> **Status:** Planning / pre-build

---

## 1. Vision & Guiding Principles

Build a virtual patient simulator for medical students and professionals, starting with Hematology, where users take a history, order investigations, and reach a diagnosis — scored on accuracy, efficiency, and avoidance of patient harm.

**Principles:**

1. **Medicine is the moat, code is the easy part.** The technical build is fast; clinical accuracy is what makes it valuable and safe.
2. **Nothing reaches a student unreviewed.** A human clinician (you) signs off on every case and every AI-generated (synthetic) field.
3. **Ground truth first.** Cases are anchored to peer-reviewed, open-access case reports. Synthetic data only fills gaps, always flagged, always reviewed.
4. **Start small, validate the schema, then scale.** 10–20 excellent hematology cases beat 200 shaky ones.
5. **Separate content from consumption.** A dedicated authoring system (CMS) is decoupled from the student-facing simulator, sharing one backend.

---

## 2. Two-App Architecture

The platform is split into two applications over one shared backend. This is how production edtech is built and keeps the medical-quality gate (the CMS) cleanly separated from the student experience (the Simulator).

```
┌─────────────────────────────────────────────────────────┐
│                    SHARED BACKEND                        │
│         Supabase (PostgreSQL) + API + AI Layer           │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
    ┌──────────▼──────────┐    ┌──────────▼──────────┐
    │   App 1: CMS        │    │   App 2: Simulator   │
    │  Case authoring +   │    │  Student-facing play │
    │  review (internal)  │    │  webapp → mobile     │
    └─────────────────────┘    └─────────────────────┘
```

### App 1 — Case Authoring CMS (internal)

A structured case-report processor with an editorial workflow. Only you (and later, trusted clinician contributors) use it.

- **Input methods:** DOI/URL import → AI extraction; manual de novo entry; PDF upload → AI parse.
- **Per-case workflow:** Import/Create → AI synthetic fill → clinician review queue → approve → publish → (retire/archive).
- **Views:** case library (filter by status/specialty/difficulty); case editor (full schema); synthetic-data review queue; investigation builder; diagnostic-path & scoring editor.

### App 2 — Simulator (student-facing)

Reads from the same DB the CMS writes to. Starts as a webapp; later React Native mobile.

- **Views:** dashboard (cases, progress, XP); case player (presentation → history → investigations → diagnosis → feedback); performance analytics; auth/subscription (later).

---

## 3. Tech Stack

```
Shared Backend
├── Database: Supabase (PostgreSQL)
├── AI Layer: Claude API (R&D + extraction) → MedGemma (production/local)
├── File Storage: Supabase Storage (imaging results, source PDFs)
└── API: Supabase auto-REST + Edge Functions for AI calls

App 1 — CMS
├── Next.js (React), webapp only
├── DOI resolver: CrossRef API (free, no key)
├── PDF parsing: Claude API (document input)
└── Hosting: Vercel

App 2 — Simulator
├── Next.js (React), webapp first
├── Later: React Native (shares component/logic layer)
└── Hosting: Vercel

Shared
├── Auth: Supabase Auth (roles: admin/clinician vs student)
├── Language: TypeScript throughout
└── Styling: Tailwind CSS
```

**Why Supabase over JSON files from day one:** clean schema migrations, natural AI-layer integration, SQL joins across cases, tidy synthetic-data flag columns, zero refactor when the mobile app arrives, and a visual table editor that doubles as a lightweight CMS in the earliest days.

---

## 4. Data Schema

Seven entities serving three masters simultaneously: case content, the simulation engine, and the scoring system.

```
Disease (1) ──────────── (many) Case
Case (1) ──────────────── (1) Patient
Case (1) ──────────────── (many) Investigation
Case (1) ──────────────── (1) DiagnosticPath
Case (1) ──────────────── (1) ScoringRubric
Investigation (many) ──── (many) SyntheticDataLog
```

### 4.1 `Disease` — master reference per condition

```json
{
  "disease_id": "uuid",
  "name": "Acute Promyelocytic Leukemia",
  "icd_10_code": "C92.4",
  "icd_11_code": "2A60.0Z",
  "category": "Leukemia",
  "sub_category": "Acute Myeloid Leukemia",
  "specialty": "Hematology",
  "difficulty_level": "hard",
  "prevalence_tag": "rare",
  "key_differentials": ["disease_id_AML_NOS", "disease_id_DIC", "disease_id_ITP"],
  "must_not_miss": true,
  "teaching_points": [
    "Always suspect APL in bleeding patient with high WBC",
    "Do NOT delay ATRA pending cytogenetics"
  ]
}
```

### 4.2 `Case` — individual patient case

```json
{
  "case_id": "uuid",
  "disease_id": "uuid (FK → Disease)",
  "title": "A 34-year-old male with spontaneous gingival bleeding",
  "source": {
    "type": "case_report",
    "journal": "BMC Hematology",
    "doi": "10.1186/s12878-021-00234-x",
    "year": 2021,
    "license": "CC BY 4.0"
  },
  "difficulty_level": "hard",
  "estimated_solve_time_minutes": 12,
  "specialty": "Hematology",
  "tags": ["APL", "coagulopathy", "emergency", "ATRA"],
  "status": "approved",
  "created_at": "timestamp",
  "reviewed_by": "doctor_id",
  "reviewed_at": "timestamp"
}
```

### 4.3 `Patient` — the simulated patient the user sees

```json
{
  "patient_id": "uuid",
  "case_id": "uuid (FK → Case)",
  "demographics": {
    "age": 34, "sex": "Male", "ethnicity": "South Asian",
    "occupation": "Teacher", "residence": "Urban"
  },
  "chief_complaint": "Bleeding from gums for 3 days, increasing fatigue",
  "presenting_symptoms": [
    { "symptom": "Gingival bleeding", "duration": "3 days", "severity": "moderate", "is_volunteered": true },
    { "symptom": "Fatigue", "duration": "2 weeks", "severity": "moderate", "is_volunteered": true },
    { "symptom": "Petechiae on legs", "duration": "1 week", "severity": "mild", "is_volunteered": false }
  ],
  "vitals": {
    "bp_systolic": 100, "bp_diastolic": 68, "pulse": 102, "rr": 18,
    "temperature_celsius": 38.1, "spo2_percent": 97, "weight_kg": 68, "height_cm": 172
  },
  "past_medical_history": "None significant",
  "family_history": "No known hematological disorders",
  "drug_history": "No regular medications",
  "social_history": "Non-smoker, occasional alcohol",
  "review_of_systems": {
    "constitutional": "Weight loss of 3kg over 1 month",
    "ENT": "No epistaxis", "GI": "No hematemesis or melena", "GU": "No hematuria"
  }
}
```

> **`is_volunteered`** drives the history-taking mechanic: `true` symptoms are offered freely; `false` symptoms are revealed only if the user asks — making it feel like a real patient encounter.

### 4.4 `Investigation` — every orderable test + result for this case

```json
{
  "investigation_id": "uuid",
  "case_id": "uuid (FK → Case)",
  "category": "Laboratory",
  "sub_category": "Hematology",
  "name": "Complete Blood Count",
  "short_name": "CBC",
  "result": {
    "display_type": "table",
    "values": [
      { "parameter": "Haemoglobin", "value": 7.2, "unit": "g/dL", "reference_range": "13.5–17.5", "flag": "LOW", "is_synthetic": false },
      { "parameter": "WBC", "value": 38.4, "unit": "× 10³/µL", "reference_range": "4.5–11.0", "flag": "HIGH", "is_synthetic": false },
      { "parameter": "Platelets", "value": 18, "unit": "× 10³/µL", "reference_range": "150–400", "flag": "CRITICALLY LOW", "is_synthetic": false },
      { "parameter": "Neutrophils", "value": 0.8, "unit": "× 10³/µL", "reference_range": "1.8–7.7", "flag": "LOW", "is_synthetic": false }
    ]
  },
  "cost_points": 2,
  "time_minutes": 2,
  "is_essential": true,
  "is_harmful": false,
  "reveals_diagnosis": false,
  "diagnostic_weight": "high",
  "is_synthetic": false,
  "synthetic_generation_prompt": null
}
```

**Categories:** History, Physical_Exam, Laboratory, Imaging, Histopathology, Microbiology, Procedure.
**`diagnostic_weight`:** low | medium | high | definitive.

### 4.5 `DiagnosticPath` — gold-standard pathway (scoring + feedback)

```json
{
  "path_id": "uuid",
  "case_id": "uuid (FK → Case)",
  "optimal_sequence": [
    { "step": 1, "investigation_id": "CBC_id", "rationale": "First-line in any cytopenias or bleeding workup" },
    { "step": 2, "investigation_id": "peripheral_smear_id", "rationale": "Look for blast morphology, Auer rods" },
    { "step": 3, "investigation_id": "coagulation_profile_id", "rationale": "DIC screen — critical in APL" },
    { "step": 4, "investigation_id": "bone_marrow_biopsy_id", "rationale": "Definitive — hypergranular promyelocytes, Faggot cells" },
    { "step": 5, "investigation_id": "FISH_PML_RARA_id", "rationale": "Confirms t(15;17) — essential before ATRA" }
  ],
  "minimum_required_investigations": ["CBC_id", "peripheral_smear_id", "FISH_PML_RARA_id"],
  "correct_diagnosis_id": "disease_id_APL",
  "acceptable_diagnoses": ["disease_id_APL", "disease_id_AML_NOS"],
  "critical_actions": [
    { "action": "Order coagulation profile", "timing": "Within first 3 investigations", "penalty_if_missed": "high" },
    { "action": "Do NOT order platelet transfusion without checking coags", "timing": "Before any transfusion order", "penalty_if_missed": "high" }
  ],
  "red_herrings": ["investigation_id_ANA", "investigation_id_viral_panel"]
}
```

### 4.6 `ScoringRubric` — how performance is evaluated

```json
{
  "rubric_id": "uuid",
  "case_id": "uuid (FK → Case)",
  "max_score": 100,
  "components": {
    "diagnosis_accuracy": { "weight_percent": 40, "exact_match_score": 40, "acceptable_match_score": 20, "wrong_score": 0 },
    "investigation_efficiency": { "weight_percent": 25, "description": "Penalise unnecessary/redundant tests", "excess_test_penalty_per_test": 2 },
    "critical_action_completion": { "weight_percent": 25, "description": "Binary — did they do the must-do steps?" },
    "time_efficiency": { "weight_percent": 10, "par_time_minutes": 12, "penalty_per_minute_over": 1 }
  },
  "harm_flags": [
    {
      "investigation_id": "lumbar_puncture_id",
      "condition": "if ordered before correcting coagulopathy",
      "penalty": "case_failed",
      "feedback": "LP in uncorrected DIC/APL is contraindicated — risk of fatal hemorrhage"
    }
  ]
}
```

> **`harm_flags`** enable the single most powerful teaching moment in clinical simulation: "you harmed the patient." Use sparingly and only where clinically defensible.

### 4.7 `SyntheticDataLog` — audit trail for AI-generated data

```json
{
  "log_id": "uuid",
  "case_id": "uuid",
  "investigation_id": "uuid",
  "parameter": "ALT",
  "synthetic_value": 34,
  "unit": "U/L",
  "generation_prompt": "Patient has APL confirmed by FISH t(15;17). Age 34M. Generate plausible ALT. No hepatic involvement in source report.",
  "model_used": "claude-sonnet-4-6",
  "generated_at": "timestamp",
  "review_status": "pending",
  "reviewed_by": "doctor_id",
  "reviewed_value": null,
  "review_note": null
}
```

---

## 5. Case Sourcing Strategy

**Primary source:** open-access, peer-reviewed case reports (e.g. *BMC Hematology / BMC series*, *Hematology Reports* (MDPI), *American Journal of Case Reports*, *Blood* open-access items). Peer-reviewed and clinically validated by definition; CC-BY licensing permits data reuse with attribution.

**Strengths:** real diagnostic journeys (not textbook-perfect), embedded clinical reasoning in the discussion section, no copyright barrier.

**Deliberate caveats to manage:**

- Case reports skew toward **rare/unusual** presentations (that's why they're published). Balance the library with **common** hematology presentations (iron-deficiency anemia, uncomplicated ITP) that won't appear as reports because they're "unremarkable." Author these de novo.
- Reports often log only relevant/abnormal investigations. Missing fields are handled by the **synthetic fill** pipeline below.

**Attribution:** store `doi`, `journal`, `year`, and `license` on every case (see `Case.source`).

---

## 6. Synthetic Data Pipeline

The mechanism that turns an incomplete case report into a complete, playable case — safely.

```
Case Report (ground-truth anchor)
        ↓
Extract: demographics, presenting complaints,
         key abnormal labs, imaging, FINAL DIAGNOSIS
        ↓
AI fills missing fields using clinical context
  (e.g. "Patient has APL; generate plausible CBC,
   LFT, RFT, coagulation profile within normal limits
   unless the diagnosis implies otherwise")
        ↓
Synthetic fields flagged (is_synthetic = true) + logged
        ↓
Clinician review queue  ← YOU validate every synthetic field
        ↓
Approved → case goes live
```

**Why this is medically defensible:** generation is **constrained** — anchored to a known, confirmed diagnosis — not free invention. This dramatically reduces hallucination risk, and the clinician review step is the final safety gate. Every synthetic value is individually reviewable and overridable via `SyntheticDataLog`.

---

## 7. AI Strategy

### 7.1 Model choice: Claude/GPT API vs MedGemma 1.5

**MedGemma 1.5 4B** (Google, `google/medgemma-1.5-4b-it`) is an open, medically-tuned model: compute-efficient, suitable for **offline/local deployment on modest hardware** (~6GB VRAM, or CPU slowly), with explicit support for medical document understanding (structured extraction from lab reports) and EHR understanding. MedQA ~69%, lab-report extraction F1 ~78%.

**Honest trade-off:**

| | Claude/GPT API | MedGemma 1.5 4B (local) |
|---|---|---|
| Broad medical reasoning & dialogue | Stronger | Good, narrower |
| Complex structured-output adherence | Stronger | Adequate |
| PDF/case-report extraction accuracy | Stronger | Adequate |
| Cost | Per-token | Free after download |
| Data locality / privacy | Data leaves premises | Fully local |
| Auditability / version-lock | Vendor-controlled | Full control, fine-tunable |
| Constrained synthetic fill (structured) | Overkill | Ideal |

> **Note:** MedGemma is explicitly a *starting point* requiring validation/adaptation; its outputs are **not** intended to directly inform real clinical decisions. That's fine here — every output is clinician-reviewed and the app is educational, not diagnostic.

**Decision:** Claude/GPT API for R&D and case-report extraction (accuracy, iteration speed); migrate the repetitive **synthetic-fill** step to local MedGemma to cut cost; consider a **fine-tuned MedGemma** for the production Simulator once the case library is large enough to fine-tune on.

### 7.2 CMS AI access — tiered by project phase

```
Phase          Method                  Cost    Control   Speed
─────────────────────────────────────────────────────────────
R&D / Early    Copy-paste (Project)    Free    Full      Slow
CMS Build      Ollama local (MedGemma) Free    Full      Medium
Production     API (Claude primary)    Paid    Medium    Fast
Simulator      MedGemma fine-tuned     Free    Full      Fast
```

- **Copy-paste via a Claude Project** — schema + guidelines held as persistent context; paste case content, get schema-shaped JSON. Zero infra. Ideal for the first handful of cases where hands-on review is a feature, not a cost.
- **Ollama / LM Studio (local MedGemma)** — best fit for the **synthetic-fill** step specifically: repetitive, structured, and clinician-reviewed downstream.
- **API (Claude primary, Gemini fallback)** — best for DOI/PDF extraction into the detailed schema at scale.

### 7.3 Simulator runtime — TWO options laid out (decision pending)

The Simulator's first version can go either way. Both documented; decision deferred.

#### Option 1 — Fully deterministic (no LLM at runtime)

All patient responses and results are **pre-authored** in the schema; scoring is **algorithmic** against `DiagnosticPath` + `ScoringRubric`.

- **Pros:** fast, zero runtime cost, fully predictable/reproducible, nothing can hallucinate to a student, trivial to host, works offline.
- **Cons:** history-taking limited to pre-authored `presenting_symptoms` (ask-to-reveal), no free-text patient conversation.
- **Best when:** shipping the core investigation→diagnosis→scoring loop quickly and safely.

#### Option 2 — Conversational Patient AI from the start

An LLM powers free-text history-taking (like Full Code's Patient AI) — the user "talks" to the patient.

- **Pros:** richer communication-skills practice; higher engagement.
- **Cons:** runtime cost (API) or on-device model weight (MedGemma); needs guardrails so the patient never leaks the diagnosis or invents findings that contradict the case; adds latency; more validation surface.
- **Deployment split if chosen:** Claude API server-side for the webapp; fine-tuned MedGemma on-device for mobile.

> **Recommendation to resolve later:** ship **Option 1** first (the deterministic loop is the product's spine and is inherently safe), then layer **Option 2** as an enhancement once the case library and scoring are proven. Revisit after the first 10–15 cases are live.

---

## 8. Case-Authoring Workflow (C → A → B progression)

Three architectures for getting a case report into the database. Use them **in sequence** as the schema matures — deliberately starting manual.

### Option C — Claude Project (structured copy-paste) · zero setup

Schema + instructions live in a Claude Project, so you paste only case content, not the schema each time.

```
Claude Project: "HemoSim Case Builder"
  System prompt: full schema + authoring instructions
  Uploaded docs: ICD-10 heme list, normal lab ranges, key guidelines
Workflow:
  1. Paste DOI abstract + key findings
  2. Claude → schema-shaped JSON
  3. You review/correct as clinician
  4. Paste JSON into Supabase
```

- **Removes:** re-explaining the task each time.
- **Remains:** paste input, copy output.
- **Use for:** cases **1–5**. Manual friction here is doing real work — it surfaces schema gaps against real papers before you automate.

### Option A — Claude.ai + Supabase MCP (semi-automated)

MCP lets **Claude reach your tools** (fetch a paper, write to Supabase) from within a chat. It does **not** reduce pasting *into* Claude — it removes copy-pasting Claude's *output* back out.

```
You (in Claude.ai): "Process DOI 10.1186/xxx"
        ↓
Claude via MCP: fetch paper → structure → write DRAFT row to Supabase
        ↓
You: review the row in the CMS/Supabase, approve
```

- **Removes:** output copy-paste to DB.
- **Remains:** you still trigger each case manually in chat (fine while you want to eyeball each).
- **Setup:** Supabase MCP server + a fetch/web MCP server on your Claude.ai account (~an afternoon).
- **Use for:** cases **6–15**, as the schema stabilizes.

### Option B — API batch script (fully automated) · end state

A standalone script (not MCP) runs outside any chat and produces draft cases in batches.

```python
for doi in list_of_dois:
    paper      = fetch_paper(doi)         # CrossRef / fetch
    structured = claude_api(paper)        # extract → schema
    synthetic  = claude_api(structured)   # fill missing fields
    write_to_supabase(structured, status="pending_review")
```

- **Removes:** all copy-paste AND per-case chat triggering.
- **Remains:** clinician review (never removed) — done in batches via the CMS review queue.
- **Cost:** a few cents of tokens per case.
- **Use for:** cases **16+**, once the schema is locked.

> **Guiding rule:** don't optimize the copy-paste away too early. Automating a broken schema just generates broken cases faster. Automate only after the schema has survived contact with ~5 real papers.

---

## 9. Phased Roadmap

```
Week 0 — Schema validation (NO code yet)
├── Set up Claude Project "HemoSim Case Builder" (schema as context)
├── Source 2–3 open-access APL/AML case reports
├── Run them through the schema manually (Option C)
└── Note & fix schema gaps the real cases reveal

Week 1–2 — Foundation
├── Create Supabase project
├── Implement the 7-entity schema as tables + migrations
└── Seed the validated 2–3 cases via Supabase dashboard

Week 3–4 — CMS (App 1)
├── DOI import → CrossRef metadata
├── Claude API extraction from case-report text/PDF
├── Case editor UI (patient, investigations, diagnostic path)
├── Synthetic-data generation + review queue
└── Approve/publish workflow  →  graduate to Option A (MCP)

Week 5–6 — Simulator (App 2), Option 1 deterministic
├── Case browser + dashboard
├── Patient presentation + ask-to-reveal history
├── Investigation ordering interface
├── Algorithmic scoring engine (DiagnosticPath + ScoringRubric)
└── Feedback screen (teaching points, harm flags)

Week 7+ — First real library + scale
├── Import 10–15 hematology cases (graduate to Option B batch)
├── Validate all synthetic data (clinician review)
├── Beta test with 2–3 medical students
└── Decide on Patient AI (Option 2) based on feedback

Later
├── React Native mobile Simulator
├── Fine-tune MedGemma on the case library
├── On-device Patient AI for mobile
└── Open CMS to trusted clinician contributors (platform play)
```

---

## 10. Open Decisions & Risks

**Decisions pending:**

1. **Simulator runtime** — Option 1 (deterministic) vs Option 2 (Patient AI). Leaning Option 1 first; revisit after 10–15 live cases.
2. **Production CMS model** — Claude API vs local MedGemma for extraction (fill step likely local either way).
3. **Common-case coverage** — how many de novo "bread-and-butter" cases to author alongside case-report-derived rare ones.

**Risks & mitigations:**

- *Rare-case skew from case reports* → deliberately author common presentations de novo.
- *Synthetic data inaccuracy* → constrained generation anchored to confirmed diagnosis + mandatory clinician review + full audit log.
- *Schema rigidity* → validate against real papers before automating (Week 0).
- *Scope creep across specialties* → stay in Hematology until the loop is proven end-to-end.
- *Over-reliance on AI reasoning for scoring* → scoring is deterministic/algorithmic, not LLM-judged, in v1.
- *Attribution/licensing* → only CC-BY (or equivalent) open-access sources; store license + DOI per case.

---

## 11. The Moat

Most medical-education apps stall because **content creation is the bottleneck**. Building a proper CMS from day one — DOI import, AI-assisted extraction, clinician review workflow — is infrastructure that could later let hematologists worldwide contribute validated cases. That is what turns a study app into a **platform**. PubMed alone holds thousands of open-access hematology case reports waiting to become cases.

---

*End of planning document.*
