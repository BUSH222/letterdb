from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from letterdb.db import Base


class Letter(Base):
    """A letter."""

    __tablename__ = "letterdb"

    catalogue: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    date: Mapped[str | None] = mapped_column(Text)
    addressee: Mapped[str | None] = mapped_column("adressee", Text)  # column name typo is legacy
    keywords: Mapped[str | None] = mapped_column(Text)
    regions: Mapped[str | None] = mapped_column(Text)
    contents_txt: Mapped[str | None] = mapped_column(Text)
    imagelink: Mapped[str | None] = mapped_column(Text)
    comments: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class User(Base):
    """A staff user who can create, edit and delete letters."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
