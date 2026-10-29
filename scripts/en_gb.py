"""British English from the US English source.

British English takes -ise (organise, prioritise), -our, -re and the doubled
l, the British pages price in pounds sterling, and the workshop sessions read
in UK time with Pacific time beside it. The changes apply to visible text
only: tags, attributes, scripts, styles and code samples (CSS variable names
such as --color-primary) are left alone.
"""
from __future__ import annotations

import re

SPELLINGS = {
    "color": "colour",
    "colors": "colours",
    "colored": "coloured",
    "recolor": "recolour",
    "full-color": "full-colour",
    "behavior": "behaviour",
    "behaviors": "behaviours",
    "favorite": "favourite",
    "favorites": "favourites",
    "honor": "honour",
    "labor": "labour",
    "neighbor": "neighbour",
    "center": "centre",
    "centers": "centres",
    "catalog": "catalogue",
    "gray": "grey",
    "canceled": "cancelled",
    "labeled": "labelled",
    "modeling": "modelling",
    "traveled": "travelled",
    "fulfill": "fulfil",
    "enrollment": "enrolment",
    "defense": "defence",
    "licenses": "licences",
    "analyze": "analyse",
    "analyzed": "analysed",
}

# -ize stems that take -ise in British English. An explicit list, so "size"
# and "prize" are never touched.
ISE_STEMS = (
    "organ", "reorgan", "priorit", "recogn", "revolution", "capital", "anonym",
    "custom", "optim", "standard", "summar", "real", "util", "minim", "maxim",
    "categor", "emphas", "personal", "special", "apolog", "author", "central",
    "final", "normal", "visual", "synchron", "modern", "familiar", "character",
)

# US list price -> British list price (about 0.78, rounded the way a price
# list would be).
PRICES = {
    "$18,000": "£14,000",
    "$42,000": "£32,500",
    "$90,000": "£70,000",
    "$900": "£700",
    "$750": "£580",
    "$6,000": "£4,700",
    "$8,000": "£6,200",
    "$5,000": "£3,900",
}

# The workshop sessions, in UK time (GMT in November and December) first.
SESSION_TIMES = {
    "9:00 to 10:00 am PT / 12:00 to 1:00 pm ET": "5:00 to 6:00 pm GMT (9:00 to 10:00 am PT)",
    "11:00 am to 12:00 pm PT / 2:00 to 3:00 pm ET": "7:00 to 8:00 pm GMT (11:00 am to 12:00 pm PT)",
    "8:00 to 9:00 am PT / 11:00 am to 12:00 pm ET": "4:00 to 5:00 pm GMT (8:00 to 9:00 am PT)",
}

PHRASES = [
    (r"US\s+dollars", "pounds sterling"),
    (r"US\s+English", "British English"),
    (r"Times\s+are\s+shown\s+in\s+Pacific\s+and\s+Eastern\s+time\.",
     "Times are shown in UK time, with Pacific time alongside."),
]

_WORD = re.compile(r"\b(" + "|".join(re.escape(w) for w in sorted(SPELLINGS, key=len, reverse=True)) + r")\b", re.I)
_ISE = re.compile(r"\b(" + "|".join(ISE_STEMS) + r")iz(e|es|ed|ing|ation|ations)\b", re.I)
_PRICE = re.compile(r"\$\d[\d,]*(?![\d,]*\d)")
_SKIP = re.compile(r"(<(script|style|code|pre)\b.*?</\2>|<[^>]+>)", re.S | re.I)


def _respell(match: re.Match[str]) -> str:
    word = match.group(0)
    out = SPELLINGS[word.lower()]
    if word.isupper():
        return out.upper()
    if word[0].isupper():
        return out[0].upper() + out[1:]
    return out


def text(value: str) -> str:
    """British English for a run of visible text."""
    value = _WORD.sub(_respell, value)
    value = _ISE.sub(lambda m: f"{m.group(1)}is{m.group(2)}", value)
    value = _PRICE.sub(lambda m: PRICES.get(m.group(0), m.group(0)), value)
    for us, uk in SESSION_TIMES.items():
        value = value.replace(us, uk)
    for pattern, repl in PHRASES:
        value = re.sub(pattern, repl, value)
    return value


_READABLE_ATTR = re.compile(r'\b(alt|title|aria-label|placeholder)="([^"]*)"')


def _tag(tag: str) -> str:
    if tag.startswith("<") and not re.match(r"<(script|style|code|pre)\b", tag, re.I):
        return _READABLE_ATTR.sub(lambda m: f'{m.group(1)}="{text(m.group(2))}"', tag)
    return tag


def html(source: str) -> str:
    """British English for an HTML fragment: text nodes and the attributes
    a reader sees (alt, title, aria-label, placeholder)."""
    out, last = [], 0
    for m in _SKIP.finditer(source):
        out.append(text(source[last:m.start()]))
        out.append(_tag(m.group(0)))
        last = m.end()
    out.append(text(source[last:]))
    return "".join(out)
