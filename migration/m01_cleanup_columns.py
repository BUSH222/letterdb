"""Clean up the legacy columns of the letterdb table.

- `published` is dropped.
- `filename` is dropped. Values that are empty, '-' or end in '.txt' are discarded;
  anything else is appended to `comments`.
- `imagelink` keeps only Flickr embeds and 'нет'; anything else is moved to `comments`.
- `catalogue` becomes an INTEGER primary key ('001' -> 1, '000' -> 0).
- Trailing dots are stripped from `date` ('1946.04.' -> '1946.04').
"""

from typing import Any

from sqlalchemy import Column, Integer, MetaData, Table, Text, select, text

from letterdb.db import engine
from migration import backup_sqlite, columns

KEPT_COLUMNS = ("date", "adressee", "keywords", "regions", "contents_txt", "imagelink", "comments", "notes")


def append(comments: str | None, extra: str) -> str:
    comments = (comments or "").rstrip()
    return f"{comments}\n\n{extra}" if comments else extra


def clean_row(row: dict[str, Any]) -> dict[str, Any]:
    comments = row["comments"]

    filename = (row["filename"] or "").strip()
    if filename and filename != "-" and not filename.lower().endswith(".txt"):
        comments = append(comments, filename)

    imagelink = row["imagelink"]
    stripped = (imagelink or "").strip()
    if stripped and "<a data-flickr-embed" not in stripped and stripped != "нет":
        comments = append(comments, stripped)
        imagelink = None

    date = row["date"].rstrip().rstrip(".") if row["date"] is not None else None

    return {
        **{name: row[name] for name in KEPT_COLUMNS},
        "catalogue": int(row["catalogue"].strip()),
        "date": date,
        "imagelink": imagelink,
        "comments": comments,
    }


def main() -> None:
    if "filename" not in columns("letterdb"):
        print("Already applied.")
        return
    backup_sqlite("m01")

    new_table = Table(
        "letterdb_new",
        MetaData(),
        Column("catalogue", Integer, primary_key=True, autoincrement=False),
        *(Column(name, Text) for name in KEPT_COLUMNS),
    )
    with engine.begin() as conn:
        old_table = Table("letterdb", MetaData(), autoload_with=conn)
        rows = [clean_row(dict(row)) for row in conn.execute(select(old_table)).mappings()]
        new_table.create(conn)
        conn.execute(new_table.insert(), rows)
        conn.execute(text("DROP TABLE letterdb"))
        conn.execute(text("ALTER TABLE letterdb_new RENAME TO letterdb"))
    print(f"Migrated {len(rows)} letters.")


if __name__ == "__main__":
    main()
