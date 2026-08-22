import argparse


def create_cli_parser() -> argparse.ArgumentParser:
    """Factory creating CLI argument parser with single responsibility."""
    parser = argparse.ArgumentParser(
        description="Aplikasi Importer Data Hadith API ke Database Relasional"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Hapus dan buat ulang seluruh tabel database sebelum memulai proses impor.",
    )
    parser.add_argument(
        "--reset-only",
        action="store_true",
        help="Hapus dan buat ulang seluruh tabel database saja, lalu keluar tanpa melakukan impor.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Jalur file konfigurasi YAML (default: config.yaml)",
    )
    return parser
