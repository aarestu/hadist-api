import logging
import os
from typing import Any, Dict, List, Optional
import lancedb
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.config import VectorSearchConfig
from app.infrastructure.database.models import (
    HadithGradeModel,
    HadithModel,
    HadithTextModel,
)
from app.services.embedding_provider import BaseEmbeddingProvider, get_embedding_provider

logger = logging.getLogger(__name__)


class HadithVectorSearchService:
    """Service layer for Hadith Vector Search using LanceDB with JSONL Staging Checkpoints."""

    def __init__(
        self,
        config: VectorSearchConfig,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.config = config
        self.db_path = config.vector_db_path
        self.table_name = config.table_name
        self._provider = embedding_provider
        self.db = lancedb.connect(self.db_path)

        os.makedirs(self.db_path, exist_ok=True)
        self.json_file_path = os.path.join(self.db_path, "embeddings.jsonl")

    @property
    def provider(self) -> BaseEmbeddingProvider:
        """Lazy load embedding provider (hanya dimuat saat dibutuhkan)."""
        if self._provider is None:
            self._provider = get_embedding_provider(self.config)
        return self._provider

    def _has_table(self) -> bool:
        if hasattr(self.db, "list_tables"):
            res = self.db.list_tables()
            if hasattr(res, "tables"):
                return self.table_name in res.tables
            return self.table_name in list(res)
        return self.table_name in self.db.table_names()

    async def generate_vectors(
        self,
        session: AsyncSession,
        batch_size: int = 250,
        show_progress: bool = True,
        max_doc_length: int = 3000,
        reset: bool = False,
    ) -> int:
        """TAHAP 1 (KALKULASI BERAT): Menghasilkan vector embeddings dan menyimpannya ke file JSONL (embeddings.jsonl)."""
        import gc
        import json
        import torch

        logger.info("=== TAHAP 1: PEMBUATAN VEKTOR EMBEDDING -> FILE JSONL (KALKULASI BERAT) ===")

        if reset and os.path.exists(self.json_file_path):
            logger.info(f"Mereset/menghapus file simpanan lama '{self.json_file_path}'...")
            os.remove(self.json_file_path)

        existing_ids = set()
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        try:
                            item = json.loads(line_str)
                            existing_ids.add(item["hadith_id"])
                        except Exception:
                            pass
            logger.info(
                f"Terdeteksi file JSONL '{self.json_file_path}'. {len(existing_ids)} hadis sudah pernah di-vectorize (Checkpointed)."
            )

        stmt = select(HadithModel).options(
            selectinload(HadithModel.book),
            selectinload(HadithModel.section),
            selectinload(HadithModel.texts).selectinload(HadithTextModel.edition),
            selectinload(HadithModel.grades).selectinload(HadithGradeModel.grader),
        )

        result = await session.execute(stmt)
        all_hadiths = result.scalars().all()

        if not all_hadiths:
            logger.warning("Tidak ada hadis di database relasional.")
            return 0

        unindexed_hadiths = [h for h in all_hadiths if h.id not in existing_ids]
        total_unindexed = len(unindexed_hadiths)

        if total_unindexed == 0:
            logger.info("Seluruh hadis (100%) sudah selesai di-vectorize ke JSONL! Tidak ada data baru.")
            return len(existing_ids)

        logger.info(
            f"Memulai kalkulasi GPU/CPU embedding untuk {total_unindexed} hadis tersisa (dari total {len(all_hadiths)} hadis)..."
        )

        processed_count = len(existing_ids)

        with open(self.json_file_path, "a", encoding="utf-8") as f_out:
            for i in range(0, total_unindexed, batch_size):
                hadith_chunk = unindexed_hadiths[i : i + batch_size]

                batch_records = []
                batch_texts = []

                for hadith in hadith_chunk:
                    book_slug = hadith.book_slug
                    book_name = hadith.book.name if hadith.book else book_slug
                    section_title = (
                        hadith.section.title if hadith.section and hadith.section.title else ""
                    )
                    section_num = (
                        float(hadith.section.section_number)
                        if hadith.section and hadith.section.section_number is not None
                        else 0.0
                    )

                    ind_text = ""
                    eng_text = ""
                    ara_text = ""

                    for t in hadith.texts:
                        lang = (
                            t.edition.language.lower()
                            if t.edition and t.edition.language
                            else ""
                        )
                        if "ind" in lang or "indonesian" in lang:
                            if not ind_text:
                                ind_text = t.text
                        elif "eng" in lang or "english" in lang:
                            if not eng_text:
                                eng_text = t.text
                        elif "ara" in lang or "arabic" in lang:
                            if not ara_text:
                                ara_text = t.text

                    doc_parts = [f"Kitab: {book_name}"]
                    if section_title:
                        doc_parts.append(f"Bab: {section_title}")
                    if ind_text:
                        doc_parts.append(f"Teks Indonesia: {ind_text}")
                    if eng_text:
                        doc_parts.append(f"Teks Inggris: {eng_text}")

                    document_content = "\n".join(doc_parts)
                    if len(document_content) > max_doc_length:
                        document_content = document_content[:max_doc_length]

                    batch_records.append(
                        {
                            "hadith_id": hadith.id,
                            "book_slug": book_slug,
                            "book_name": book_name,
                            "hadith_number": float(hadith.hadith_number),
                            "arabic_number": (
                                float(hadith.arabic_number)
                                if hadith.arabic_number is not None
                                else 0.0
                            ),
                            "section_number": section_num,
                            "section_title": section_title,
                            "indonesian_text": ind_text,
                            "english_text": eng_text,
                            "arabic_text": ara_text,
                            "document_content": document_content,
                        }
                    )
                    batch_texts.append(document_content)

                # Heavy GPU/CPU Embedding Inference
                batch_embeddings = self.provider.embed_texts(batch_texts)

                for idx, rec in enumerate(batch_records):
                    rec["vector"] = batch_embeddings[idx]
                    f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")

                f_out.flush()
                processed_count += len(batch_records)

                if show_progress:
                    logger.info(
                        f"Vektor tersimpan di JSONL: {processed_count}/{len(all_hadiths)} hadis ({processed_count / len(all_hadiths) * 100:.1f}%)"
                    )

                del batch_records, batch_texts, batch_embeddings, hadith_chunk
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

        logger.info(f"Tahap 1 Selesai! File '{self.json_file_path}' berisi {processed_count} vektor hadis.")
        return processed_count

    def create_vector_index(self) -> bool:
        """TAHAP 2 (RINGAN & TANPA REKALKULASI GPU): Membaca file JSONL dan membuat LanceDB Index dalam hitungan detik."""
        import json

        logger.info("=== TAHAP 2: BACA FILE JSONL -> BUILD LANCEDB INDEX (TANPA KALKULASI BERAT) ===")

        if not os.path.exists(self.json_file_path):
            logger.error(
                f"File simpanan vektor '{self.json_file_path}' tidak ditemukan. Jalankan Tahap 1 (build-vectors) terlebih dahulu."
            )
            return False

        logger.info(f"Memuat data vektor dari file '{self.json_file_path}'...")
        records = []
        with open(self.json_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    records.append(json.loads(line_str))

        if not records:
            logger.warning("File JSONL kosong.")
            return False

        logger.info(f"Menulis {len(records)} baris data ke LanceDB tabel '{self.table_name}'...")
        table = self.db.create_table(self.table_name, data=records, mode="overwrite")

        logger.info(f"Membuat IVF-PQ Vector Index di LanceDB...")
        try:
            table.create_index("vector")
            logger.info("Tahap 2 Selesai! Vector Index LanceDB berhasil dibuat secara instant.")
            return True
        except Exception as e:
            logger.warning(f"Membuat index standar (Flat search aktif): {e}")
            return True

    async def build_index(
        self,
        session: AsyncSession,
        batch_size: int = 250,
        show_progress: bool = True,
        max_doc_length: int = 3000,
        reset: bool = False,
    ) -> int:
        """Eksekusi Gabungan: Tahap 1 (Pembuatan Vektor dengan Checkpoint) + Tahap 2 (Pembuatan Index)."""
        count = await self.generate_vectors(
            session=session,
            batch_size=batch_size,
            show_progress=show_progress,
            max_doc_length=max_doc_length,
            reset=reset,
        )
        self.create_vector_index()
        return count

    async def search(
        self,
        query: str,
        limit: int = 5,
        book_slug: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Mencari hadis relevan secara semantik menggunakan query vektor."""
        if not query.strip():
            return []

        def _has_table(db_obj, name: str) -> bool:
            if hasattr(db_obj, "list_tables"):
                res = db_obj.list_tables()
                if hasattr(res, "tables"):
                    return name in res.tables
                return name in list(res)
            return name in db_obj.table_names()

        if not _has_table(self.db, self.table_name):
            logger.error(
                f"Vector table '{self.table_name}' not found. Please run build-vector-index first."
            )
            raise RuntimeError(
                f"Vector index table '{self.table_name}' does not exist. Run 'build-vector-index' first."
            )

        table = self.db.open_table(self.table_name)

        logger.info(f"Embedding query: '{query}'")
        query_vector = self.provider.embed_query(query)

        search_query = table.search(query_vector)

        if book_slug:
            search_query = search_query.where(f"book_slug = '{book_slug}'")

        results = search_query.limit(limit).to_list()

        formatted_results = []
        for r in results:
            dist = r.get("_distance", 0.0)
            # Distance in cosine/L2 metric: convert to similarity score
            score = max(0.0, 1.0 - dist) if dist <= 1.0 else 1.0 / (1.0 + dist)
            formatted_results.append(
                {
                    "hadith_id": r["hadith_id"],
                    "book_slug": r["book_slug"],
                    "book_name": r["book_name"],
                    "hadith_number": r["hadith_number"],
                    "arabic_number": r["arabic_number"],
                    "section_title": r["section_title"],
                    "indonesian_text": r["indonesian_text"],
                    "english_text": r["english_text"],
                    "arabic_text": r["arabic_text"],
                    "score": round(score, 4),
                    "distance": round(dist, 4),
                }
            )

        return formatted_results
