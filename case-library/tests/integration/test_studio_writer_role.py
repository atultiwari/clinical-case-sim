"""casevault_studio_writer: the Case Studio v2 writer role (SPEC §8, PLAN L1.5).

It records review decisions in Studio batches and sets figure production
decisions, and can do nothing else.
"""

import psycopg
import pytest

from tests.integration.conftest import add_affected_cbc, seed_mini_case

pytestmark = pytest.mark.integration

WRITER = "casevault_studio_writer"
BATCH = "studio-2026-09-26-atul"


@pytest.fixture
def seeded(db: psycopg.Connection) -> tuple[psycopg.Connection, str]:
    """The fixture case with a ledger, loaded as the owner; the test then switches role."""
    cv = seed_mini_case(db)
    add_affected_cbc(db, cv)
    return db, cv


def _as(db: psycopg.Connection, role: str) -> None:
    db.execute(f"set local role {role}")


def _ledger_id(db: psycopg.Connection, cv: str) -> str:
    row = db.execute(
        "select id::text from casevault.synthetic_ledger where case_version_id = %s limit 1", (cv,)
    ).fetchone()
    assert row is not None
    return str(row[0])


def _open_batch(db: psycopg.Connection, cv: str, batch: str = BATCH) -> None:
    db.execute(
        "insert into casevault.review_batch (id, case_version_ids) values (%s, %s)", (batch, [cv])
    )


def test_the_writer_records_a_review_decision(seeded: tuple[psycopg.Connection, str]) -> None:
    db, cv = seeded
    ledger_id = _ledger_id(db, cv)
    _as(db, WRITER)
    _open_batch(db, cv)
    db.execute(
        "insert into casevault.review_decision (batch_id, target_table, target_id, decision,"
        " edited, note, decided_by) values (%s, 'synthetic_ledger', %s, 'edit',"
        " '{\"value\": 80}', 'Closer to day 0', 'atul')",
        (BATCH, ledger_id),
    )
    db.execute(
        "insert into casevault.review_decision (batch_id, target_table, target_id, decision,"
        " decided_by) values (%s, 'fact', %s, 'approve', 'atul')",
        (BATCH, f"{cv}/H01"),
    )
    row = db.execute(
        "select count(*) from casevault.review_decision where batch_id = %s", (BATCH,)
    ).fetchone()
    assert row == (2,)


def test_the_writer_adds_a_case_version_to_an_open_studio_batch(
    seeded: tuple[psycopg.Connection, str],
) -> None:
    db, cv = seeded
    _as(db, WRITER)
    _open_batch(db, cv)
    db.execute(
        "update casevault.review_batch set case_version_ids = case_version_ids || %s::text"
        " where id = %s",
        ("PMC0000002@v1", BATCH),
    )
    row = db.execute(
        "select case_version_ids from casevault.review_batch where id = %s", (BATCH,)
    ).fetchone()
    assert row == ([cv, "PMC0000002@v1"],)


def test_the_writer_sets_a_figure_decision(seeded: tuple[psycopg.Connection, str]) -> None:
    db, cv = seeded
    _as(db, WRITER)
    db.execute(
        "update casevault.media set production_decision = 'mask',"
        " masked_path = %s, decided_by = 'atul', decided_at = now()"
        " where case_version_id = %s and id = 'M01'",
        ("PMC0000001/M01-masked.png", cv),
    )
    row = db.execute(
        "select production_decision, masked_path, decided_by from casevault.media"
        " where case_version_id = %s and id = 'M01'",
        (cv,),
    ).fetchone()
    assert row == ("mask", "PMC0000001/M01-masked.png", "atul")


def test_the_writer_sets_a_figure_decision_after_freeze(
    seeded: tuple[psycopg.Connection, str],
) -> None:
    db, cv = seeded
    db.execute(
        "update casevault.case_version set status = 'frozen', frozen_at = now() where id = %s",
        (cv,),
    )
    _as(db, WRITER)
    db.execute(
        "update casevault.media set production_decision = 'use', decided_by = 'atul',"
        " decided_at = now() where case_version_id = %s and id = 'M01'",
        (cv,),
    )


