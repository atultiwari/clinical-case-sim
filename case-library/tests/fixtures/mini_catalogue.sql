-- A tiny catalogue for the fixture case (tests only).
insert into casevault.catalogue_item (id, kind, name, synonyms, active, since_version) values
  ('LAB.CBC', 'test', 'Full blood count', '{CBC,FBC}', true, 0),
  ('LAB.BLOOD_LEAD', 'test', 'Blood lead', '{"lead level","blood lead level"}', true, 0),
  ('LAB.FILM', 'test', 'Peripheral blood film', '{"blood film",smear}', true, 0),
  ('LAB.UA', 'test', 'Urinalysis', '{"urine test",UA}', true, 0),
  ('LAB.RENAL', 'test', 'Renal profile', '{"kidney function",U&E}', true, 0),
  ('HX.PRESENTING', 'history', 'Presenting complaint', '{complaint,problem}', true, 0),
  ('HX.OCCUPATION', 'history', 'Occupation', '{job,work}', true, 0),
  ('HX.SUPPLEMENTS', 'history', 'Supplements', '{herbal,remedies}', true, 0),
  ('REF.TOXICOLOGY', 'referral', 'Clinical toxicology', '{toxicology,poisons}', true, 0),
  ('DX.LEAD_POISONING', 'diagnosis', 'Lead poisoning', '{saturnism,"lead toxicity"}', true, 0);
insert into casevault.test_def (item_id, route, price_inr, tat_minutes) values
  ('LAB.CBC', 'direct', 150, 60), ('LAB.BLOOD_LEAD', 'direct', 1200, 2880),
  ('LAB.FILM', 'service.pathology', 100, 120), ('LAB.UA', 'direct', 80, 60),
  ('LAB.RENAL', 'direct', 250, 120);
insert into casevault.component (id, name, unit_si, decimals, ref_ranges, normal_text) values
  ('CMP.HB', 'Haemoglobin', 'g/L', 0,
   '[{"sex": "F", "low": 115, "high": 165}, {"sex": "M", "low": 130, "high": 180}]', null),
  ('CMP.RBC', 'Red cell count', 'x10^12/L', 2, '[{"sex": "F", "low": 3.8, "high": 4.8}]', null),
  ('CMP.MCH', 'Mean cell haemoglobin', 'pg', 1, '[{"low": 27, "high": 32}]', null),
  ('CMP.PB', 'Blood lead', 'ug/dL', 1, '[{"low": 0, "high": 5}]', null),
  ('CMP.UA_COLOUR', 'Urine colour', null, null, null, 'Straw'),
  -- Sodium's sex-specific ranges are deliberately far apart, so tests can tell them apart.
  ('CMP.NA', 'Sodium', 'mmol/L', 0,
   '[{"sex": "F", "low": 136, "high": 145}, {"sex": "M", "low": 150, "high": 160}]', null),
  ('CMP.K', 'Potassium', 'mmol/L', 1, '[{"low": 3.5, "high": 5.1}]', null);
insert into casevault.test_component (test_item_id, component_id, position) values
  ('LAB.CBC', 'CMP.HB', 1), ('LAB.CBC', 'CMP.RBC', 2), ('LAB.CBC', 'CMP.MCH', 3),
  ('LAB.BLOOD_LEAD', 'CMP.PB', 1), ('LAB.UA', 'CMP.UA_COLOUR', 1),
  ('LAB.RENAL', 'CMP.NA', 1), ('LAB.RENAL', 'CMP.K', 2);
insert into casevault.normal_template (item_id, template, review_status) values
  ('HX.OCCUPATION', 'Works in an office.', 'approved'),
  ('HX.PRESENTING', 'Nothing else to add.', 'approved');
insert into casevault.value_rule (id, kind, target, inputs, formula) values
  ('R.MCH', 'ratio', 'CMP.MCH', '{CMP.HB,CMP.RBC}', 'MCH (pg) = Hb (g/L) / RBC (x10^12/L)');
