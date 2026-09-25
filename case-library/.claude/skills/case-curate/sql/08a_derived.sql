-- step: 8 Resolve
-- writes: fact (derived rows from casevault.value_rule formulas)
-- params: cv, generator, skill_version
select casevault.compute_derived({{cv}}, {{generator}}, {{skill_version}}) as derived_rows;
