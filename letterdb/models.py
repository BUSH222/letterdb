from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from letterdb.db import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("keyword", Text, unique=True)


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("region", Text, unique=True)


class LetterKeyword(Base):
    """Links a letter to one of its keywords; `position` keeps the order they were entered in."""

    __tablename__ = "letter_keywords"

    letter_catalogue: Mapped[int] = mapped_column(
        ForeignKey("letterdb.catalogue", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )
    term_id: Mapped[int] = mapped_column("keyword_id", ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    term: Mapped[Keyword] = relationship(lazy="joined")


class LetterRegion(Base):
    """Links a letter to one of its regions; `position` keeps the order they were entered in."""

    __tablename__ = "letter_regions"

    letter_catalogue: Mapped[int] = mapped_column(
        ForeignKey("letterdb.catalogue", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )
    term_id: Mapped[int] = mapped_column("region_id", ForeignKey("regions.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    term: Mapped[Region] = relationship(lazy="joined")


class Letter(Base):
    """A letter."""

    __tablename__ = "letterdb"

    catalogue: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    date: Mapped[str | None] = mapped_column(Text)
    addressee: Mapped[str | None] = mapped_column("adressee", Text)  # column name typo is legacy
    contents_txt: Mapped[str | None] = mapped_column(Text)
    imagelink: Mapped[str | None] = mapped_column(Text)
    comments: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    keyword_links: Mapped[list[LetterKeyword]] = relationship(
        order_by=LetterKeyword.position, cascade="all, delete-orphan", lazy="selectin"
    )
    region_links: Mapped[list[LetterRegion]] = relationship(
        order_by=LetterRegion.position, cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def keywords(self) -> list[str]:
        return [link.term.name for link in self.keyword_links]

    @property
    def regions(self) -> list[str]:
        return [link.term.name for link in self.region_links]


class User(Base):
    """A staff user who can create, edit and delete letters."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