@pytest.mark.parametrize(
    "statement",
    [
        # Other media columns.
        "update casevault.media set production_ok = false",
        "update casevault.media set licence = 'CC0'",
        "update casevault.media set file_path = 'x/y.png'",
        # Content tables.
        "update casevault.fact set value = 'x'",
        "insert into casevault.fact (case_version_id, id, category, item, origin, release,"
        " generator, skill_version, source_locator)"
        " values ('PMC0000001@v1', 'H99', 'history', 'x', 'article', 'chart', 'g', 'v', 'p1')",
        "update casevault.synthetic_ledger set review_status = 'approved',"
        " reviewed_by = 'atul', reviewed_at = now()",
        "insert into casevault.synthetic_ledger (case_version_id, target, tier, value, generator,"
        " skill_version) values ('PMC0000001@v1', 'CMP.HB', 'normal', '{}', 'g', 'v')",
        "update casevault.report set review_status = 'approved'",
        "update casevault.consult_note set review_status = 'approved'",
        "update casevault.case_version set status = 'frozen', frozen_at = now()",
        "update casevault.ground_truth set outcome = 'x'",
        "select * from casevault.ground_truth",
        "insert into casevault.missing_request (source, query) values ('nidana', 'x')",
        # Review tables beyond what the Studio needs.
        "update casevault.review_batch set applied_at = now()",
        "update casevault.review_decision set decision = 'reject'",
        "insert into casevault.review_decision (batch_id, target_table, target_id, decision,"
        " decided_by, decided_at) values ('studio-2026-09-26-atul', 'fact', 'x', 'approve',"
        " 'atul', now())",
        "insert into casevault.review_batch (id, case_version_ids, applied_at)"
        " values ('studio-2026-09-26-atul-2', '{PMC0000001@v1}', now())",
        # Deletes.
        "delete from casevault.review_decision",
        "delete from casevault.review_batch",
        "delete from casevault.media",
        "delete from casevault.fact",
        # Functions that write.
        "select casevault.import_case_json('{}'::jsonb, 'g', 'v')",
        "select casevault.resolve_normals('PMC0000001@v1')",
        "select casevault.compute_derived('PMC0000001@v1', 'g', 'v')",
    ],
)
def test_the_writer_cannot_do_anything_else(
    seeded: tuple[psycopg.Connection, str], statement: str
) -> None:
    db, cv = seeded
    _as(db, WRITER)
    _open_batch(db, cv)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(statement)


@pytest.mark.parametrize(
    ("batch", "target_table", "decision", "edited"),
    [
        ("pack-batch-1", "fact", "approve", None),  # not a Studio batch
        (BATCH, "ground_truth", "approve", None),  # not a reviewable table
        (BATCH, "fact", "edit", None),  # an edit needs the new value
        (BATCH, "fact", "approve", '{"value": 1}'),  # only an edit carries one
    ],
)
def test_row_level_security_refuses_other_decisions(
    seeded: tuple[psycopg.Connection, str],
    batch: str,
    target_table: str,
    decision: str,
    edited: str | None,
) -> None:
    db, cv = seeded
    db.execute(
        "insert into casevault.review_batch (id, case_version_ids) values ('pack-batch-1', %s)",
        ([cv],),
    )
    _as(db, WRITER)
    _open_batch(db, cv)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(
            "insert into casevault.review_decision (batch_id, target_table, target_id, decision,"
            " edited, decided_by) values (%s, %s, %s, %s, %s::jsonb, 'atul')",
            (batch, target_table, f"{cv}/H01", decision, edited),
        )


