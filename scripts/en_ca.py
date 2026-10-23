"""Canadian English from the US English source.

Canadian English keeps -ize (organize, prioritize) but takes -our, -re and
the doubled l, and the Canadian pages price in Canadian dollars. The
changes apply to visible text only: tags, attributes, scripts, styles and
code samples (CSS variable names such as --color-primary) are left alone.
"""
from __future__ import annotations

import re

SPELLINGS = {
    "color": "colour",
    "colors": "colours",
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
}

# US list price -> Canadian list price (about 1.36, rounded the way a price
# list would be). Kept in step with the fr-CA brief's table.
PRICES = {
    "$18,000": "$24,500",
    "$42,000": "$57,000",
    "$90,000": "$122,000",
    "$900": "$1,225",
    "$750": "$1,025",
    "$6,000": "$8,200",
    "$8,000": "$10,900",
    "$5,000": "$6,800",
}

PHRASES = [
    (r"US\s+dollars", "Canadian dollars"),
    (r"US\s+English", "Canadian English"),
]

_WORD = re.compile(r"\b(" + "|".join(SPELLINGS) + r")\b", re.I)
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
    """Canadian English for a run of visible text."""
    value = _WORD.sub(_respell, value)
    value = _PRICE.sub(lambda m: PRICES.get(m.group(0), m.group(0)), value)
    for pattern, repl in PHRASES:
        value = re.sub(pattern, repl, value)
    return value


_READABLE_ATTR = re.compile(r'\b(alt|title|aria-label|placeholder)="([^"]*)"')


def _tag(tag: str) -> str:
    if tag.startswith("<") and not re.match(r"<(script|style|code|pre)\b", tag, re.I):
        return _READABLE_ATTR.sub(lambda m: f'{m.group(1)}="{text(m.group(2))}"', tag)
    return tag


def html(source: str) -> str:
    """Canadian English for an HTML fragment: text nodes and the attributes
    a reader sees (alt, title, aria-label, placeholder)."""
    out, last = [], 0
    for m in _SKIP.finditer(source):
        out.append(text(source[last:m.start()]))
        out.append(_tag(m.group(0)))
        last = m.end()
    out.append(text(source[last:]))
    return "".join(out)
