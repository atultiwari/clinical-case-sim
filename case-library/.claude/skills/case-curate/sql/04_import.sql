-- step: 4 Extract
-- writes: source_article, case, case_version (draft), fact, raw_material, media, gap, ground_truth
-- params: doc:jsonb, generator, skill_version
-- One call imports the whole gold case file (steps 1-6 content) as a new draft version.
select casevault.import_case_json({{doc:jsonb}}, {{generator}}, {{skill_version}}) as case_version_id;
