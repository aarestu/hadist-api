import pytest
from app.infrastructure.config import VectorSearchConfig
from app.services.batch_benchmark_service import BatchBenchmarkService
from tests.test_vector_search import MockEmbeddingProvider


@pytest.mark.asyncio
async def test_batch_benchmark_service(test_session, tmp_path):
    config = VectorSearchConfig(
        vector_db_path=str(tmp_path / "test_vec"),
        provider="sentence-transformers",
    )
    service = BatchBenchmarkService(config)

    # Test retrieving sample texts
    sample_texts = await service.get_sample_texts(session=test_session, count=10)
    assert len(sample_texts) == 10

    # Inject mock provider to run benchmark quickly
    mock_provider = MockEmbeddingProvider()

    # Patch get_embedding_provider in batch_benchmark_service module
    import app.services.batch_benchmark_service as bbs_mod
    original_fn = bbs_mod.get_embedding_provider
    bbs_mod.get_embedding_provider = lambda cfg: mock_provider

    try:
        results = service.run_benchmark(sample_texts, batch_sizes=[2, 5, 10])
        assert len(results) == 3
        assert results[0]["batch_size"] == 2
        assert results[0]["status"] == "Success"
    finally:
        bbs_mod.get_embedding_provider = original_fn
