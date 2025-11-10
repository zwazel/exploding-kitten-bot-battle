"""Database models for the arena backend."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    bot: Mapped[Optional["Bot"]] = relationship("Bot", back_populates="owner", uselist=False)


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    current_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bot_versions.id", ondelete="SET NULL", use_alter=True), nullable=True
    )

    owner: Mapped[User] = relationship("User", back_populates="bot")
    versions: Mapped[list["BotVersion"]] = relationship(
        "BotVersion",
        back_populates="bot",
        order_by="BotVersion.version_number",
        foreign_keys="BotVersion.bot_id",
    )
    current_version: Mapped[Optional["BotVersion"]] = relationship(
        "BotVersion", foreign_keys=[current_version_id], post_update=True
    )


class BotVersion(Base):
    __tablename__ = "bot_versions"
    __table_args__ = (
        UniqueConstraint("bot_id", "version_number", name="uq_bot_version_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    bot: Mapped[Bot] = relationship("Bot", back_populates="versions", foreign_keys=[bot_id])
    replay_entries: Mapped[list["ReplayParticipant"]] = relationship(
        "ReplayParticipant", back_populates="bot_version"
    )

    @property
    def resolved_path(self) -> Optional[Path]:
        return Path(self.file_path) if self.file_path else None


class Replay(Base):
    __tablename__ = "replays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    winner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    participants: Mapped[list["ReplayParticipant"]] = relationship(
        "ReplayParticipant", back_populates="replay", cascade="all, delete-orphan"
    )


class ReplayParticipant(Base):
    __tablename__ = "replay_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    replay_id: Mapped[int] = mapped_column(ForeignKey("replays.id", ondelete="CASCADE"))
    bot_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bot_versions.id", ondelete="SET NULL", use_alter=True), nullable=True
    )
    bot_label: Mapped[str] = mapped_column(String(255), nullable=False)
    placement: Mapped[int] = mapped_column(Integer, nullable=False)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    replay: Mapped[Replay] = relationship("Replay", back_populates="participants")
    bot_version: Mapped[Optional[BotVersion]] = relationship(
        "BotVersion", back_populates="replay_entries"
    )


__all__ = [
    "Base",
    "User",
    "Bot",
    "BotVersion",
    "Replay",
    "ReplayParticipant",
]
