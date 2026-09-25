-- step: 4 Extract
-- writes: fact (one row per history fact released by a catalogue item)
-- params: cv, links:jsonb
-- links: [{"fact": "H10", "released_by": ["HX.MEDS.SUPPLEMENTS", "HX.MEDS.SUPPLEMENT_DETAILS"]}, ...]
update casevault.fact f
set released_by = casevault.json_text_array(l -> 'released_by')
from jsonb_array_elements({{links:jsonb}}) l
where f.case_version_id = {{cv}} and f.id = l ->> 'fact';
