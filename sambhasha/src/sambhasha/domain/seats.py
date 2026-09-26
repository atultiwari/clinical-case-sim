"""Seat ids from the glossary (SPEC §1)."""

import re
from typing import Annotated, Final

from pydantic import AfterValidator

SERVICES: Final = ("pathology", "radiology", "microbiology")

_SEAT_ID = re.compile(
    r"attending|challenger|gatekeeper|synthetic|evaluator|scheduler"
    r"|consultant\.[a-z][a-z_]*"
    rf"|service\.(?:{'|'.join(SERVICES)})"
)


def validate_seat_id(seat: str) -> str:
    """Return the seat id unchanged, or raise ValueError if the glossary has no such seat."""
    if not _SEAT_ID.fullmatch(seat):
        raise ValueError(
            f"not a seat id: {seat!r}; expected attending, challenger, consultant.<specialty>, "
            f"service.<{'|'.join(SERVICES)}> or an engine role"
        )
    return seat


def is_consultant(seat: str) -> bool:
    return seat.startswith("consultant.")


def is_service(seat: str) -> bool:
    return seat.startswith("service.")


SeatId = Annotated[str, AfterValidator(validate_seat_id)]
