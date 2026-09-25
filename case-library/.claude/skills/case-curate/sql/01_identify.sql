-- step: 1 Identify
-- writes: nothing
-- params: pmcid
-- Stop if the article or its case is already in the Case Vault.
select s.pmcid, s.title, s.licence, c.id as case_id,
       (select array_agg(v.id || ' ' || v.status order by v.version)
        from casevault.case_version v where v.case_id = c.id) as versions
from casevault.source_article s
left join casevault."case" c on c.source_id = s.id
where s.pmcid = {{pmcid}};
