-- step: 8 Resolve
-- writes: synthetic_ledger (one row per affected or reviewer-placeholder value)
-- params: cv, rows:jsonb, generator, skill_version
-- rows: [{"target": "LAB.TOX.ZPP", "day_bucket": 0, "tier": "affected", "gap_id": "G11",
--         "value": {"value": 180, "unit": "umol/mol haem", "ref_range": "<70"},
--         "release_text": "...", "lay_text": null, "priority": "high", "judgement_call": false,
--         "rationale": "...", "confidence": 0.8}]
-- Every affected row needs a rationale and a confidence (SPEC §6.4, rule 7).
insert into casevault.synthetic_ledger
  (case_version_id, target, day_bucket, tier, gap_id, value, release_text, lay_text, priority,
   judgement_call, rationale, confidence, generator, skill_version)
select {{cv}}, r ->> 'target', (r ->> 'day_bucket')::int, r ->> 'tier', r ->> 'gap_id', r -> 'value',
       r ->> 'release_text', r ->> 'lay_text', r ->> 'priority',
       coalesce((r ->> 'judgement_call')::boolean, false), r ->> 'rationale',
       (r ->> 'confidence')::numeric, {{generator}}, {{skill_version}}
from jsonb_array_elements({{rows:jsonb}}) r;
