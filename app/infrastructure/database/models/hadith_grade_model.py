from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.models.base import Base


class HadithGradeModel(Base):
    __tablename__ = "hadith_grades"
    __table_args__ = (
        UniqueConstraint("hadith_id", "grader_id", name="uk_hadith_grades_hadith_grader"),
        Index("idx_hadith_grades_hadith_id", "hadith_id"),
        Index("idx_hadith_grades_grader_id", "grader_id"),
        Index("idx_hadith_grades_grade", "grade"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    hadith_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("hadiths.id", ondelete="CASCADE"),
        nullable=False,
    )
    grader_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("graders.id", ondelete="CASCADE"), nullable=False
    )
    grade: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    hadith: Mapped["HadithModel"] = relationship("HadithModel", back_populates="grades")
    grader: Mapped["GraderModel"] = relationship("GraderModel", back_populates="grades")
