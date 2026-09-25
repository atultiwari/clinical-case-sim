"""RFC 8785 canonical JSON (scripts/jcs.py)."""

import math

import pytest

from scripts.jcs import CanonicalizationError, canonicalize


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        # RFC 8785 §3.2.2.3 and appendix B examples.
        (0.0, "0"),
        (-0.0, "0"),
        (333333333.33333329, "333333333.3333333"),
        (1e30, "1e+30"),
        (4.50, "4.5"),
        (2e-3, "0.002"),
        (0.000000000000000000000000001, "1e-27"),
        (1e21, "1e+21"),
        (1e20, "100000000000000000000"),
        (1e-7, "1e-7"),
        (0.000001, "0.000001"),
        (-1.5, "-1.5"),
        (72, "72"),
        (72.0, "72"),
        (5e-324, "5e-324"),
        (1.7976931348623157e308, "1.7976931348623157e+308"),
        (9007199254740992, "9007199254740992"),
    ],
)
def test_numbers_follow_ecmascript(number: float, expected: str) -> None:
    assert canonicalize(number) == expected.encode()


def test_keys_sort_by_utf16_code_units() -> None:
    # RFC 8785 §3.2.3: by UTF-16 code unit, so U+20AC (0x20AC) sorts before the emoji,
    # whose first code unit is 0xD83D, although its code point is higher.
    value = {"\u20ac": "Euro", "\r": "CR", "\U0001f600": "Smiley", "1": "One", "\u00f6": "o"}

    assert canonicalize(value).decode() == (
        '{"\\r":"CR","1":"One","\u00f6":"o","\u20ac":"Euro","\U0001f600":"Smiley"}'
    )


def test_no_whitespace_and_nested_order() -> None:
    value = {"b": [1, {"d": True, "c": None}], "a": "x"}

    assert canonicalize(value) == b'{"a":"x","b":[1,{"c":null,"d":true}]}'


def test_strings_escape_only_what_json_needs() -> None:
    assert canonicalize('é "q" \\ \n \u001f /') == '"é \\"q\\" \\\\ \\n \\u001f /"'.encode()


@pytest.mark.parametrize("bad", [math.nan, math.inf, 2**53 + 1, {1: "x"}, {1, 2}])
def test_invalid_values_are_refused(bad: object) -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize(bad)
