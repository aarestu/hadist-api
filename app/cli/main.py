import asyncio
import logging
import sys
from typing import Set
import httpx
from tqdm.asyncio import tqdm

from app.cli.parser import create_cli_parser
from app.infrastructure.config import load_config
from app.infrastructure.database import (
    drop_db,
    get_engine,
    get_session_maker,
    init_db,
    reset_db,
)
from app.infrastructure.http_client import HadithApiClient
from app.services.importer_service import HadithImporterService

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("HadithImporter")


async def run_importer():
    parser = create_cli_parser()
    args = parser.parse_args()

    logger.info("=== HADITH API DATABASE IMPORTER ===")
    config = load_config(args.config)

    logger.info(f"Target Database: {config.database_url}")
    engine = get_engine(config.database_url)

    if args.reset or args.reset_only:
        await reset_db(engine)
        if args.reset_only:
            logger.info("Database telah di-reset. Keluar dari program sesuai instruksi --reset-only.")
            return
    else:
        await init_db(engine)

    session_maker = get_session_maker(engine)

    client = HadithApiClient(
        base_url=config.http.base_url,
        timeout=config.http.timeout_seconds,
        max_retries=config.http.max_retries,
        max_concurrent=config.http.max_concurrent_requests,
    )

    async with httpx.AsyncClient() as http_session:
        editions_index = await client.fetch_editions_index(http_session)
        info_index = await client.fetch_info_index(http_session)

        if not editions_index:
            logger.error("Gagal mengunduh editions.json! Proses dibatalkan.")
            return

        allowed_languages: Set[str] = set(config.editions_filter.languages or [])
        allowed_editions: Set[str] = set(config.editions_filter.specific_editions or [])

        async with session_maker() as session:
            importer = HadithImporterService(session, batch_size=config.batch_size)

            logger.info("Mengimpor data Books dan Editions ke database...")
            target_editions = await importer.import_books_and_editions(
                editions_index, allowed_languages, allowed_editions
            )

            if info_index:
                logger.info("Mengimpor metadata Sections/Bab ke database...")
                await importer.import_sections(info_index)

        logger.info(f"Jumlah edisi yang akan diunduh & diimpor: {len(target_editions)}")

        pbar = tqdm(target_editions, desc="Proses Impor Edisi", unit="edisi")
        for ed_meta in pbar:
            ed_name = ed_meta.get("name")
            book_slug = ed_meta.get("book")

            pbar.set_postfix({"edisi": ed_name})

            ed_data = await client.fetch_edition_content(http_session, ed_name)
            if not ed_data:
                logger.warning(f"Melewati edisi '{ed_name}' karena gagal mengunduh.")
                continue

            async with session_maker() as session:
                importer = HadithImporterService(session, batch_size=config.batch_size)
                await importer.import_edition_hadiths(ed_name, book_slug, ed_data)

    logger.info("SELESAI! Seluruh data hadis yang dikonfigurasi berhasil diimpor ke database.")


def main():
    try:
        asyncio.run(run_importer())
    except KeyboardInterrupt:
        logger.info("\nProses dibatalkan oleh pengguna.")


if __name__ == "__main__":
    main()
