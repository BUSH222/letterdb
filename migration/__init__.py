"""One-off database migrations. Run each from the project root, in order:

    uv run python -m migration.m01_cleanup_columns
    uv run python -m migration.m02_keywords_regions

Each script backs up a SQLite database first and does nothing if it has already been applied.
"""

import os
import shutil
from datetime import datetime, timezone
from typing import Set

from sqlalchemy import inspect
from sqlalchemy.engine import make_url

from letterdb.config import DATABASE_URL
from letterdb.db import engine


def backup_sqlite(name: str) -> None:
    """Copy a SQLite database into maindb-backups/ before migrating; other databases need their own dump."""
    url = make_url(DATABASE_URL)
    if url.get_backend_name() != "sqlite" or url.database is None:
        print("Not SQLite: make a backup of the database yourself before running this.")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    directory = os.path.join(os.path.dirname(url.database), "maindb-backups")
    os.makedirs(directory, exist_ok=True)
    base = os.path.splitext(os.path.basename(url.database))[0]
    target = os.path.join(directory, f"{base}_before_{name}_{stamp}.db")
    shutil.copy(url.database, target)
    print(f"Backup: {target}")


def columns(table: str) -> Set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table)}
