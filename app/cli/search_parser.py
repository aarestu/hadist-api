import argparse


def create_search_cli_parser() -> argparse.ArgumentParser:
    """Factory creating CLI argument parser for searching Hadith by canonical number or Arabic number."""
    parser = argparse.ArgumentParser(
        description="CLI Pencarian Hadis Berdasarkan Nomor Digital Kanonikal / Nomor Arab & Kitab"
    )
    parser.add_argument(
        "-b",
        "--book",
        type=str,
        default=None,
        help="Slug kitab hadis (contoh: bukhari, muslim, abudawud, tirmidhi, nasai, ibnmajah)",
    )
    parser.add_argument(
        "-s",
        "--semantic",
        type=str,
        default=None,
        help="Pencarian semantik / vector search berdasarkan makna konteks (contoh: 'memuliakan tetangga')",
    )
    parser.add_argument(
        "-n",
        "--number",
        type=float,
        default=None,
        help="Nomor kanonikal digital hadis yang ingin dicari (contoh: 1 atau 1035)",
    )
    parser.add_argument(
        "-a",
        "--arabic-number",
        type=float,
        default=None,
        help="Nomor cetakan Arab hadis yang ingin dicari (contoh: 1035)",
    )
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        nargs="+",
        default=None,
        help="Opsional: Filter satu atau beberapa bahasa terjemahan (contoh: -l Indonesian English)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Jalur file konfigurasi YAML (default: config.yaml)",
    )
    return parser
