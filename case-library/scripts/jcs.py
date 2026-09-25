"""RFC 8785 JSON Canonicalization Scheme (JCS).

Bundles are written once with this serializer, and their SHA-256 is taken over
the bytes it produces (SPEC §7.5, §10.5). Same data, same bytes.

- Object keys are sorted by their UTF-16 code units.
- Numbers are IEEE 754 doubles, written as ECMAScript's Number.prototype.toString.
- Strings escape only what JSON requires; everything else is literal UTF-8.
- No whitespace.
"""

import json
import math
from decimal import Decimal
from typing import Any

# Integers beyond 2**53 cannot survive the round trip through a double.
MAX_SAFE_INTEGER = 2**53
# ECMAScript switches to exponent notation outside 1e-7 < |x| < 1e21.
MAX_PLAIN_EXPONENT = 21
MIN_PLAIN_EXPONENT = -6


class CanonicalizationError(ValueError):
    """The value cannot be written as canonical JSON."""


def canonicalize(value: Any) -> bytes:
    """Return the RFC 8785 canonical UTF-8 bytes of a JSON-compatible value."""
    return _serialize(value).encode("utf-8")


def _serialize(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return _number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list | tuple):
        return "[" + ",".join(_serialize(item) for item in value) + "]"
    if isinstance(value, dict):
        return _object(value)
    raise CanonicalizationError(f"Cannot canonicalize a {type(value).__name__}.")


def _object(value: dict[Any, Any]) -> str:
    if not all(isinstance(key, str) for key in value):
        raise CanonicalizationError("Object keys must be strings.")
    keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
    return "{" + ",".join(f"{_serialize(key)}:{_serialize(value[key])}" for key in keys) + "}"


def _number(value: int | float) -> str:
    if isinstance(value, int) and abs(value) > MAX_SAFE_INTEGER:
        raise CanonicalizationError(f"Integer {value} is outside the safe range of a double.")
    number = float(value)
    if not math.isfinite(number):
        raise CanonicalizationError("NaN and infinity are not valid JSON.")
    if number == 0:
        return "0"
    sign = "-" if number < 0 else ""
    return sign + _format_positive(abs(number))


def _format_positive(number: float) -> str:
    # repr gives the shortest digits that round-trip, as ECMAScript does.
    parts = Decimal(repr(number)).normalize().as_tuple()
    digits = "".join(str(d) for d in parts.digits)
    exponent = int(parts.exponent)
    point = len(digits) + exponent  # the value is 0.<digits> x 10**point

    if len(digits) <= point <= MAX_PLAIN_EXPONENT:
        return digits + "0" * (point - len(digits))
    if 0 < point <= MAX_PLAIN_EXPONENT:
        return digits[:point] + "." + digits[point:]
    if MIN_PLAIN_EXPONENT < point <= 0:
        return "0." + "0" * -point + digits
    mantissa = digits[0] + ("." + digits[1:] if len(digits) > 1 else "")
    shown = point - 1
    return f"{mantissa}e{'+' if shown > 0 else '-'}{abs(shown)}"
