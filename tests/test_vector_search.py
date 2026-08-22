import os
import shutil
import pytest
from app.infrastructure.config import VectorSearchConfig
from app.infrastructure.database.models import (
    BookModel,
    EditionModel,
    HadithModel,
    HadithTextModel,
    SectionModel,
)
from app.services.embedding_provider import BaseEmbeddingProvider
from app.services.vector_search_service import HadithVectorSearchService


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Mock Provider embedding sederhana untuk pengujian cepat."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # Return deterministic dummy 4-dimensional vector based on string length
        results = []
        for t in texts:
            val = float(len(t) % 100) / 100.0
            results.append([val, val + 0.1, val + 0.2, val + 0.3])
        return results

    def embed_query(self, query: str) -> list[float]:
        val = float(len(query) % 100) / 100.0
        return [val, val + 0.1, val + 0.2, val + 0.3]


@pytest.mark.asyncio
async def test_vector_search_build_and_query(test_session, tmp_path):
    # Setup sample database data
    book = BookModel(slug="bukhari", name="Sahih Bukhari")
    test_session.add(book)

    section = SectionModel(
        book_slug="bukhari", section_number=1.0, title="Wahyu & Niat"
    )
    test_session.add(section)
    await test_session.flush()

    edition_id = EditionModel(
        name="ind-bukhari",
        book_slug="bukhari",
        language="Indonesian",
        iso_code="ind",
        direction="ltr",
    )
    test_session.add(edition_id)
    await test_session.flush()

    hadith = HadithModel(
        book_slug="bukhari",
        hadith_number=1.0,
        arabic_number=1.0,
        section_id=section.id,
    )
    test_session.add(hadith)
    await test_session.flush()

    hadith_text = HadithTextModel(
        hadith_id=hadith.id,
        edition_name="ind-bukhari",
        text="Sesungguhnya setiap amalan tergantung pada niatnya.",
    )
    test_session.add(hadith_text)
    await test_session.commit()

    # Configure Vector Search using temporary path
    v_db_path = str(tmp_path / "test_vector_store")
    config = VectorSearchConfig(
        vector_db_path=v_db_path,
        table_name="test_hadiths",
        provider="sentence-transformers",
    )

    mock_provider = MockEmbeddingProvider()
    service = HadithVectorSearchService(config, embedding_provider=mock_provider)

    # Build Index
    count = await service.build_index(test_session, show_progress=False)
    assert count == 1

    # Query Search
    results = await service.search(query="niat amalan", limit=5)
    assert len(results) == 1
    assert results[0]["hadith_number"] == 1.0
    assert results[0]["book_slug"] == "bukhari"
    assert "niatnya" in results[0]["indonesian_text"]
    assert "score" in results[0]
