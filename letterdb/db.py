from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from letterdb.config import DATABASE_URL

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
    """Create any missing tables. With `force`, the letter tables are dropped first (users are kept)."""
    from letterdb.models import User

    if force:
        Base.metadata.drop_all(engine, tables=[t for t in Base.metadata.sorted_tables if t.name != User.__tablename__])
    Base.metadata.create_all(engine)
