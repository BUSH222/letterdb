"""Reading and writing letters, search, and the catalogue lists.

Search and the lists compare text in Python because SQLite's lower() does not handle Cyrillic.
With a few hundred letters and a few thousand keywords this is cheap.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import groupby
from typing import TYPE_CHECKING

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select

from letterdb.models import Keyword, Letter, LetterKeyword, LetterRegion, Region
from letterdb.text import extract_year, fold, normalise_name, word_start_rank

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from sqlalchemy.orm import Session

TEXT_FIELDS = ("date", "addressee", "contents_txt", "imagelink", "comments", "notes")
SINGLE_LINE_FIELDS = ("date", "addressee")

FILTER_LABELS = {
    "year": "год",
    "addressee": "адресат",
    "keyword": "ключевое слово",
    "region": "регион",
}


@dataclass(frozen=True)
class TermKind:
    """Keywords and regions work the same way: a table of terms, linked to letters."""

    model: type[Keyword] | type[Region]
    link: type[LetterKeyword] | type[LetterRegion]
    links_attr: str  # Letter.keyword_links / Letter.region_links
    field: str  # Letter.keywords / Letter.regions, and the form field


TERM_KINDS = {
    "keyword": TermKind(Keyword, LetterKeyword, "keyword_links", "keywords"),
    "region": TermKind(Region, LetterRegion, "region_links", "regions"),
}


class InvalidLetter(ValueError):
    """The submitted letter cannot be saved."""


# Reading


def all_letters(session: Session) -> list[Letter]:
    """All letters, in catalogue order."""
    return list(session.scalars(select(Letter).order_by(Letter.catalogue)))


def get(session: Session, catalogue: int) -> Letter | None:
    return session.get(Letter, catalogue)


def next_catalogue(session: Session) -> int:
    """The highest catalogue number plus one (0 for an empty database)."""
    highest = session.scalar(select(func.max(Letter.catalogue)))
    return 0 if highest is None else highest + 1


def as_dict(letter: Letter) -> dict[str, object]:
    """The letter's fields for a template, with NULL columns as empty strings."""
    data: dict[str, object] = {name: getattr(letter, name) or "" for name in TEXT_FIELDS}
    data["catalogue"] = letter.catalogue
    data["keywords"] = letter.keywords
    data["regions"] = letter.regions
    return data


def suggest_terms(session: Session, kind: str, query: str) -> list[str]:
    """Keywords or regions with a word starting with `query` (case-insensitive, ё = е).

    Terms that start with the query come first, then the rest; each group alphabetically.
    """
    names = session.scalars(select(TERM_KINDS[kind].model.name))
    ranked = [(rank, fold(name), name) for name in names if (rank := word_start_rank(name, query)) is not None]
    return [name for _, _, name in sorted(ranked)]


# Writing


def _fields_from_form(form: Mapping[str, object]) -> tuple[int, dict[str, str]]:
    """The catalogue number and the text fields."""
    catalogue = str(form.get("catalogue") or "").strip()
    if not catalogue.isdigit():
        raise InvalidLetter("Каталожный номер должен состоять из цифр.")
    fields = {name: str(form.get(name) or "") for name in TEXT_FIELDS}
    for name in SINGLE_LINE_FIELDS:  # typed into a textarea, so drop stray newlines
        fields[name] = normalise_name(fields[name])
    return int(catalogue), fields


def _form_terms(form: Mapping[str, object], kind: TermKind) -> list[str]:
    value = form.get(kind.field) or []
    return [str(name) for name in value] if isinstance(value, list | tuple) else [str(value)]


def _set_terms(session: Session, letter: Letter, kind: TermKind, names: Iterable[str]) -> None:
    """Link the letter to these terms, in order. A name matching an existing term (ignoring case and ё/е)
    reuses it; anything else becomes a new term."""
    existing = {fold(term.name): term for term in session.scalars(select(kind.model))}
    links = []
    for name in names:
        name = normalise_name(name)
        if not name or any(fold(link.term.name) == fold(name) for link in links):
            continue
        term = existing.get(fold(name))
        if term is None:
            term = existing[fold(name)] = kind.model(name=name)
        links.append(kind.link(term=term, position=len(links)))
    setattr(letter, kind.links_attr, links)


def _delete_unused_terms(session: Session) -> None:
    session.flush()
    for kind in TERM_KINDS.values():
        session.execute(sql_delete(kind.model).where(kind.model.id.not_in(select(kind.link.term_id))))


def _save_terms(session: Session, letter: Letter, form: Mapping[str, object]) -> None:
    for kind in TERM_KINDS.values():
        _set_terms(session, letter, kind, _form_terms(form, kind))
    _delete_unused_terms(session)


def create(session: Session, form: Mapping[str, object]) -> Letter:
    number, fields = _fields_from_form(form)
    if get(session, number) is not None:
        raise InvalidLetter(f"Письмо с номером {number} уже существует.")
    letter = Letter(catalogue=number, **fields)
    session.add(letter)
    _save_terms(session, letter, form)
    session.commit()
    return letter


def update(session: Session, catalogue: int, form: Mapping[str, object]) -> Letter | None:
    """Update a letter; the catalogue number itself may change. Returns None if it does not exist."""
    letter = get(session, catalogue)
    if letter is None:
        return None
    number, fields = _fields_from_form(form)
    if number != catalogue and get(session, number) is not None:
        raise InvalidLetter(f"Письмо с номером {number} уже существует.")
    # Unlink first, so that a changed catalogue number never leaves links pointing at the old one.
    letter.keyword_links = []
    letter.region_links = []
    session.flush()
    letter.catalogue = number
    for name, value in fields.items():
        setattr(letter, name, value)
    session.flush()
    _save_terms(session, letter, form)
    session.commit()
    return letter


def delete(session: Session, catalogue: int) -> bool:
    letter = get(session, catalogue)
    if letter is None:
        return False
    session.delete(letter)
    _delete_unused_terms(session)
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
    if kind in TERM_KINDS:
        key = fold(normalise_name(value))
        field = TERM_KINDS[kind].field
        return [letter for letter in letters if key in {fold(name) for name in getattr(letter, field)}]
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


def term_counts(session: Session, kind: str) -> list[tuple[str, int]]:
    """[(term, number of letters), ...] for 'keyword' or 'region'.

    Most frequent first; terms with the same count in alphabetical order.
    """
    term_kind = TERM_KINDS[kind]
    rows = session.execute(
        select(term_kind.model.name, func.count())
        .join(term_kind.link, term_kind.link.term_id == term_kind.model.id)
        .group_by(term_kind.model.id)
    )
    return sorted(((name, n) for name, n in rows), key=lambda item: (-item[1], fold(item[0])))
