-- step: 5 Redact
-- writes: case_version (1 row), case (1 row)
-- params: cv, vignette, opening_statement_lay, display_title, display_tags:textarray, slug
update casevault.case_version
set vignette = {{vignette}}, opening_statement_lay = {{opening_statement_lay}}
where id = {{cv}} and status = 'draft';
update casevault."case" c
set display_title = {{display_title}}, display_tags = {{display_tags:textarray}},
    slug = coalesce(c.slug, {{slug}})
from casevault.case_version v
where v.id = {{cv}} and c.id = v.case_id;
