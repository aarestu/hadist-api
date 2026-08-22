import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.models import Base


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    async_session = sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session


@pytest.fixture
def mock_editions_data():
    return {
        "bukhari": {
            "name": "Sahih al Bukhari",
            "collection": [
                {
                    "name": "ind-bukhari",
                    "book": "bukhari",
                    "author": "Unknown",
                    "language": "Indonesian",
                    "has_sections": True,
                    "direction": "ltr",
                },
                {
                    "name": "ara-bukhari",
                    "book": "bukhari",
                    "author": "Unknown",
                    "language": "Arabic",
                    "has_sections": True,
                    "direction": "rtl",
                },
            ],
        }
    }


@pytest.fixture
def mock_info_data():
    return {
        "bukhari": {
            "metadata": {
                "name": "Sahih al Bukhari",
                "last_hadithnumber": 7563,
                "sections": {"1": "Revelation", "2": "Belief"},
                "section_detail": {
                    "1": {
                        "hadithnumber_first": 1,
                        "hadithnumber_last": 7,
                        "arabicnumber_first": 1,
                        "arabicnumber_last": 7,
                    }
                },
            }
        }
    }


@pytest.fixture
def mock_edition_content():
    return {
        "hadiths": [
            {
                "hadithnumber": 1,
                "arabicnumber": 1,
                "text": "Actions are by intentions.",
                "grades": [{"name": "Al-Albani", "grade": "Sahih"}],
                "reference": {"book": 1, "hadith": 1},
            }
        ]
    }
