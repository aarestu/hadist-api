import logging
import time
from typing import Any, Dict, List, Optional
import torch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.config import VectorSearchConfig
from app.infrastructure.database.models import HadithModel, HadithTextModel
from app.services.embedding_provider import get_embedding_provider

logger = logging.getLogger(__name__)


class BatchBenchmarkService:
    """Service layer to benchmark optimal embedding batch size for CPU/GPU hardware."""

    def __init__(self, config: VectorSearchConfig):
        self.config = config

    async def get_sample_texts(
        self, session: Optional[AsyncSession] = None, count: int = 500
    ) -> List[str]:
        """Mengambil sampel teks hadis dari database relasional atau sampel sintesis."""
        texts = []
        if session:
            stmt = select(HadithModel).options(
                selectinload(HadithModel.book),
                selectinload(HadithModel.section),
                selectinload(HadithModel.texts).selectinload(HadithTextModel.edition),
            ).limit(count)

            result = await session.execute(stmt)
            hadiths = result.scalars().all()

            for h in hadiths:
                book_name = h.book.name if h.book else h.book_slug
                sec_title = h.section.title if h.section else ""
                ind_text = next((t.text for t in h.texts if t.edition and "ind" in t.edition.language.lower()), "")
                eng_text = next((t.text for t in h.texts if t.edition and "eng" in t.edition.language.lower()), "")

                doc = f"Kitab: {book_name}\nBab: {sec_title}\nTeks ID: {ind_text}\nTeks EN: {eng_text}"
                texts.append(doc)

        if not texts:
            # Synthetic sample fallback if database is empty
            base_sample = (
                "Kitab: Sahih Bukhari\nBab: Niat dan Keikhlasan\n"
                "Teks ID: Telah menceritakan kepada kami Umar bin Al-Khattab bahwa Rasulullah SAW bersabda: "
                "Semua amalan tergantung pada niatnya dan setiap orang mendapatkan apa yang ia niatkan.\n"
                "Teks EN: Actions are judged by intentions and every person will get what he intended."
            )
            texts = [f"{base_sample} #{i}" for i in range(count)]

        return texts

    def run_benchmark(
        self,
        sample_texts: List[str],
        batch_sizes: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Menjalankan benchmark untuk berbagai variasi batch size."""
        if not batch_sizes:
            batch_sizes = [16, 32, 64, 128, 256, 512, 1024]

        provider = get_embedding_provider(self.config)
        is_cuda = torch.cuda.is_available()

        results = []

        # Warmup model inference
        provider.embed_texts(sample_texts[:min(8, len(sample_texts))])

        for b_size in batch_sizes:
            if is_cuda:
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()

            total_count = len(sample_texts)
            start_time = time.perf_counter()
            oom_occurred = False

            try:
                for i in range(0, total_count, b_size):
                    batch = sample_texts[i : i + b_size]
                    provider.embed_texts(batch)

                elapsed = time.perf_counter() - start_time
                items_per_sec = total_count / elapsed if elapsed > 0 else 0.0

                peak_vram_mb = 0.0
                if is_cuda:
                    peak_vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)

                results.append(
                    {
                        "batch_size": b_size,
                        "time_seconds": round(elapsed, 3),
                        "items_per_sec": round(items_per_sec, 2),
                        "peak_vram_mb": round(peak_vram_mb, 1),
                        "status": "Success",
                    }
                )
            except torch.cuda.OutOfMemoryError:
                if is_cuda:
                    torch.cuda.empty_cache()
                results.append(
                    {
                        "batch_size": b_size,
                        "time_seconds": 0.0,
                        "items_per_sec": 0.0,
                        "peak_vram_mb": 0.0,
                        "status": "OOM (Out of Memory)",
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "batch_size": b_size,
                        "time_seconds": 0.0,
                        "items_per_sec": 0.0,
                        "peak_vram_mb": 0.0,
                        "status": f"Error: {str(e)[:40]}",
                    }
                )

        return results
