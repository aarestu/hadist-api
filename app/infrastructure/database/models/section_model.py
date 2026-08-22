from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.models.base import Base


class SectionModel(Base):
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("book_slug", "section_number", name="uk_sections_book_number"),
        Index("idx_sections_book_slug", "book_slug"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    book_slug: Mapped[str] = mapped_column(
        String(50), ForeignKey("books.slug", ondelete="CASCADE"), nullable=False
    )
    section_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hadithnumber_first: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    hadithnumber_last: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    arabicnumber_first: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    arabicnumber_last: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    book: Mapped["BookModel"] = relationship("BookModel", back_populates="sections")
    hadiths: Mapped[List["HadithModel"]] = relationship("HadithModel", back_populates="section")
