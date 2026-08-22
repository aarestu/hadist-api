import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.infrastructure.database.models import Base

logger = logging.getLogger(__name__)


def get_engine(database_url: str):
    if database_url.startswith("sqlite://"):
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    return create_async_engine(database_url, echo=False, future=True)


async def init_db(engine):
    logger.info("Memulai inisialisasi tabel database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tabel database berhasil diinisialisasi.")


async def drop_db(engine):
    logger.warning("Menghapus seluruh tabel dan data di database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Seluruh tabel database berhasil dihapus.")


async def reset_db(engine):
    await drop_db(engine)
    await init_db(engine)


def get_session_maker(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
