-- step: 8 Resolve
-- writes: synthetic_ledger (normal rows: components, approved templates, formula targets)
-- params: cv, skill_version
-- Deterministic; never touches items on a path (SPEC §6.5).
-- The second formula pass fills targets whose inputs are themselves calculated
-- (the albumin/globulin ratio uses the calculated globulin).
select casevault.resolve_normals({{cv}}, 'normal-generator v1', {{skill_version}})
       + casevault.resolve_normal_derived({{cv}}, 'normal-generator v1', {{skill_version}})
       as normal_rows;
