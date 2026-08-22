# Hadith API Database Importer & Schema

Aplikasi Importer Data Hadis dari **[fawazahmed0/hadith-api](https://github.com/fawazahmed0/hadith-api)** ke Database Relasional (PostgreSQL, SQLite, MySQL) berbasis **Python Async & SQLAlchemy 2.0 ORM**.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aarestu/hadist-api/blob/master/docs/Colab_Hadist_API_Vector_Search.ipynb)

---

## 🛠️ Isolated Workspace Setup (Venv & Conda)

Untuk menghindari konflik dependensi Python global, Anda dapat mengaktifkan lingkungan terisolasi (*isolated environment*) menggunakan **Virtualenv (venv)** atau **Conda**.

### Opsi A: Menggunakan Automatic Venv Script (Direkomendasikan)

#### **Windows (Command Prompt / PowerShell)**
Jalankan script `setup.bat`:
```cmd
setup.bat
```
Untuk mengaktifkan environment kapan saja:
```cmd
.venv\Scripts\activate
```

#### **Linux / macOS (Bash / Zsh)**
Jalankan script `setup.sh`:
```bash
chmod +x setup.sh
./setup.sh
```
Untuk mengaktifkan environment kapan saja:
```bash
source .venv/bin/activate
```

---

### Opsi B: Menggunakan Anaconda / Miniconda

Jika Anda menggunakan Conda, gunakan file `environment.yml`:
```bash
# 1. Buat conda environment baru bernama 'hadist-api'
conda env create -f environment.yml

# 2. Aktifkan conda environment
conda activate hadist-api
```

---

## 🚀 Cara Menjalankan Importer

Setelah mengaktifkan venv/conda environment:

### 1. Impor Data Hadis (Normal Run)
```bash
python -m app.cli.main
```

### 2. Reset Database & Impor Ulang
Jika Anda ingin menghapus seluruh data lama dan mengimpor ulang dari awal:
```bash
python -m app.cli.main --reset
```

### 3. Reset Database Saja (Tanpa Impor)
Jika Anda hanya ingin menghapus data dan mengosongkan database:
```bash
python -m app.cli.main --reset-only
```

### 5. Pencarian Hadis (CLI Search & Semantic Search)
Anda dapat mencari hadis spesifik berdasarkan nama kitab (`--book` / `-b`) dan nomor kanonikal digital (`--number` / `-n`) ATAU nomor cetakan Arab (`--arabic-number` / `-a`):
```bash
# Pencarian berdasarkan Nomor Digital Kanonikal
python -m app.cli.search -b abudawud -n 1035

# Pencarian berdasarkan Nomor Cetakan Arab
python -m app.cli.search -b abudawud -a 1035
```
Atau dengan filter satu/beberapa bahasa terjemahan sekaligus (`--lang` / `-l`):
```bash
python -m app.cli.search -b abudawud -n 1035 -l Indonesian Arabic
```

---

## 🔍 Pencarian Semantik (Vector Search)

Aplikasi ini mendukung **Vector / Semantic Search** berbasis **LanceDB** untuk mencari hadis berdasarkan kemiripan makna/konteks (bukan sekadar kata kunci eksak).

### 1. Pembuatan Vektor & Indexing Hadis

Proses perancangan vektor kini dipisah menjadi dua tahap modular yang **dapat di-resume/dihentikan kapan saja tanpa kehilangan progres**:

#### **Tahap 1: Pembuatan Vektor Embedding (Build Vectors -> JSONL Staging)**
Menghasilkan vektor embedding menggunakan model GPU/CPU (kalkulasi berat) dan menyimpannya secara bertahap ke file staging `vector_store/embeddings.jsonl`.
Proses ini **Checkpointed**: jika dihentikan kapan saja, proses akan **melanjutkan dari data tersisa** (tanpa mengulang dari 0):
```bash
# Melanjutkan / membuat vektor ke embeddings.jsonl
python -m app.cli.vector_cli build-vectors --batch-size 250

# (Opsional) Jika ingin menghapus file simpanan lama dan membuat ulang dari 0:
python -m app.cli.vector_cli build-vectors --reset
```

#### **Tahap 2: Pembuatan Struktur Index LanceDB (Create Index - Sangat Cepat / Instant)**
Membaca file `vector_store/embeddings.jsonl` dan menyimpannya ke LanceDB Table & IVF-PQ Index. **Tanpa kalkulasi berat GPU/Model**, selesai dalam hitungan detik:
```bash
python -m app.cli.vector_cli create-index
```

#### **Atau Jalankan Otomatis Kedua Tahap Sekaligus:**
```bash
python -m app.cli.vector_cli build-index
```

### 2. Melakukan Pencarian Semantik
Anda dapat mencari hadis relevan berdasarkan kueri topik atau konsep:
```bash
# Menggunakan CLI Vector Search
python -m app.cli.vector_cli search -q "memuliakan dan menghormati tetangga" -k 5

# Menggunakan CLI Search utama dengan flag --semantic (-s)
python -m app.cli.search -s "amalan tergantung pada niat"
```
### 3. Benchmarking Best Embedding Batch Size
Untuk mencari batch size terbaik (kecepatan & penggunaan VRAM) yang paling optimal di perangkat CPU/GPU Anda:
```bash
python -m app.cli.vector_cli benchmark-batch -s 500
```
Atau menggunakan CLI benchmark terpisah:
```bash
python -m app.cli.benchmark_batch -s 500
```

---

## ☁️ Jalankan di Google Colab (Free T4 GPU)

Anda dapat menguji dan menjalankan proses pembuatan vektor embedding & pencarian semantik secara gratis menggunakan GPU T4 di Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aarestu/hadist-api/blob/master/docs/Colab_Hadist_API_Vector_Search.ipynb)

