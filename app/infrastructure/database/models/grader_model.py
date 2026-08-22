from typing import List
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.models.base import Base


class GraderModel(Base):
    __tablename__ = "graders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)

    grades: Mapped[List["HadithGradeModel"]] = relationship(
        "HadithGradeModel", back_populates="grader", cascade="all, delete-orphan"
    )
