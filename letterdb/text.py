"""Helpers that read structure out of the plaintext letter fields."""

import re

_YEAR = re.compile(r"\d{4}")
_TERM_SEPARATORS = re.compile(r"[,;]")
_WHITESPACE = re.compile(r"\s+")


def fold(s: str | None) -> str:
    """Comparison key: case-insensitive, with ё treated as е."""
    return (s or "").casefold().replace("ё", "е")


def extract_year(date: str | None) -> int | None:
    """The first four-digit number in a (possibly partial) date such as '1952.02.' or '1952-1955'."""
    match = _YEAR.search(date or "")
    return int(match.group()) if match else None


def normalise_name(s: str | None) -> str:
    """Collapse runs of whitespace and strip."""
    return _WHITESPACE.sub(" ", s or "").strip()


def split_terms(s: str | None) -> list[str]:
    """Split a keywords/regions string on ',' and ';', dropping blanks and repeats."""
    terms = []
    seen = set()
    for part in _TERM_SEPARATORS.split(s or ""):
        term = normalise_name(part)
        if term and fold(term) not in seen:
            seen.add(fold(term))
            terms.append(term)
    return terms
