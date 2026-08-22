import pytest
from sqlalchemy import select

from app.infrastructure.database.models import BookModel, EditionModel, GraderModel, HadithModel, SectionModel
from app.services.importer_service import HadithImporterService


@pytest.mark.asyncio
async def test_import_books_and_editions(test_session, mock_editions_data):
    service = HadithImporterService(test_session)
    allowed_langs = {"Indonesian"}
    allowed_eds = set()

    target_editions = await service.import_books_and_editions(
        mock_editions_data, allowed_langs, allowed_eds
    )

    assert len(target_editions) == 1
    assert target_editions[0]["name"] == "ind-bukhari"

    # Verify Book in DB
    book_res = await test_session.execute(select(BookModel).where(BookModel.slug == "bukhari"))
    book = book_res.scalar_one_or_none()
    assert book is not None
    assert book.name == "Sahih al Bukhari"

    # Verify Edition in DB
    ed_res = await test_session.execute(select(EditionModel).where(EditionModel.name == "ind-bukhari"))
    ed = ed_res.scalar_one_or_none()
    assert ed is not None
    assert ed.language == "Indonesian"


@pytest.mark.asyncio
async def test_import_sections(test_session, mock_editions_data, mock_info_data):
    service = HadithImporterService(test_session)
    await service.import_books_and_editions(mock_editions_data, set(), set())
    await service.import_sections(mock_info_data)

    sec_res = await test_session.execute(
        select(SectionModel).where(SectionModel.book_slug == "bukhari", SectionModel.section_number == 1)
    )
    section = sec_res.scalar_one_or_none()
    assert section is not None
    assert section.title == "Revelation"
    assert float(section.hadithnumber_first) == 1.0


@pytest.mark.asyncio
async def test_import_edition_hadiths(test_session, mock_editions_data, mock_info_data, mock_edition_content):
    service = HadithImporterService(test_session)
    await service.import_books_and_editions(mock_editions_data, set(), set())
    await service.import_sections(mock_info_data)

    await service.import_edition_hadiths("ind-bukhari", "bukhari", mock_edition_content)

    hadith_res = await test_session.execute(
        select(HadithModel).where(HadithModel.book_slug == "bukhari", HadithModel.hadith_number == 1)
    )
    hadith = hadith_res.scalar_one_or_none()
    assert hadith is not None
    assert float(hadith.hadith_number) == 1.0

    # Verify Grader created
    grader_res = await test_session.execute(select(GraderModel).where(GraderModel.name == "Al-Albani"))
    grader = grader_res.scalar_one_or_none()
    assert grader is not None
    assert grader.name == "Al-Albani"
