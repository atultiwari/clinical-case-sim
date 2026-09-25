"""Schema 0.3 integrity rules: frozen versions and the ledger (SPEC §10.2, PLAN L0.3)."""

from typing import Any

import psycopg
import pytest

from tests.integration.conftest import seed_case_version

pytestmark = pytest.mark.integration

INSERT_FACT = (
    "insert into casevault.fact"
    " (case_version_id, id, category, item, origin, release, source_locator,"
    "  generator, skill_version)"
    " values (%s, %s, 'lab', 'Haemoglobin', 'article', 'chart', 'Table 1', 'g', 's')"
)
INSERT_MEDIA = (
    "insert into casevault.media (case_version_id, id, licence, redacted_caption)"
    " values (%s, 'M01', 'CC BY 4.0', 'Blood film.')"
)
INSERT_LEDGER = (
    "insert into casevault.synthetic_ledger"
    " (case_version_id, target, day_bucket, tier, value, generator, skill_version,"
    "  review_status, supersedes)"
    " values (%s, %s, %s, 'normal', '{\"value\": 140}', 'normal-generator v1', 's', %s, %s)"
    " returning id"
)
APPROVE = (
    "update casevault.synthetic_ledger set review_status = 'approved',"
    " reviewed_by = 'reviewer', reviewed_at = now() where id = %s"
)
SUPERSEDE = "update casevault.synthetic_ledger set review_status = 'superseded' where id = %s"
CHECK_NOW = "set constraints casevault.check_supersession immediate"


def _freeze(db: psycopg.Connection, cv: str) -> None:
    db.execute(
        "update casevault.case_version set status = 'frozen', frozen_at = now() where id = %s",
        (cv,),
    )


def _ledger(
    db: psycopg.Connection,
    cv: str,
    day: int | None = 0,
    status: str = "pending",
    supersedes: Any = None,
    target: str = "CMP.NA",
) -> Any:
    row = db.execute(INSERT_LEDGER, (cv, target, day, status, supersedes)).fetchone()
    assert row is not None
    return row[0]


# --- Frozen case versions ----------------------------------------------------


