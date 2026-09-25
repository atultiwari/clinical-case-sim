-- step: 9 Author
-- writes: report (one row per variant)
-- params: cv, reports:jsonb, generator, skill_version
-- An 'original' variant is provisional and must carry a status line (enforced by a constraint).
insert into casevault.report
  (case_version_id, id, test_item_id, variant, status, status_line, findings, report_text,
   impression, suggested_reflex, based_on, origins, rationale, confidence, generator, skill_version)
select {{cv}}, r ->> 'id', r ->> 'test_item_id', r ->> 'variant', r ->> 'status', r ->> 'status_line',
       casevault.json_text_array(r -> 'findings'), r ->> 'report_text', r ->> 'impression',
       casevault.json_text_array(r -> 'suggested_reflex'), casevault.json_text_array(r -> 'based_on'),
       casevault.json_text_array(r -> 'origins'), r ->> 'rationale', (r ->> 'confidence')::numeric,
       {{generator}}, {{skill_version}}
from jsonb_array_elements({{reports:jsonb}}) r;
