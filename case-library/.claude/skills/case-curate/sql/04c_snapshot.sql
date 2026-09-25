-- step: 4 Extract
-- writes: source_article (1 row)
-- params: pmcid, fulltext_format, fulltext, content_hash
-- Store the full-text snapshot and its SHA-256 once the source row exists (after the import above).
update casevault.source_article
set fulltext_format = {{fulltext_format}}, fulltext = {{fulltext}},
    content_hash = {{content_hash}}, fetched_at = now()
where pmcid = {{pmcid}} and (content_hash is null or content_hash = {{content_hash}});