def test_the_writer_cannot_decide_into_an_applied_batch(
    seeded: tuple[psycopg.Connection, str],
) -> None:
    db, cv = seeded
    db.execute(
        "insert into casevault.review_batch (id, case_version_ids, applied_at)"
        " values (%s, %s, now())",
        (BATCH, [cv]),
    )
    _as(db, WRITER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(
            "insert into casevault.review_decision (batch_id, target_table, target_id, decision,"
            " decided_by) values (%s, 'fact', %s, 'approve', 'atul')",
            (BATCH, f"{cv}/H01"),
        )


@pytest.mark.parametrize("batch", ["pack-1", "studio-26-09-2026-atul", "studio-2026-09-26-Atul"])
def test_the_writer_creates_only_studio_batches(
    seeded: tuple[psycopg.Connection, str], batch: str
) -> None:
    db, cv = seeded
    _as(db, WRITER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _open_batch(db, cv, batch)


@pytest.mark.parametrize(
    "assignments",
    [
        "production_decision = 'pending', decided_by = 'atul', decided_at = now()",
        "production_decision = 'use', decided_by = null, decided_at = now()",
        "production_decision = 'use', masked_path = 'PMC0000001/M01.png',"
        " decided_by = 'atul', decided_at = now()",
    ],
)
def test_row_level_security_refuses_incomplete_figure_decisions(
    seeded: tuple[psycopg.Connection, str], assignments: str
) -> None:
    db, _ = seeded
    _as(db, WRITER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(f"update casevault.media set {assignments}")  # noqa: S608 (fixed test strings)


@pytest.mark.parametrize("role", ["anon", "authenticated"])
@pytest.mark.parametrize("table", ["review_decision", "review_batch", "media"])
def test_nidana_player_roles_still_see_nothing(
    seeded: tuple[psycopg.Connection, str], role: str, table: str
) -> None:
    db, _ = seeded
    _as(db, role)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(f"select * from casevault.{table}")  # noqa: S608 (fixed table names)


def _set_status(db: psycopg.Connection, cv: str, status: str) -> None:
    frozen = ", frozen_at = now()" if status in ("frozen", "retired") else ""
    db.execute(
        f"update casevault.case_version set status = %s{frozen} where id = %s",  # noqa: S608
        (status, cv),
    )


@pytest.mark.parametrize("status", ["draft", "in_review"])
def test_the_writer_decides_on_a_version_still_in_review(
    seeded: tuple[psycopg.Connection, str], status: str
) -> None:
    db, cv = seeded
    ledger_id = _ledger_id(db, cv)
    _set_status(db, cv, status)
    _as(db, WRITER)
    _open_batch(db, cv)
    for table, target in (("fact", f"{cv}/H01"), ("synthetic_ledger", ledger_id)):
        db.execute(
            "insert into casevault.review_decision (batch_id, target_table, target_id, decision,"
            " decided_by) values (%s, %s, %s, 'approve', 'atul')",
            (BATCH, table, target),
        )


@pytest.mark.parametrize("status", ["frozen", "retired"])
@pytest.mark.parametrize("target_table", ["fact", "synthetic_ledger"])
def test_the_writer_cannot_decide_on_a_frozen_or_retired_version(
    seeded: tuple[psycopg.Connection, str], status: str, target_table: str
) -> None:
    db, cv = seeded
    target = f"{cv}/H01" if target_table == "fact" else _ledger_id(db, cv)
    _set_status(db, cv, status)
    _as(db, WRITER)
    _open_batch(db, cv)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(
            "insert into casevault.review_decision (batch_id, target_table, target_id, decision,"
            " decided_by) values (%s, %s, %s, 'approve', 'atul')",
            (BATCH, target_table, target),
        )


@pytest.mark.parametrize(
    "target",
    ["PMC0000001@v1/NO_SUCH_ROW", "PMC0000002@v1/H01", "00000000-0000-0000-0000-000000000000"],
)
def test_the_writer_cannot_decide_on_a_row_outside_the_batch(
    seeded: tuple[psycopg.Connection, str], target: str
) -> None:
    db, cv = seeded
    _as(db, WRITER)
    _open_batch(db, cv)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(
            "insert into casevault.review_decision (batch_id, target_table, target_id, decision,"
            " decided_by) values (%s, 'fact', %s, 'approve', 'atul')",
            (BATCH, target),
        )


def test_the_writer_cannot_decide_on_a_retired_version_figure(
    seeded: tuple[psycopg.Connection, str],
) -> None:
    db, cv = seeded
    _set_status(db, cv, "retired")
    _as(db, WRITER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(
            "update casevault.media set production_decision = 'use', decided_by = 'atul',"
            " decided_at = now() where case_version_id = %s and id = 'M01'",
            (cv,),
        )
