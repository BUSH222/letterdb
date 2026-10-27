"""Move keywords and regions out of the letterdb text columns into their own tables.

- Creates `keywords` (id, keyword) and `regions` (id, region), plus the link tables
  `letter_keywords` and `letter_regions` (letter, term, position).
- Splits the old comma/semicolon-separated text into terms. Spellings that differ only in
  case or ё/е are merged into one term, using the most common spelling.
- Drops the old `keywords` and `regions` columns from letterdb.
"""

from collections import Counter, defaultdict

from sqlalchemy import text

from letterdb.db import Base, engine
from letterdb.models import Keyword, LetterKeyword, LetterRegion, Region
from letterdb.text import fold, split_terms
from migration import backup_sqlite, columns

# old letterdb column -> (term table, its name column, link table, its term id column)
KINDS = {
    "keywords": ("keywords", "keyword", "letter_keywords", "keyword_id"),
    "regions": ("regions", "region", "letter_regions", "region_id"),
}


def build_terms(rows: list[tuple[int, str | None]]) -> tuple[list[dict[str, int | str]], list[dict[str, int]]]:
    """Term rows and link rows for one column, from (catalogue, text) pairs."""
    per_letter = [(catalogue, split_terms(value)) for catalogue, value in rows]
    spellings: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for _, names in per_letter:
        for name in names:
            spellings[fold(name)][name] += 1

    ids = {key: i for i, key in enumerate(sorted(spellings), start=1)}
    terms = [{"id": ids[key], "name": counts.most_common(1)[0][0]} for key, counts in spellings.items()]
    links = [
        {"letter": catalogue, "term": ids[fold(name)], "position": position}
        for catalogue, names in per_letter
        for position, name in enumerate(names)
    ]
    return terms, links


def main() -> None:
    if "keywords" not in columns("letterdb"):
        print("Already applied.")
        return
    backup_sqlite("m02")

    with engine.begin() as conn:
        models = (Keyword, Region, LetterKeyword, LetterRegion)
        Base.metadata.create_all(conn, tables=[Base.metadata.tables[model.__tablename__] for model in models])
        for column, (term_table, name_column, link_table, id_column) in KINDS.items():
            rows = [(row[0], row[1]) for row in conn.execute(text(f"SELECT catalogue, {column} FROM letterdb"))]
            terms, links = build_terms(rows)
            conn.execute(text(f"INSERT INTO {term_table} (id, {name_column}) VALUES (:id, :name)"), terms)
            insert_link = f"INSERT INTO {link_table} (letter_catalogue, {id_column}, position)"
            conn.execute(text(f"{insert_link} VALUES (:letter, :term, :position)"), links)
            print(f"{column}: {len(terms)} terms, {len(links)} links")
        conn.execute(text("ALTER TABLE letterdb DROP COLUMN keywords"))
        conn.execute(text("ALTER TABLE letterdb DROP COLUMN regions"))


if __name__ == "__main__":
    main()
