from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.models.base import Base


class HadithTextModel(Base):
    __tablename__ = "hadith_texts"
    __table_args__ = (
        UniqueConstraint("hadith_id", "edition_name", name="uk_hadith_texts_hadith_edition"),
        Index("idx_hadith_texts_hadith_id", "hadith_id"),
        Index("idx_hadith_texts_edition_name", "edition_name"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    hadith_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("hadiths.id", ondelete="CASCADE"),
        nullable=False,
    )
    edition_name: Mapped[str] = mapped_column(
        String(100), ForeignKey("editions.name", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    hadith: Mapped["HadithModel"] = relationship("HadithModel", back_populates="texts")
    edition: Mapped["EditionModel"] = relationship("EditionModel", back_populates="texts")
