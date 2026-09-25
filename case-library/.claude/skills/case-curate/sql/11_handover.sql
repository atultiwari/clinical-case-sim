-- step: 11 Hand over
-- writes: case_version (1 row: draft -> in_review)
-- params: cv, generator, skill_version
-- Only after step 10 is clean. Never freeze or publish: those need Atul's words.
update casevault.case_version
set status = 'in_review', curated_by = {{generator}}, skill_version = {{skill_version}},
    curated_at = now()
where id = {{cv}} and status = 'draft';
select 'origin ' || origin as bucket, count(*) from casevault.fact where case_version_id = {{cv}} group by origin
union all
select 'ledger ' || tier || case when judgement_call then ' (judgement call)' else '' end, count(*)
from casevault.synthetic_ledger where case_version_id = {{cv}} and casevault.is_live(review_status)
group by tier, judgement_call
order by 1;
