"""P0.5: redaction of leaked diagnosis terms from text bound for a seat."""

from sambhasha.curation.leakscan import Lexicon
from sambhasha.curation.redact import REDACTED, redact

LEXICON = Lexicon(terms=("lead poisoning", "plumbism"), allowed=("blood lead",))


def test_leaked_terms_are_replaced() -> None:
    text = "Findings suggest Lead poisoning (plumbism)."

    assert redact(text, LEXICON) == f"Findings suggest {REDACTED} ({REDACTED})."


def test_allowed_phrases_and_clean_text_are_untouched() -> None:
    text = "Blood lead 77.8 µg/dL; film shows coarse basophilic stippling."

    assert redact(text, LEXICON) == text


def test_redaction_finds_nothing_left_to_scan() -> None:
    from sambhasha.curation.leakscan import find_leaks

    once = redact("plumbism, lead\npoisoning and PLUMBISM", LEXICON)

    assert find_leaks(once, LEXICON) == ()


def test_overlapping_terms_become_one_placeholder() -> None:
    lexicon = Lexicon(terms=("lead poisoning", "poisoning from lead"), allowed=())

    assert redact("It was lead poisoning from lead paint.", lexicon) == f"It was {REDACTED} paint."
