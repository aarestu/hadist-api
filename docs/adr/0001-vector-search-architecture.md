# 1. Arsitektur Pencarian Semantik (Vector Search) Hadis

* Status: Approved
* Tanggal: 2026-04-20

## Konteks & Masalah

Pengguna membutuhkan kemampuan pencarian hadis berdasarkan relevansi makna/konteks (pencarian semantik) melebihi pencarian kata kunci (*exact/full-text search*). Data hadis terdiri dari kitab, bab, teks Arab, serta edisi terjemahan Bahasa Indonesia dan Inggris.

## Pilihan Keputusan

1. **Vector Database / Store**:
   - *LanceDB (Embedded File-based)*: Dipilih karena berjalan tanpa server tambahan, berbasis file columnar (Arrow/Parquet), ringan, dan sangat selaras dengan skema SQLite lokal maupun PostgreSQL.
   - *Alternatif lain*: Qdrant (butuh container/service), pgvector (perlu migrasi total DB ke PostgreSQL).

2. **Model & Provider Embedding**:
   - *Modular Embedding Provider Interface*: Dipilih untuk fleksibilitas. Default menggunakan model open-source lokal (seperti `BAAI/bge-m3` atau `nomic-embed-text` via sentence-transformers/fastembed) yang 100% gratis dan offline, dengan dukungan opsional untuk Cloud API (OpenAI `text-embedding-3-small`).

3. **Granularitas Indexing**:
   - *Per-Hadis Kanonikal (Aggregated)*: Teks edisi terjemahan Bahasa Indonesia & Inggris serta metadata judul bab disatukan menjadi 1 unit dokumen embedding per Hadis Kanonikal untuk memberikan relevansi konteks yang paling utuh.

4. **CLI & Service Integration**:
   - Menambahkan `app/services/vector_search_service.py` dan CLI command:
     - `build-vector-index`
     - `vector-search`

## Konsekuensi

- Membutuhkan dependensi Python tambahan (`lancedb`, `pyarrow`, `sentence-transformers` atau `fastembed`).
- Diperlukan proses build index satu kali (`build-vector-index`) untuk membentuk berkas index vektor di folder `vector_store/`.
- Pencarian semantik kini mendukung pencarian berbasis makna seperti "cara memuliakan tetangga" atau "perintah menjaga lisan" meskipun kata-kata tersebut tidak tertulis secara harfiah.
