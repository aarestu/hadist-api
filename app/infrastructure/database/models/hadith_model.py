from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.models.base import Base


class HadithModel(Base):
    __tablename__ = "hadiths"
    __table_args__ = (
        UniqueConstraint("book_slug", "hadith_number", name="uk_hadiths_book_number"),
        Index("idx_hadiths_book_slug", "book_slug"),
        Index("idx_hadiths_section_id", "section_id"),
        Index("idx_hadiths_number", "hadith_number"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    book_slug: Mapped[str] = mapped_column(
        String(50), ForeignKey("books.slug", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[Optional[int]] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    hadith_number: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    arabic_number: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    reference_book: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_hadith: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    book: Mapped["BookModel"] = relationship("BookModel", back_populates="hadiths")
    section: Mapped[Optional["SectionModel"]] = relationship("SectionModel", back_populates="hadiths")
    texts: Mapped[List["HadithTextModel"]] = relationship(
        "HadithTextModel", back_populates="hadith", cascade="all, delete-orphan"
    )
    grades: Mapped[List["HadithGradeModel"]] = relationship(
        "HadithGradeModel", back_populates="hadith", cascade="all, delete-orphan"
    )
