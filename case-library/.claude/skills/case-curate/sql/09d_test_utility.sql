-- step: 9 Author
-- writes: test_utility (one row per test on the case's paths, plus the routine admission panel)
-- params: cv, utility:jsonb
-- utility: [{"test_item_id": "LAB.TOX.BLOOD_LEAD", "utility": "essential", "rationale": "..."}]
insert into casevault.test_utility (case_version_id, test_item_id, utility, rationale)
select {{cv}}, u ->> 'test_item_id', u ->> 'utility', u ->> 'rationale'
from jsonb_array_elements({{utility:jsonb}}) u
on conflict (case_version_id, test_item_id) do update
  set utility = excluded.utility, rationale = excluded.rationale;
