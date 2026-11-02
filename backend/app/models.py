from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    api_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sentences: Mapped[list["Sentence"]] = relationship(back_populates="user")


class ErrorType(Base):
    __tablename__ = "error_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Sentence(Base):
    __tablename__ = "sentences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    original_text: Mapped[str] = mapped_column(Text)
    corrected_text: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20))  # "hook" / "skill"
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped[User] = relationship(back_populates="sentences")
    errors: Mapped[list["SentenceError"]] = relationship(
        back_populates="sentence", cascade="all, delete-orphan", lazy="selectin"
    )


class SentenceError(Base):
    __tablename__ = "sentence_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    sentence_id: Mapped[int] = mapped_column(ForeignKey("sentences.id", ondelete="CASCADE"), index=True)
    error_type_id: Mapped[int] = mapped_column(ForeignKey("error_types.id"), index=True)
    error_snippet: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str] = mapped_column(Text)

    sentence: Mapped[Sentence] = relationship(back_populates="errors")
    error_type: Mapped[ErrorType] = relationship(lazy="joined")
