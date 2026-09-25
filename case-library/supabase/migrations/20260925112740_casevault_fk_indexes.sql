-- Indexes for foreign keys that have none (Supabase performance advisor, PLAN L0.3).
-- ledger_supersedes also serves check_supersession's lookup at commit.

create index case_source_id on casevault."case" (source_id);
create index raw_material_test_item_id on casevault.raw_material (test_item_id);
create index report_test_item_id on casevault.report (test_item_id);
create index review_decision_batch_id on casevault.review_decision (batch_id);
create index ledger_gap on casevault.synthetic_ledger (case_version_id, gap_id);
create index ledger_supersedes on casevault.synthetic_ledger (supersedes);
create index test_component_component_id on casevault.test_component (component_id);
create index test_utility_test_item_id on casevault.test_utility (test_item_id);
