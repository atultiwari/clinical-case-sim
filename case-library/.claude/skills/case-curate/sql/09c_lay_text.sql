-- step: 9 Author
-- writes: fact (lay_text on history facts)
-- params: cv, lay:jsonb
-- lay: [{"fact": "H10", "lay_text": "Actually, yes. A friend gave me a herbal supplement..."}]
-- The lay text carries exactly the clinical fact: no added symptoms, no lost negatives (SPEC §6.7).
update casevault.fact f
set lay_text = l ->> 'lay_text'
from jsonb_array_elements({{lay:jsonb}}) l
where f.case_version_id = {{cv}} and f.id = l ->> 'fact';
