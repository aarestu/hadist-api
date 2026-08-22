from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.models.base import Base


class EditionModel(Base):
    __tablename__ = "editions"
    __table_args__ = (
        Index("idx_editions_book_slug", "book_slug"),
        Index("idx_editions_iso_code", "iso_code"),
    )

    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    book_slug: Mapped[str] = mapped_column(
        String(50), ForeignKey("books.slug", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    iso_code: Mapped[str] = mapped_column(String(10), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False, default="Unknown")
    direction: Mapped[str] = mapped_column(String(3), nullable=False, default="ltr")
    has_sections: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkmin: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    book: Mapped["BookModel"] = relationship("BookModel", back_populates="editions")
    texts: Mapped[List["HadithTextModel"]] = relationship(
        "HadithTextModel", back_populates="edition", cascade="all, delete-orphan"
    )
