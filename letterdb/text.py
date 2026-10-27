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


def word_start_rank(name: str, query: str) -> int | None:
    """Whether `query` matches the start of a word in `name` (case-insensitive, ё = е).

    0 if `name` itself starts with it, 1 if a later word does, None if neither.
    'лес' matches 'лёсс' and 'совещание по лёссу', but not 'слесарь'.
    """
    name, query = fold(normalise_name(name)), fold(normalise_name(query))
    if not query:
        return None
    if name.startswith(query):
        return 0
    starts = (i for i in range(1, len(name)) if not name[i - 1].isalnum() and name[i].isalnum())
    return 1 if any(name.startswith(query, i) for i in starts) else None
