"""Redaction of leaked diagnosis terms from text bound for a seat (SPEC §9).

Titles, keywords, figure captions and the article's discussion are removed in the Case
Library before a bundle is exported (D-021), and seat views have no field for the case's
display title or tags. What remains for Sambhasha is a last guard on text generated at run
time, such as a Synthetic Findings Service narrative: `redact` blanks any leaked term.
"""

from typing import Final

from sambhasha.curation.leakscan import Lexicon, find_leaks

REDACTED: Final = "[redacted]"


def redact(text: str, lexicon: Lexicon, placeholder: str = REDACTED) -> str:
    """The text with every leaked term replaced; overlapping matches become one placeholder."""
    spans: list[tuple[int, int]] = []
    for leak in find_leaks(text, lexicon):
        if spans and leak.start < spans[-1][1]:
            spans[-1] = (spans[-1][0], max(spans[-1][1], leak.end))
        else:
            spans.append((leak.start, leak.end))
    pieces: list[str] = []
    cursor = 0
    for start, end in spans:
        pieces += [text[cursor:start], placeholder]
        cursor = end
    return "".join([*pieces, text[cursor:]])
