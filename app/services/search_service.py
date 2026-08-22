import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    BookModel,
    EditionModel,
    HadithGradeModel,
    HadithModel,
    HadithTextModel,
    SectionModel,
)

logger = logging.getLogger(__name__)


class HadithSearchService:
    """Service layer providing queries to search hadith by book slug and hadith number."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_by_number(
        self,
        book_slug: str,
        hadith_number: Optional[float] = None,
        arabic_number: Optional[float] = None,
        languages: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Mencari hadis berdasarkan slug kitab, nomor hadis kanonikal dan/atau nomor Arab, serta filter bahasa."""
        conditions = [HadithModel.book_slug == book_slug]

        if hadith_number is not None:
            conditions.append(HadithModel.hadith_number == hadith_number)

        if arabic_number is not None:
            conditions.append(HadithModel.arabic_number == arabic_number)

        stmt = (
            select(HadithModel)
            .options(
                selectinload(HadithModel.book),
                selectinload(HadithModel.section),
                selectinload(HadithModel.texts).selectinload(HadithTextModel.edition),
                selectinload(HadithModel.grades).selectinload(HadithGradeModel.grader),
            )
            .where(*conditions)
        )

        result = await self.session.execute(stmt)
        hadith = result.scalar_one_or_none()

        if not hadith:
            return None

        target_langs = (
            {l.strip().lower() for l in languages}
            if languages
            else None
        )

        # Build clean formatted result dictionary
        texts_by_edition = []
        for t in hadith.texts:
            ed_lang = t.edition.language if t.edition else "Unknown"
            if target_langs and ed_lang.lower() not in target_langs:
                continue
            texts_by_edition.append(
                {
                    "edition_name": t.edition_name,
                    "language": ed_lang,
                    "author": t.edition.author if t.edition else "Unknown",
                    "text": t.text,
                }
            )

        grades_list = [
            {"grader": g.grader.name, "grade": g.grade}
            for g in hadith.grades
            if g.grader
        ]

        return {
            "id": hadith.id,
            "book_slug": hadith.book_slug,
            "book_name": hadith.book.name if hadith.book else hadith.book_slug,
            "hadith_number": float(hadith.hadith_number),
            "arabic_number": float(hadith.arabic_number) if hadith.arabic_number is not None else None,
            "section": {
                "number": hadith.section.section_number,
                "title": hadith.section.title,
            }
            if hadith.section
            else None,
            "reference": {
                "book": hadith.reference_book,
                "hadith": hadith.reference_hadith,
            },
            "texts": texts_by_edition,
            "grades": grades_list,
        }
