import asyncio
import logging
import sys
from typing import Optional

from app.cli.search_parser import create_search_cli_parser
from app.infrastructure.config import load_config
from app.infrastructure.database import get_engine, get_session_maker, init_db
from app.services.search_service import HadithSearchService

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("HadithSearchCLI")


def display_hadith_result(result: dict, parse_lang: str = "Indonesian"):
    """Menampilkan hasil pencarian hadis dengan format konsol yang rapi."""
    print("\n" + "=" * 70)
    print(f"📖 KITAB       : {result['book_name']} ({result['book_slug']})")
    print(f"🔢 NOMOR HADIS : {result['hadith_number']}")
    if result["arabic_number"]:
        print(f"🔢 NOMOR ARAB  : {result['arabic_number']}")

    if result["section"]:
        sec = result["section"]
        print(f"📑 BAB / SECTION: Bab {sec['number']} - {sec['title']}")

    ref = result["reference"]
    if ref["book"] or ref["hadith"]:
        print(f"📚 REFERENSI   : Kitab {ref['book']}, Hadis #{ref['hadith']}")

    print("-" * 70)
    print("💬 TEKS & TERJEMAHAN:")
    
    target_text_for_parser = ""
    target_lang_found = ""

    if not result["texts"]:
        print("  (Tidak ada teks terjemahan yang sesuai filter)")
    else:
        for idx, t in enumerate(result["texts"], start=1):
            print(f"\n  [{idx}] Edisi: {t['edition_name']} ({t['language']}) - Penulis: {t['author']}")
            print(f"      \"{t['text']}\"")
            
            # Cari teks yang cocok dengan parse_lang
            if parse_lang.lower() in t['language'].lower():
                target_text_for_parser = t['text']
                target_lang_found = t['language']
            elif not target_text_for_parser and ("ind" in t['language'].lower() or "eng" in t['language'].lower()):
                target_text_for_parser = t['text']
                target_lang_found = t['language']

    # Integrasi Local LLM Parser (jika LLM lokal tersedia)
    if target_text_for_parser:
        from app.services.llm_parser_service import LocalLLMHadithParserService
        parser_service = LocalLLMHadithParserService()
        parsed_llm = parser_service.parse_hadith(target_text_for_parser, lang=target_lang_found or parse_lang)
        if parsed_llm:
            print("\n" + "-" * 70)
            print(f"🤖 HASIL EKSTRAKSI LOCAL LLM ({target_lang_found or parse_lang}):")
            print(f"1. Narrator : {parsed_llm['narrator']}")
            print(f"2. Narration: {parsed_llm['narration']}")
            print(f"3. Note     : {parsed_llm['note']}")

    print("\n" + "-" * 70)
    print("⚖️ DERAJAT KESHAHIHAN ULAMA:")
    if not result["grades"]:
        print("  (Belum ada data penilai derajat)")
    else:
        for g in result["grades"]:
            print(f"  • {g['grader']} : {g['grade']}")

    print("=" * 70 + "\n")


async def search_cli():
    parser = create_search_cli_parser()
    args = parser.parse_args()

    config = load_config(args.config)

    if args.semantic:
        from app.cli.vector_cli import display_vector_search_results
        from app.services.vector_search_service import HadithVectorSearchService

        vector_service = HadithVectorSearchService(config.vector_search)
        results = await vector_service.search(
            query=args.semantic,
            limit=1000,
            book_slug=args.book,
        )
        display_vector_search_results(args.semantic, results)
        return

    if not args.book:
        print("\n❌ Error: Opsi -b / --book wajib diisi untuk pencarian nomor hadis.")
        parser.print_help()
        return

    if args.number is None and args.arabic_number is None:
        print("\n❌ Error: Harap tentukan setidaknya satu opsi nomor hadis: -n / --number ATAU -a / --arabic-number (atau gunakan -s / --semantic untuk pencarian konteks)")
        parser.print_help()
        return
    engine = get_engine(config.database_url)

    await init_db(engine)
    session_maker = get_session_maker(engine)

    async with session_maker() as session:
        service = HadithSearchService(session)
        result = await service.search_by_number(
            book_slug=args.book.lower(),
            hadith_number=args.number,
            arabic_number=args.arabic_number,
            languages=args.lang,
        )

        if not result:
            target_no = f"nomor '{args.number}'" if args.number is not None else f"nomor Arab '{args.arabic_number}'"
            print(f"\n❌ Hadis tidak ditemukan untuk kitab '{args.book}' dengan {target_no}.")
            if args.lang:
                print(f"   (Catatan: Filter bahasa {args.lang} aktif)")
            return

        display_hadith_result(result, parse_lang=args.parse_lang)


def main():
    try:
        asyncio.run(search_cli())
    except KeyboardInterrupt:
        logger.info("\nPencarian dibatalkan oleh pengguna.")


if __name__ == "__main__":
    main()
