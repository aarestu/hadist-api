import argparse
import asyncio
import logging
import sys
from typing import Optional

from app.infrastructure.config import load_config
from app.infrastructure.database import get_engine, get_session_maker, init_db
from app.services.vector_search_service import HadithVectorSearchService

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("HadithVectorCLI")


def display_vector_search_results(query: str, results: list):
    """Menampilkan hasil pencarian semantik dengan format konsol yang intuitif."""
    print("\n" + "=" * 75)
    print(f"🔍 HASIL PENCARIAN SEMANTIK (VECTOR SEARCH)")
    print(f"📌 KUERI: \"{query}\"")
    print("=" * 75)

    if not results:
        print("\n❌ Tidak ditemukan hadis yang relevan secara semantik.")
        return

    for idx, r in enumerate(results, start=1):
        print(f"\n[{idx}] 📖 Kitab: {r['book_name']} ({r['book_slug']}) | Hadis No: #{r['hadith_number']}")
        print(f"    ⭐ Skor Relevansi : {r['score'] * 100:.1f}% (Distance: {r['distance']})")
        if r['section_title']:
            print(f"    📑 Bab            : {r['section_title']}")

        if r['indonesian_text']:
            snippet = r['indonesian_text'][:250] + ("..." if len(r['indonesian_text']) > 250 else "")
            print(f"    🇮🇩 Terjemahan (ID): \"{snippet}\"")
        elif r['english_text']:
            snippet = r['english_text'][:250] + ("..." if len(r['english_text']) > 250 else "")
            print(f"    🇬🇧 Terjemahan (EN): \"{snippet}\"")

        if r['arabic_text']:
            snippet = r['arabic_text'][:150] + ("..." if len(r['arabic_text']) > 150 else "")
            print(f"    🇦🇪 Teks Arab    : \"{snippet}\"")

        print("-" * 75)
    print()


def create_vector_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI Hadith Vector Search (Semantic Search) & Index Building"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: build-index
    build_parser = subparsers.add_parser(
        "build-index", help="Menjalankan pemrosesan vektor + pembuatan index LanceDB secara otomatis"
    )
    build_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path file konfigurasi YAML (default: config.yaml)",
    )
    build_parser.add_argument(
        "--batch-size",
        type=int,
        default=250,
        help="Ukuran batch untuk pemrosesan embedding (default: 250)",
    )
    build_parser.add_argument(
        "--reset",
        action="store_true",
        help="Hapus vektor lama dan buat ulang dari awal",
    )

    # Subcommand: build-vectors
    vectors_parser = subparsers.add_parser(
        "build-vectors", help="TAHAP 1: Menghasilkan vector embeddings secara incremental (Checkpointed / dapat di-resume)"
    )
    vectors_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path file konfigurasi YAML (default: config.yaml)",
    )
    vectors_parser.add_argument(
        "--batch-size",
        type=int,
        default=250,
        help="Ukuran batch untuk pemrosesan embedding (default: 250)",
    )
    vectors_parser.add_argument(
        "--reset",
        action="store_true",
        help="Hapus vektor lama dan buat ulang dari awal",
    )

    # Subcommand: create-index
    idx_parser = subparsers.add_parser(
        "create-index", help="TAHAP 2: Membuat struktur index pencarian cepat (IVF-PQ Index) dari data vektor LanceDB"
    )
    idx_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path file konfigurasi YAML (default: config.yaml)",
    )

    # Subcommand: search
    search_parser = subparsers.add_parser(
        "search", help="Mencari hadis relevan secara konteks semantik"
    )
    search_parser.add_argument(
        "-q",
        "--query",
        type=str,
        required=True,
        help="Kueri atau konsep yang ingin dicari (contoh: 'memuliakan tetangga')",
    )
    search_parser.add_argument(
        "-b",
        "--book",
        type=str,
        default=None,
        help="Opsional: Filter slug kitab (contoh: bukhari, muslim)",
    )
    search_parser.add_argument(
        "-k",
        "--limit",
        type=int,
        default=5,
        help="Jumlah hasil pencarian terbanyak yang ditampilkan (default: 5)",
    )
    search_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path file konfigurasi YAML (default: config.yaml)",
    )

    # Subcommand: benchmark-batch
    benchmark_parser = subparsers.add_parser(
        "benchmark-batch", help="Menguji dan mencari batch size embedding terbaik untuk hardware"
    )
    benchmark_parser.add_argument(
        "-s",
        "--samples",
        type=int,
        default=500,
        help="Jumlah sampel dokumen hadis yang diuji (default: 500)",
    )
    benchmark_parser.add_argument(
        "-b",
        "--batch-sizes",
        type=int,
        nargs="+",
        default=[16, 32, 64, 128, 256, 512, 1024],
        help="Daftar batch size yang ingin diuji (default: 16 32 64 128 256 512 1024)",
    )
    benchmark_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path file konfigurasi YAML (default: config.yaml)",
    )

    return parser


async def run_vector_cli():
    parser = create_vector_cli_parser()
    args = parser.parse_args()
    config = load_config(args.config)

    if args.command in ["build-index", "build-vectors"]:
        logger.info("Membuka koneksi database relasional...")
        engine = get_engine(config.database_url)
        await init_db(engine)
        session_maker = get_session_maker(engine)

        async with session_maker() as session:
            vector_service = HadithVectorSearchService(config.vector_search)
            if args.command == "build-vectors":
                count = await vector_service.generate_vectors(
                    session, batch_size=args.batch_size, reset=args.reset
                )
                logger.info(f"Berhasil membuat/melanjutkan {count} vektor hadis di LanceDB.")
            else:
                count = await vector_service.build_index(
                    session, batch_size=args.batch_size, reset=args.reset
                )
                logger.info(f"Berhasil membuat {count} vektor dan index LanceDB.")

    elif args.command == "create-index":
        vector_service = HadithVectorSearchService(config.vector_search)
        success = vector_service.create_vector_index()
        if success:
            logger.info("Vector Index (Tahap 2) berhasil dibuat/diperbarui.")

    elif args.command == "search":
        vector_service = HadithVectorSearchService(config.vector_search)
        results = await vector_service.search(
            query=args.query,
            limit=args.limit,
            book_slug=args.book,
        )
        display_vector_search_results(args.query, results)

    elif args.command == "benchmark-batch":
        import torch
        from app.cli.benchmark_batch import display_benchmark_results
        from app.services.batch_benchmark_service import BatchBenchmarkService

        engine = get_engine(config.database_url)
        await init_db(engine)
        session_maker = get_session_maker(engine)

        benchmark_service = BatchBenchmarkService(config.vector_search)

        async with session_maker() as session:
            sample_texts = await benchmark_service.get_sample_texts(
                session=session, count=args.samples
            )

        device_name = (
            f"CUDA ({torch.cuda.get_device_name(0)})"
            if torch.cuda.is_available()
            else "CPU"
        )

        results = benchmark_service.run_benchmark(
            sample_texts=sample_texts, batch_sizes=args.batch_sizes
        )

        display_benchmark_results(
            model_name=config.vector_search.model_name,
            device_name=device_name,
            sample_count=len(sample_texts),
            results=results,
        )


def main():
    try:
        asyncio.run(run_vector_cli())
    except KeyboardInterrupt:
        logger.info("\nProses dibatalkan oleh pengguna.")


if __name__ == "__main__":
    main()