def test_draft_facts_can_change(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    db.execute(INSERT_FACT, (cv, "L01"))

    db.execute("update casevault.fact set value = '72' where case_version_id = %s", (cv,))


@pytest.mark.parametrize(
    "statement",
    [
        "update casevault.fact set value = '99' where case_version_id = %s",
        "delete from casevault.fact where case_version_id = %s",
    ],
)
def test_frozen_facts_cannot_change(db: psycopg.Connection, statement: str) -> None:
    cv = seed_case_version(db)
    db.execute(INSERT_FACT, (cv, "L01"))
    _freeze(db, cv)

    with pytest.raises(psycopg.errors.RestrictViolation), db.transaction():
        db.execute(statement, (cv,))


def test_frozen_version_takes_no_new_facts(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    _freeze(db, cv)

    with pytest.raises(psycopg.errors.RestrictViolation), db.transaction():
        db.execute(INSERT_FACT, (cv, "L02"))


def test_frozen_figures_accept_production_decisions_only(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    db.execute(INSERT_MEDIA, (cv,))
    _freeze(db, cv)

    db.execute(
        "update casevault.media set production_decision = 'mask', masked_path = 'x/M01-masked.jpg',"
        " decided_by = 'reviewer', decided_at = now() where case_version_id = %s",
        (cv,),
    )
    with pytest.raises(psycopg.errors.RestrictViolation), db.transaction():
        db.execute(
            "update casevault.media set redacted_caption = 'Changed.' where case_version_id = %s",
            (cv,),
        )


def test_frozen_version_can_only_be_retired(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    _freeze(db, cv)

    for statement in (
        "update casevault.case_version set status = 'draft', frozen_at = null where id = %s",
        "update casevault.case_version set vignette = 'Changed.' where id = %s",
        "delete from casevault.case_version where id = %s",
    ):
        with pytest.raises(psycopg.errors.RestrictViolation), db.transaction():
            db.execute(statement, (cv,))

    db.execute("update casevault.case_version set status = 'retired' where id = %s", (cv,))
    with pytest.raises(psycopg.errors.RestrictViolation), db.transaction():
        db.execute("update casevault.case_version set status = 'frozen' where id = %s", (cv,))


# --- One live ledger row per target and day ----------------------------------


@pytest.mark.parametrize("day", [0, None], ids=["day-0", "all-admission"])
def test_second_live_row_for_same_target_and_day_fails(
    db: psycopg.Connection, day: int | None
) -> None:
    cv = seed_case_version(db)
    _ledger(db, cv, day)

    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        _ledger(db, cv, day)


def test_rejected_row_leaves_room_for_a_new_one(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    first = _ledger(db, cv)
    db.execute(
        "update casevault.synthetic_ledger set review_status = 'rejected',"
        " reviewed_by = 'reviewer', reviewed_at = now() where id = %s",
        (first,),
    )

    _ledger(db, cv)


def test_other_days_and_targets_are_separate(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    _ledger(db, cv, 0)

    _ledger(db, cv, 1)
    _ledger(db, cv, None)
    _ledger(db, cv, 0, target="CMP.K")


# --- Ledger: append-only, one-time review, supersession ----------------------


def test_ledger_rows_cannot_be_deleted(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    row = _ledger(db, cv)

    with pytest.raises(psycopg.errors.RestrictViolation), db.transaction():
        db.execute("delete from casevault.synthetic_ledger where id = %s", (row,))


def test_ledger_values_cannot_be_updated(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    row = _ledger(db, cv)

    with pytest.raises(psycopg.errors.RestrictViolation), db.transaction():
        db.execute(
            "update casevault.synthetic_ledger set value = '{\"value\": 150}' where id = %s", (row,)
        )


def test_review_fields_are_set_once(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    row = _ledger(db, cv)
    db.execute(APPROVE, (row,))

    with pytest.raises(psycopg.errors.RestrictViolation), db.transaction():
        db.execute(
            "update casevault.synthetic_ledger set review_note = 'Changed my mind' where id = %s",
            (row,),
        )


def test_review_needs_reviewer_and_time(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    row = _ledger(db, cv)

    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute(
            "update casevault.synthetic_ledger set review_status = 'approved' where id = %s", (row,)
        )


@pytest.mark.parametrize("new_status", ["rejected", "pending", "edited"])
def test_approved_row_can_only_become_superseded(db: psycopg.Connection, new_status: str) -> None:
    cv = seed_case_version(db)
    row = _ledger(db, cv)
    db.execute(APPROVE, (row,))

    with pytest.raises(psycopg.errors.RestrictViolation), db.transaction():
        db.execute(
            "update casevault.synthetic_ledger set review_status = %s where id = %s",
            (new_status, row),
        )


def test_approved_row_is_superseded_by_a_replacement(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    old = _ledger(db, cv)
    db.execute(APPROVE, (old,))

    db.execute(SUPERSEDE, (old,))
    _ledger(db, cv, status="edited", supersedes=old)
    db.execute(CHECK_NOW)


def test_superseding_without_a_replacement_fails(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    row = _ledger(db, cv)
    db.execute(APPROVE, (row,))

    with db.transaction(force_rollback=True):
        db.execute(SUPERSEDE, (row,))
        with pytest.raises(
            psycopg.errors.IntegrityConstraintViolation, match="without a replacement"
        ):
            db.execute(CHECK_NOW)


def test_replacement_must_match_target_and_day(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)
    old = _ledger(db, cv)
    db.execute(APPROVE, (old,))
    db.execute(SUPERSEDE, (old,))

    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        _ledger(db, cv, day=3, status="edited", supersedes=old)


@pytest.mark.parametrize("status", ["rejected", "superseded"])
def test_new_rows_cannot_start_closed(db: psycopg.Connection, status: str) -> None:
    cv = seed_case_version(db)

    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        _ledger(db, cv, status=status)


def test_edited_row_must_name_what_it_supersedes(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)

    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        _ledger(db, cv, status="edited")
