-- step: 9 Author
-- writes: consult_note (one row per specialty variant, plus rule notes off the paths)
-- params: cv, notes:jsonb, generator, skill_version
-- notes: [{"id": "CN01", "specialty": "REF.HAEMATOLOGY", "variant": 1, "condition": {...},
--          "note_text": "...", "recommendations": ["..."], "origin": "affected", "rationale": "...", "confidence": 0.7}]
insert into casevault.consult_note
  (case_version_id, id, specialty, variant, condition, note_text, recommendations, origin,
   rationale, confidence, generator, skill_version)
select {{cv}}, n ->> 'id', n ->> 'specialty', coalesce((n ->> 'variant')::int, 1), n -> 'condition',
       n ->> 'note_text', casevault.json_text_array(n -> 'recommendations'), n ->> 'origin',
       n ->> 'rationale', (n ->> 'confidence')::numeric, {{generator}}, {{skill_version}}
from jsonb_array_elements({{notes:jsonb}}) n;
