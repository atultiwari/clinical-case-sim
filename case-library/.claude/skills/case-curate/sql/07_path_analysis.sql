-- step: 7 Path analysis
-- writes: path_analysis (one row per path)
-- params: cv, paths:jsonb
-- paths: [{"path_id": "P1", "kind": "efficient", "name": "...", "rationale": "...", "items": ["HX...", "LAB..."]}]
insert into casevault.path_analysis (case_version_id, path_id, kind, name, rationale, items)
select {{cv}}, p ->> 'path_id', p ->> 'kind', p ->> 'name', p ->> 'rationale',
       casevault.json_text_array(p -> 'items')
from jsonb_array_elements({{paths:jsonb}}) p
on conflict (case_version_id, path_id) do update
  set kind = excluded.kind, name = excluded.name, rationale = excluded.rationale, items = excluded.items;
