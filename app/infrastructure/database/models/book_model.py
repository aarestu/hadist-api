from datetime import datetime, timezone
from typing import List
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.models.base import Base


class BookModel(Base):
    __tablename__ = "books"

    slug: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_hadiths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    sections: Mapped[List["SectionModel"]] = relationship(
        "SectionModel", back_populates="book", cascade="all, delete-orphan"
    )
    editions: Mapped[List["EditionModel"]] = relationship(
        "EditionModel", back_populates="book", cascade="all, delete-orphan"
    )
    hadiths: Mapped[List["HadithModel"]] = relationship(
        "HadithModel", back_populates="book", cascade="all, delete-orphan"
    )
