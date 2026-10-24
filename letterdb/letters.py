"""Reading and writing letters, search, and the catalogue lists.

Search and the lists work on the letters in Python: the keyword/region/date fields are still
plaintext, and SQLite's lower() does not handle Cyrillic. With a few hundred letters this is cheap.
"""

from collections import Counter, defaultdict
from itertools import groupby
from typing import TYPE_CHECKING

from sqlalchemy import select

from letterdb.models import Letter
from letterdb.text import extract_year, fold, normalise_name, split_terms

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from sqlalchemy.orm import Session

LETTER_FIELDS = (
    "catalogue",
    "date",
    "addressee",
    "keywords",
    "regions",
    "contents_txt",
    "filename",
    "imagelink",
    "published",
    "comments",
    "notes",
)

FILTER_LABELS = {
    "year": "год",
    "addressee": "адресат",
    "keyword": "ключевое слово",
    "region": "регион",
}


class InvalidLetter(ValueError):
    """The submitted letter cannot be saved."""


# Reading


def _catalogue_sort_key(catalogue: str) -> tuple[int, int, str]:
    return (0, int(catalogue), catalogue) if catalogue.isdigit() else (1, 0, catalogue)


def all_letters(session: Session) -> list[Letter]:
    """All letters, in catalogue order."""
    letters = list(session.scalars(select(Letter)))
    letters.sort(key=lambda letter: _catalogue_sort_key(letter.catalogue))
    return letters


def get(session: Session, catalogue: str) -> Letter | None:
    return session.get(Letter, catalogue)


def as_dict(letter: Letter) -> dict[str, str]:
    """The letter's fields for a template, with NULL columns as empty strings."""
    return {name: getattr(letter, name) or "" for name in LETTER_FIELDS}


# Writing


def _fields_from_form(form: Mapping[str, object]) -> dict[str, str]:
    fields = {name: str(form.get(name) or "") for name in LETTER_FIELDS}
    fields["catalogue"] = fields["catalogue"].strip()
    if not fields["catalogue"].isdigit():
        raise InvalidLetter("Каталожный номер должен состоять из цифр.")
    return fields


def create(session: Session, form: Mapping[str, object]) -> Letter:
    fields = _fields_from_form(form)
    if get(session, fields["catalogue"]) is not None:
        raise InvalidLetter(f"Письмо с номером {fields['catalogue']} уже существует.")
    letter = Letter(**fields)
    session.add(letter)
    session.commit()
    return letter


def update(session: Session, catalogue: str, form: Mapping[str, object]) -> Letter | None:
    """Update a letter; the catalogue number itself may change. Returns None if it does not exist."""
    letter = get(session, catalogue)
    if letter is None:
        return None
    fields = _fields_from_form(form)
    if fields["catalogue"] != catalogue and get(session, fields["catalogue"]) is not None:
        raise InvalidLetter(f"Письмо с номером {fields['catalogue']} уже существует.")
    for name, value in fields.items():
        setattr(letter, name, value)
    session.commit()
    return letter


def delete(session: Session, catalogue: str) -> bool:
    letter = get(session, catalogue)
    if letter is None:
        return False
    session.delete(letter)
    session.commit()
    return True


# Search


def search(
    letters: Iterable[Letter], contents: str = "", addressee: str = "", comments_notes: str = ""
) -> list[Letter]:
    """Substring search, case-insensitive with ё = е. Every non-empty field has to match."""
    checks: list[tuple[str, Callable[[Letter], str]]] = [
        (fold(contents.strip()), lambda letter: fold(letter.contents_txt)),
        (fold(addressee.strip()), lambda letter: fold(letter.addressee)),
        (fold(comments_notes.strip()), lambda letter: fold(letter.comments) + "\n" + fold(letter.notes)),
    ]
    checks = [(needle, haystack) for needle, haystack in checks if needle]
    return [letter for letter in letters if all(needle in haystack(letter) for needle, haystack in checks)]


def filter_by(letters: Iterable[Letter], kind: str, value: str) -> list[Letter]:
    """Letters matching one catalogue-list filter (see FILTER_LABELS)."""
    if kind == "year":
        if not value.strip().isdigit():
            return []
        return [letter for letter in letters if extract_year(letter.date) == int(value)]
    if kind == "addressee":
        key = fold(normalise_name(value))
        return [letter for letter in letters if fold(normalise_name(letter.addressee)) == key]
    if kind in ("keyword", "region"):
        key = fold(normalise_name(value))
        field = "keywords" if kind == "keyword" else "regions"
        return [letter for letter in letters if key in {fold(t) for t in split_terms(getattr(letter, field))}]
    raise ValueError(f"Unknown filter: {kind}")


# Catalogue lists


class _Tally:
    """Counts names, merging spellings that differ only in case or ё/е, and shows the most common one."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self.spellings: defaultdict[str, Counter[str]] = defaultdict(Counter)

    def add(self, name: str) -> None:
        self.counts[fold(name)] += 1
        self.spellings[fold(name)][name] += 1

    def items(self) -> list[tuple[str, int]]:
        """(name, count) pairs in alphabetical order."""
        return [(self.spellings[key].most_common(1)[0][0], n) for key, n in sorted(self.counts.items())]


def years_by_decade(letters: Iterable[Letter]) -> list[tuple[int, list[tuple[int, int]]]]:
    """[(1940, [(1942, n), (1943, n), ...]), ...]; letters without a readable year are left out."""
    years = Counter(year for letter in letters if (year := extract_year(letter.date)) is not None)
    return [
        (decade, list(group)) for decade, group in groupby(sorted(years.items()), key=lambda item: item[0] // 10 * 10)
    ]


def addressees_by_letter(letters: Iterable[Letter]) -> list[tuple[str, list[tuple[str, int]]]]:
    """[("А", [(name, n), ...]), ...]."""
    tally = _Tally()
    for letter in letters:
        if name := normalise_name(letter.addressee):
            tally.add(name)
    return [
        (initial, list(group)) for initial, group in groupby(tally.items(), key=lambda item: fold(item[0])[:1].upper())
    ]


def term_counts(letters: Iterable[Letter], field: str) -> list[tuple[str, int]]:
    """[(term, number of letters), ...] for the 'keywords' or 'regions' field.

    Most frequent first; terms with the same count stay in alphabetical order.
    """
    tally = _Tally()
    for letter in letters:
        for term in split_terms(getattr(letter, field)):
            tally.add(term)
    return sorted(tally.items(), key=lambda item: -item[1])  # stable sort keeps the alphabetical order
