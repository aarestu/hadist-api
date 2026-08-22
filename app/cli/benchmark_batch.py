import argparse
import asyncio
import logging
import sys
from typing import List, Optional
import torch

from app.infrastructure.config import load_config
from app.infrastructure.database import get_engine, get_session_maker, init_db
from app.services.batch_benchmark_service import BatchBenchmarkService

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("BatchBenchmarkCLI")


def display_benchmark_results(
    model_name: str,
    device_name: str,
    sample_count: int,
    results: List[dict],
):
    """Menampilkan hasil benchmark batch size dalam tabel konsol yang rapi."""
    print("\n" + "=" * 80)
    print("⚡ BENCHMARK EMBEDDING BATCH SIZE OPTIMIZER")
    print(f"🤖 MODEL    : {model_name}")
    print(f"💻 PERANGKAT: {device_name}")
    print(f"📊 SAMPEL   : {sample_count} dokumen hadis")
    print("=" * 80)

    print(
        f"{'BATCH SIZE':<12} | {'TOTAL WAKTU':<14} | {'KECEPATAN (docs/s)':<20} | {'PEAK VRAM (MB)':<16} | {'STATUS':<12}"
    )
    print("-" * 80)

    best_item = None
    max_throughput = -1.0

    for r in results:
        status = r["status"]
        if status == "Success":
            time_str = f"{r['time_seconds']:.3f} s"
            speed_str = f"{r['items_per_sec']:.2f} docs/s"
            vram_str = f"{r['peak_vram_mb']:.1f} MB" if r['peak_vram_mb'] > 0 else "N/A (CPU)"

            if r["items_per_sec"] > max_throughput:
                max_throughput = r["items_per_sec"]
                best_item = r
        else:
            time_str = "-"
            speed_str = "-"
            vram_str = "-"

        print(
            f"{r['batch_size']:<12} | {time_str:<14} | {speed_str:<20} | {vram_str:<16} | {status:<12}"
        )

    print("=" * 80)
    if best_item:
        print(f"\n🏆 REKOMENDASI OPTIMAL BATCH SIZE: {best_item['batch_size']}")
        print(
            f"   Kecepatan Tertinggi: {best_item['items_per_sec']:.2f} docs/s "
            f"(Total Waktu: {best_item['time_seconds']:.3f}s)"
        )
        print(
            f"   Gunakan komando: python -m app.cli.vector_cli build-index --batch-size {best_item['batch_size']}\n"
        )
    print()


def create_benchmark_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI Benchmark untuk Mencari Best Batch Size Embedding Hadis"
    )
    parser.add_argument(
        "-s",
        "--samples",
        type=int,
        default=500,
        help="Jumlah sampel dokumen hadis yang diuji (default: 500)",
    )
    parser.add_argument(
        "-b",
        "--batch-sizes",
        type=int,
        nargs="+",
        default=[16, 32, 64, 128, 256, 512, 1024],
        help="Daftar batch size yang ingin diuji (default: 16 32 64 128 256 512 1024)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Jalur file konfigurasi YAML (default: config.yaml)",
    )
    return parser


async def run_benchmark_cli():
    parser = create_benchmark_parser()
    args = parser.parse_args()
    config = load_config(args.config)

    engine = get_engine(config.database_url)
    await init_db(engine)
    session_maker = get_session_maker(engine)

    benchmark_service = BatchBenchmarkService(config.vector_search)

    logger.info("Memuat sampel data hadis dari database...")
    async with session_maker() as session:
        sample_texts = await benchmark_service.get_sample_texts(
            session=session, count=args.samples
        )

    device_name = (
        f"CUDA ({torch.cuda.get_device_name(0)})"
        if torch.cuda.is_available()
        else "CPU"
    )

    logger.info(f"Menjalankan benchmark pada {len(sample_texts)} sampel dengan GPU/CPU...")
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
        asyncio.run(run_benchmark_cli())
    except KeyboardInterrupt:
        logger.info("\nBenchmark dibatalkan oleh pengguna.")


if __name__ == "__main__":
    main()
