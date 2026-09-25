-- step: 8 Resolve
-- writes: synthetic_ledger (normal rows: components, approved templates, formula targets)
-- params: cv, skill_version
-- Deterministic; never touches items on a path (SPEC §6.5).
select casevault.resolve_normals({{cv}}, 'normal-generator v1', {{skill_version}}) as normal_rows;
