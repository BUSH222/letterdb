from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from letterdb.config import DATABASE_URL

if TYPE_CHECKING:
    from collections.abc import Iterator

_url = make_url(DATABASE_URL)
_connect_args = {"check_same_thread": False} if _url.get_backend_name() == "sqlite" else {}

engine = create_engine(_url, connect_args=_connect_args)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with SessionLocal() as session:
        yield session


def create_tables(force: bool = False) -> None:
    """Create any missing tables. With `force`, the letters table is dropped first (users are kept)."""
    from letterdb.models import Letter

    if force:
        Base.metadata.drop_all(engine, tables=[Base.metadata.tables[Letter.__tablename__]])
    Base.metadata.create_all(engine)
