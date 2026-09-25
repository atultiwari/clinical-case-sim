-- step: 6 Ground truth
-- writes: ground_truth (1 row, replaced while the version is a draft)
-- params: cv, ground_truth:jsonb
-- Rubric anchors, must-do and must-not-do carry text plus a condition (SPEC §10.4).
delete from casevault.ground_truth g
using casevault.case_version v
where g.case_version_id = {{cv}} and v.id = g.case_version_id and v.status = 'draft';
select casevault.import_ground_truth({{cv}}, {{ground_truth:jsonb}});