1. Buka notebook [`docs/Colab_Hadist_API_Vector_Search.ipynb`](docs/Colab_Hadist_API_Vector_Search.ipynb) atau klik tombol **Open In Colab** di atas.
2. Pastikan GPU aktif: **Runtime** -> **Change runtime type** -> **T4 GPU**.
3. Jalankan sel berurutan untuk clone repo, impor data, generate vector, dan cari hadis semantik.

---

## ⚙️ Konfigurasi (`config.yaml` & `.env`)

Anda dapat menyesuaikan database target dan filter bahasa pada `config.yaml`:

```yaml
# Target Database Connection String
# PostgreSQL: postgresql+asyncpg://user:pass@localhost:5432/hadist_db
# SQLite: sqlite+aiosqlite:///hadist.db
database_url: "sqlite+aiosqlite:///hadist.db"

http:
  timeout_seconds: 30
  max_concurrent_requests: 10
  max_retries: 3
  base_url: "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"

# Filter edisi yang diimpor
editions_filter:
  languages:
    - "Indonesian"
    - "Arabic"
    - "English"

# Pengaturan Vector Search & Embedding Provider
vector_search:
  vector_db_path: "vector_store"
  table_name: "hadith_vectors"
  provider: "sentence-transformers" # Opsi: "sentence-transformers", "openai"
  model_name: "BAAI/bge-m3" # Model open-source lokal (100+ bahasa)
  openai_api_key: "" # Opsional jika provider="openai"
  openai_model: "text-embedding-3-small"
```

---

## 📁 Struktur Project

```
hadist-api/
├── CONTEXT.md               # Glosarium Bahasa Domain (Book, Section, Edition, Hadith, Grade)
├── docs/
│   ├── adr/
│   │   └── 0001-vector-search-architecture.md # Architectural Decision Record Vector Search
│   ├── Colab_Hadist_API_Vector_Search.ipynb  # Interactive Google Colab Notebook
│   └── hadist-schema.md     # Rancangan Skema Relasional & PostgreSQL DDL (Trigram Index)
├── setup.bat                # Automated Venv Setup Script (Windows)
├── setup.sh                 # Automated Venv Setup Script (Linux/macOS)
├── environment.yml          # Anaconda / Conda Environment Specs
├── requirements.txt         # Pip dependency list
├── config.yaml              # App configuration file
├── .env.example             # Environment variable template
└── app/
    ├── domain/              # Layer 1: Domain Entities (dataclasses)
    ├── infrastructure/      # Layer 2: Database ORM Models, Config & HTTP Client
    │   ├── database/
    │   ├── config.py
    │   └── http_client.py
    ├── services/            # Layer 3: Application Business Logic
    │   ├── importer_service.py
    │   ├── search_service.py
    │   ├── embedding_provider.py      # Modular Embedding Provider (BGE-M3 / OpenAI)
    │   ├── vector_search_service.py   # LanceDB Vector Search Engine
    │   └── batch_benchmark_service.py # Optimizer Batch Size GPU/CPU
    └── cli/                 # Layer 4: Command Line Interface Entrypoint
        ├── main.py
        ├── search.py
        ├── vector_cli.py
        └── benchmark_batch.py
```
