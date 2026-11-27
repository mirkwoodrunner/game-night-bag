"""Database models. Matches the data model in CLAUDE.md."""
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, true, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class Deck(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    commander: Mapped[str | None] = mapped_column(Text)
    moxfield_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    moxfield_url: Mapped[str | None] = mapped_column(String(300))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    in_rotation: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    decklist_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    cards: Mapped[list["DeckCard"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )
    tokens: Mapped[list["DeckToken"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )


class DeckCard(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("deck.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    oracle_id: Mapped[str | None] = mapped_column(String(64))
    is_commander: Mapped[bool] = mapped_column(Boolean, default=False)

    deck: Mapped[Deck] = relationship(back_populates="cards")


class Card(db.Model):
    """Cache of Scryfall card lookups."""
    oracle_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    type_line: Mapped[str | None] = mapped_column(String(300))
    related_tokens: Mapped[list] = mapped_column(JSON, default=list)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Token(db.Model):
    oracle_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(300))
    name: Mapped[str] = mapped_column(String(200))
    type_line: Mapped[str | None] = mapped_column(String(300))
    power: Mapped[str | None] = mapped_column(String(10))
    toughness: Mapped[str | None] = mapped_column(String(10))
    colors: Mapped[list] = mapped_column(JSON, default=list)
    oracle_text: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))


class DeckToken(db.Model):
    deck_id: Mapped[int] = mapped_column(
        ForeignKey("deck.id", ondelete="CASCADE"), primary_key=True
    )
    token_oracle_id: Mapped[str] = mapped_column(ForeignKey("token.oracle_id"), primary_key=True)
    source_cards: Mapped[list] = mapped_column(JSON, default=list)
    manual: Mapped[bool] = mapped_column(Boolean, default=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    deck: Mapped[Deck] = relationship(back_populates="tokens")
    token: Mapped[Token] = relationship()


class BagSession(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, default=date.today)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class BagDeck(db.Model):
    session_id: Mapped[int] = mapped_column(
        ForeignKey("bag_session.id", ondelete="CASCADE"), primary_key=True
    )
    deck_id: Mapped[int] = mapped_column(ForeignKey("deck.id", ondelete="CASCADE"), primary_key=True)


class BagTokenPacked(db.Model):
    session_id: Mapped[int] = mapped_column(
        ForeignKey("bag_session.id", ondelete="CASCADE"), primary_key=True
    )
    token_oracle_id: Mapped[str] = mapped_column(ForeignKey("token.oracle_id"), primary_key=True)


class Game(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, default=date.today)
    # RESTRICT: a deck with games can't be deleted by accident.
    deck_id: Mapped[int] = mapped_column(ForeignKey("deck.id", ondelete="RESTRICT"), index=True)
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("bag_session.id", ondelete="SET NULL")
    )
    result: Mapped[str] = mapped_column(String(10))  # win, loss, draw
    pod_size: Mapped[int] = mapped_column(Integer)
    turn_count: Mapped[int | None] = mapped_column(Integer)
    winner_note: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
