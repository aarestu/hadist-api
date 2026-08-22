import pytest
from app.cli.search_parser import create_search_cli_parser
from app.services.importer_service import HadithImporterService
from app.services.search_service import HadithSearchService


def test_search_cli_parser():
    parser = create_search_cli_parser()
    args = parser.parse_args(["-b", "bukhari", "-n", "1035", "-a", "1035", "-l", "Indonesian", "English"])
    assert args.book == "bukhari"
    assert args.number == 1035.0
    assert args.arabic_number == 1035.0
    assert args.lang == ["Indonesian", "English"]


@pytest.mark.asyncio
async def test_search_service_found(
    test_session, mock_editions_data, mock_info_data, mock_edition_content
):
    importer = HadithImporterService(test_session)
    await importer.import_books_and_editions(mock_editions_data, set(), set())
    await importer.import_sections(mock_info_data)
    await importer.import_edition_hadiths("ind-bukhari", "bukhari", mock_edition_content)

    search_service = HadithSearchService(test_session)
    result = await search_service.search_by_number("bukhari", 1.0)

    assert result is not None
    assert result["book_slug"] == "bukhari"
    assert result["hadith_number"] == 1.0
    assert len(result["texts"]) == 1
    assert result["texts"][0]["edition_name"] == "ind-bukhari"
    assert len(result["grades"]) == 1
    assert result["grades"][0]["grader"] == "Al-Albani"


@pytest.mark.asyncio
async def test_search_service_by_arabic_number(
    test_session, mock_editions_data, mock_info_data, mock_edition_content
):
    importer = HadithImporterService(test_session)
    await importer.import_books_and_editions(mock_editions_data, set(), set())
    await importer.import_sections(mock_info_data)
    await importer.import_edition_hadiths("ind-bukhari", "bukhari", mock_edition_content)

    search_service = HadithSearchService(test_session)
    result = await search_service.search_by_number("bukhari", arabic_number=1.0)

    assert result is not None
    assert result["book_slug"] == "bukhari"
    assert result["arabic_number"] == 1.0
