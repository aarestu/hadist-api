import logging
from typing import Any, Dict, List, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import (
    BookModel,
    EditionModel,
    GraderModel,
    HadithGradeModel,
    HadithModel,
    HadithTextModel,
    SectionModel,
)

logger = logging.getLogger(__name__)


class HadithImporterService:
    """Service layer orchestrating domain import business logic into database repository."""

    def __init__(self, session: AsyncSession, batch_size: int = 500):
        self.session = session
        self.batch_size = batch_size
        self._grader_cache: Dict[str, int] = {}

    async def initialize_graders_cache(self):
        result = await self.session.execute(select(GraderModel.name, GraderModel.id))
        self._grader_cache = {name: gid for name, gid in result.all()}

    async def get_or_create_grader_id(self, grader_name: str) -> int:
        grader_name_clean = grader_name.strip()
        if grader_name_clean in self._grader_cache:
            return self._grader_cache[grader_name_clean]

        grader = GraderModel(name=grader_name_clean)
        self.session.add(grader)
        await self.session.flush()
        self._grader_cache[grader_name_clean] = grader.id
        return grader.id

    async def import_books_and_editions(
        self,
        editions_data: Dict[str, Any],
        allowed_languages: Set[str],
        allowed_editions: Set[str],
    ) -> List[Dict[str, Any]]:
        target_editions = []

        for book_slug, book_info in editions_data.items():
            book_name = book_info.get("name", book_slug)

            existing_book = await self.session.get(BookModel, book_slug)
            if not existing_book:
                book = BookModel(slug=book_slug, name=book_name)
                self.session.add(book)
            else:
                existing_book.name = book_name

            collections = book_info.get("collection", [])
            for item in collections:
                ed_name = item.get("name")
                language = item.get("language", "Unknown")
                iso_code = ed_name.split("-")[0] if "-" in ed_name else "unk"

                if allowed_editions and ed_name not in allowed_editions:
                    continue
                if allowed_languages and language not in allowed_languages:
                    continue

                target_editions.append(item)

                existing_edition = await self.session.get(EditionModel, ed_name)
                if not existing_edition:
                    edition = EditionModel(
                        name=ed_name,
                        book_slug=book_slug,
                        language=language,
                        iso_code=iso_code,
                        author=item.get("author", "Unknown"),
                        direction=item.get("direction", "ltr"),
                        has_sections=item.get("has_sections", True),
                        source=item.get("source"),
                        comments=item.get("comments"),
                        link=item.get("link"),
                        linkmin=item.get("linkmin"),
                    )
                    self.session.add(edition)

        await self.session.commit()
        logger.info(f"Berhasil mengimpor/memperbarui metadata {len(target_editions)} edisi.")
        return target_editions

    async def import_sections(self, info_data: Dict[str, Any]):
        if not info_data:
            return

        for book_slug, book_meta in info_data.items():
            metadata = book_meta.get("metadata", {})
            last_hadithno = metadata.get("last_hadithnumber")

            book = await self.session.get(BookModel, book_slug)
            if book and last_hadithno:
                book.total_hadiths = int(last_hadithno)

            sections = metadata.get("sections", {})
            section_details = metadata.get("section_detail", {})

            for sec_num_str, title in sections.items():
                try:
                    sec_num = int(sec_num_str)
                except ValueError:
                    continue

                detail = section_details.get(sec_num_str, {})

                stmt = select(SectionModel).where(
                    SectionModel.book_slug == book_slug, SectionModel.section_number == sec_num
                )
                res = await self.session.execute(stmt)
                existing_sec = res.scalar_one_or_none()

                if not existing_sec:
                    sec = SectionModel(
                        book_slug=book_slug,
                        section_number=sec_num,
                        title=str(title),
                        hadithnumber_first=detail.get("hadithnumber_first"),
                        hadithnumber_last=detail.get("hadithnumber_last"),
                        arabicnumber_first=detail.get("arabicnumber_first"),
                        arabicnumber_last=detail.get("arabicnumber_last"),
                    )
                    self.session.add(sec)
                else:
                    existing_sec.title = str(title)
                    existing_sec.hadithnumber_first = detail.get("hadithnumber_first")
                    existing_sec.hadithnumber_last = detail.get("hadithnumber_last")

        await self.session.commit()
        logger.info("Berhasil mengimpor metadata sections dari info.json.")

    async def import_edition_hadiths(
        self, edition_name: str, book_slug: str, edition_data: Dict[str, Any]
    ):
        hadiths_list = edition_data.get("hadiths", [])
        if not hadiths_list:
            return

        await self.initialize_graders_cache()

        sec_stmt = select(SectionModel).where(SectionModel.book_slug == book_slug)
        sec_res = await self.session.execute(sec_stmt)
        sections_map = {s.section_number: s.id for s in sec_res.scalars().all()}

        had_stmt = select(HadithModel.hadith_number, HadithModel.id).where(
            HadithModel.book_slug == book_slug
        )
        had_res = await self.session.execute(had_stmt)
        hadiths_map = {float(hno): hid for hno, hid in had_res.all()}

        for h_item in hadiths_list:
            h_no = h_item.get("hadithnumber")
            if h_no is None:
                continue

            h_no_float = float(h_no)
            arabic_no = h_item.get("arabicnumber")
            ref = h_item.get("reference", {}) or {}
            ref_book = ref.get("book")
            ref_hadith = ref.get("hadith")

            section_id = sections_map.get(ref_book) if ref_book is not None else None

            hadith_id = hadiths_map.get(h_no_float)
            if not hadith_id:
                new_hadith = HadithModel(
                    book_slug=book_slug,
                    section_id=section_id,
                    hadith_number=h_no_float,
                    arabic_number=float(arabic_no) if arabic_no is not None else None,
                    reference_book=ref_book,
                    reference_hadith=ref_hadith,
                )
                self.session.add(new_hadith)
                await self.session.flush()
                hadith_id = new_hadith.id
                hadiths_map[h_no_float] = hadith_id

            text_content = h_item.get("text", "")
            if text_content:
                text_stmt = select(HadithTextModel).where(
                    HadithTextModel.hadith_id == hadith_id,
                    HadithTextModel.edition_name == edition_name,
                )
                text_res = await self.session.execute(text_stmt)
                existing_text = text_res.scalar_one_or_none()

                if not existing_text:
                    h_text = HadithTextModel(
                        hadith_id=hadith_id, edition_name=edition_name, text=text_content
                    )
                    self.session.add(h_text)

            grades = h_item.get("grades", [])
            for g in grades:
                g_name = g.get("name")
                g_val = g.get("grade")
                if g_name and g_val:
                    grader_id = await self.get_or_create_grader_id(g_name)
                    grade_stmt = select(HadithGradeModel).where(
                        HadithGradeModel.hadith_id == hadith_id,
                        HadithGradeModel.grader_id == grader_id,
                    )
                    grade_res = await self.session.execute(grade_stmt)
                    if not grade_res.scalar_one_or_none():
                        h_grade = HadithGradeModel(
                            hadith_id=hadith_id, grader_id=grader_id, grade=g_val
                        )
                        self.session.add(h_grade)

        await self.session.commit()
        logger.info(f"Selesai memproses {len(hadiths_list)} hadis untuk edisi '{edition_name}'.")
