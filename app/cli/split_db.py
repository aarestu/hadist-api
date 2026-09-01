import argparse
import logging
import sys
from app.services.db_splitter_service import DEFAULT_LANGUAGE_MAPPINGS, HadithDbSplitterService

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("DbSplitter")


def create_split_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Alat Split Database Hadist ke Database Terpisah Per-Bahasa (untuk CDN / Distribusi Publik)"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="hadist.db",
        help="Jalur file SQLite master hadist (default: hadist.db)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Direktori penyimpanan file SQLite per bahasa (default: data/)",
    )
    parser.add_argument(
        "--gzip",
        action="store_true",
        default=True,
        help="Kompresi output database ke .gz untuk batas 20MB jsDelivr CDN (default: True)",
    )
    parser.add_argument(
        "--no-gzip",
        dest="gzip",
        action="store_false",
        help="Jangan membuat file kompresi .gz",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default=None,
        help="Filter hanya bahasa tertentu (misal: id, eng, ar). Jika kosong, semua bahasa akan diekspor.",
    )
    return parser


def main():
    parser = create_split_parser()
    args = parser.parse_args()

    splitter = HadithDbSplitterService(
        source_db_path=args.source,
        output_dir=args.output_dir,
    )

    alias_map = {
        "id": "id",
        "ind": "id",
        "indonesian": "id",
        "en": "en",
        "eng": "en",
        "english": "en",
        "ar": "ar",
        "ara": "ar",
        "arabic": "ar",
    }

    mappings = DEFAULT_LANGUAGE_MAPPINGS
    if args.lang:
        lang_key = args.lang.lower().strip()
        normalized_key = alias_map.get(lang_key)
        if normalized_key and normalized_key in DEFAULT_LANGUAGE_MAPPINGS:
            mappings = {normalized_key: DEFAULT_LANGUAGE_MAPPINGS[normalized_key]}
        else:
            logger.error(
                f"Bahasa '{args.lang}' tidak dikenal. Pilihan yang tersedia: {list(DEFAULT_LANGUAGE_MAPPINGS.keys())}"
            )
            sys.exit(1)

    logger.info(f"Memulai pemisahan database dari: {args.source}")
    logger.info(f"Target direktori: {args.output_dir}")

    results = splitter.split_all(custom_mappings=mappings, create_gzip=args.gzip)

    print("\n" + "=" * 80)
    print(f"{'RINGKASAN DATABASE PER BAHASA':^80}")
    print("=" * 80)
    print(
        f"{'File':<20} | {'Bahasa':<12} | {'Hadis':<8} | {'Teks':<8} | {'Ukuran (DB)':<12} | {'Ukuran (GZ)':<12}"
    )
    print("-" * 80)
    for r in results:
        gz_info = f"{r.get('gzip_size_mb', 0):.2f} MB" if args.gzip else "N/A"
        print(
            f"{r['filename']:<20} | {r['language']:<12} | {r['hadiths']:<8} | {r['texts']:<8} | {r['size_mb']:>7.2f} MB   | {gz_info:>10}"
        )
    print("=" * 80 + "\n")
    logger.info("Proses pemisahan database selesai dengan sukses!")


if __name__ == "__main__":
    main()
