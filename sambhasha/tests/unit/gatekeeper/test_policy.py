"""P1.3: the permission matrix in configs/permissions.yaml (SPEC §6)."""

from pathlib import Path

import pytest

from sambhasha.gatekeeper.policy import PermissionsError, in_scope, load_permissions, seat_class

PERMISSIONS = load_permissions()


@pytest.mark.parametrize(
    ("seat", "action", "allowed"),
    [
        ("attending", "order_test", True),
        ("attending", "commit", True),
        ("challenger", "challenge", True),
        ("challenger", "order_test", False),
        ("service.pathology", "report", True),
        ("service.pathology", "ask_history", False),
        ("consultant.haematology", "consult_note", True),
        ("consultant.haematology", "commit", False),
    ],
)
def test_the_matrix(seat: str, action: str, allowed: bool) -> None:
    referred = frozenset({"consultant.haematology"})

    assert (PERMISSIONS.check(seat, action, referred) is None) is allowed


def test_seat_classes() -> None:
    assert [seat_class(s) for s in ("attending", "consultant.x", "service.radiology")] == [
        "attending",
        "consultant",
        "service",
    ]


@pytest.mark.parametrize(
    ("seat", "scope", "allowed"),
    [
        ("attending", ("attending", "consultant.*"), True),
        ("consultant.neurology", ("attending", "consultant.*"), True),
        ("consultant.neurology", ("consultant.ophthalmology",), False),
        ("attending", ("consultant.ophthalmology",), False),
        ("attending", (), True),
    ],
)
def test_item_scope(seat: str, scope: tuple[str, ...], allowed: bool) -> None:
    assert in_scope(seat, scope) is allowed


def test_a_missing_file_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(PermissionsError, match="not found"):
        load_permissions(tmp_path / "absent.yaml")


def test_a_malformed_file_is_a_clear_error(tmp_path: Path) -> None:
    path = tmp_path / "permissions.yaml"
    path.write_text("actions: {}\n", encoding="utf-8")

    with pytest.raises(PermissionsError, match="refusals"):
        load_permissions(path)
