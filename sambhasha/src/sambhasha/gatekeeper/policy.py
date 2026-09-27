"""Who may do what: the permission matrix in `configs/permissions.yaml` (SPEC §6).

Item-level limits come from the catalogue: each item's `specialty_scope` lists the seats
that may use it ("attending", "consultant.*", "consultant.ophthalmology", ...).
"""

import fnmatch
from pathlib import Path
from typing import Final

import yaml
from pydantic import ValidationError

from sambhasha.domain.base import DomainModel
from sambhasha.domain.seats import is_consultant, is_service

DEFAULT_PERMISSIONS: Final = Path(__file__).resolve().parents[3] / "configs" / "permissions.yaml"
ACTION_PHRASES: Final = {
    "ask_history": "take a history",
    "examine": "examine",
    "bedside_test": "do bedside tests",
    "order_test": "order tests",
    "refer": "refer",
    "consult_note": "write consult notes",
    "report": "write reports",
    "update_differential": "update the differential",
    "challenge": "challenge",
    "commit": "commit",
    "wait": "wait for results",
}


class PermissionsError(ValueError):
    """The permissions file is missing or malformed."""


class Refusals(DomainModel):
    not_permitted: str
    consultant_orders: str
    no_referral: str
    out_of_scope: str
    vague: str
    protocol: str
    not_understood: str


class Permissions(DomainModel):
    actions: dict[str, tuple[str, ...]]
    consultants_need_referral: bool
    refusals: Refusals

    def check(self, seat: str, action: str, referred: frozenset[str]) -> str | None:
        """None if the seat may take the action now; otherwise the refusal to show it."""
        role = seat_class(seat)
        if role not in self.actions.get(action, ()):
            if role == "consultant" and action == "order_test":
                return self.refusals.consultant_orders
            return self.refusals.not_permitted.format(
                role=role.replace("_", " "), action=ACTION_PHRASES.get(action, action)
            )
        if role == "consultant" and self.consultants_need_referral and seat not in referred:
            return self.refusals.no_referral
        return None


def seat_class(seat: str) -> str:
    if is_consultant(seat):
        return "consultant"
    if is_service(seat):
        return "service"
    return seat


def in_scope(seat: str, scope: tuple[str, ...]) -> bool:
    """Whether a catalogue item's specialty_scope admits the seat. An empty scope admits all."""
    return not scope or any(fnmatch.fnmatchcase(seat, pattern) for pattern in scope)


def load_permissions(path: Path = DEFAULT_PERMISSIONS) -> Permissions:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise PermissionsError(f"permissions file not found: {path}") from error
    try:
        return Permissions.model_validate(data)
    except ValidationError as error:
        raise PermissionsError(f"{path.name}: {error}") from error
