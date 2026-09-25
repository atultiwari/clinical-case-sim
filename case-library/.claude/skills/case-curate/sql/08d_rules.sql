-- step: 8 Resolve
-- writes: synthetic_ledger (rule rows)
-- params: cv, rows:jsonb, generator, skill_version
-- Fixed template replies, e.g. {"target": "LAB.CHEM.PSA", "value": {"text": "Not applicable"},
-- "release_text": "Not applicable: prostate-specific antigen is not measured for this patient."}
insert into casevault.synthetic_ledger
  (case_version_id, target, day_bucket, tier, value, release_text, priority, generator, skill_version)
select {{cv}}, r ->> 'target', (r ->> 'day_bucket')::int, 'rule', r -> 'value', r ->> 'release_text',
       'low', {{generator}}, {{skill_version}}
from jsonb_array_elements({{rows:jsonb}}) r;
