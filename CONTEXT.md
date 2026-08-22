# Context & Domain Glossary (Glosarium Hadis)

Dokumen ini mendokumentasikan istilah-istilah domain utama yang digunakan dalam proyek ini. Glosarium ini berfungsi sebagai acuan istilah (*Ubiquitous Language*) agar seluruh entitas, tabel, dan API memiliki pemahaman konsep yang konsisten.

---

## Entitas & Istilah Domain Utama

### Kitab (Book)
Koleksi utama kumpulan hadis yang disusun oleh imam/ulama perawi utama (contoh: *Sahih Bukhari*, *Sahih Muslim*, *Sunan Abu Dawud*). Setiap kitab diidentifikasi dengan slug unik (misalnya `bukhari`, `muslim`, `abudawud`).

### Bab / Bagian (Section)
Pengelompokan tematis hadis di dalam suatu kitab (contoh: *Purification / Thaharah*, *Prayer / Salat*). Setiap bab memiliki judul, nomor bab, serta rentang nomor hadis awal hingga akhir dalam kitab tersebut.

### Hadis Kanonikal (Canonical Hadith)
Entitas dasar/induk dari satu unit hadis dalam sebuah kitab. Memiliki nomor identitas unik digital (`hadith_number`) dalam kitab tersebut, serta referensi kitab cetakan tradisional (*reference book* & *reference hadith*).

### Nomor Hadis (Hadith Numbers)
Sistem penomoran unit hadis yang terdiri dari 3 jenis referensi:
1. **Hadith Number (Nomor Kanonikal)**: Penomoran standar digital (bisa bernilai desimal/pecahan seperti `1035` atau `1.1`).
2. **Arabic Number**: Penomoran versi cetakan Arab tradisional.
3. **Reference Book & Hadith**: Pasangan nomor kitab internal dan nomor hadis berdasarkan referensi sistem penomoran internasional (misal: USC-MSA atau Darussalam).

### Matan / Teks Hadis (Hadith Text)
Isi/kandungan redaksi sabda, perbuatan, atau ketetapan Nabi Muhammad ﷺ dalam versi bahasa tertentu atau edisi tertentu. Satu Hadis Kanonikal memiliki banyak Matan/Teks berdasarkan edisi terjemahan atau varian teks.

### Edisi (Edition)
Versi publikasi teks hadis berdasarkan bahasa, penerjemah, atau varian format teks. Edisi dibagi menjadi dua kategori:
1. **Edisi Terjemahan (Translation Edition)**: Teks matan yang diterjemahkan ke bahasa tertentu (contoh: `ind-bukhari` untuk Bahasa Indonesia, `eng-bukhari` untuk Bahasa Inggris).
2. **Varian Teks Asli (Text Variant Edition)**: Formatted teks Arab asli dengan harakat (`ara-bukhari`) atau gundul/tanpa harakat (`ara-bukhari1`) untuk mempermudah pencarian.

### Muhaddits / Penilai Hadis (Grader)
Ulama atau pakar hadis yang menilai derajat keshahihan sanad dan matan suatu hadis (contoh: *Al-Albani*, *Zubair Ali Zai*, *Muhammad Muhyi Al-Din Abdul Hamid*).

### Derajat Hadis (Hadith Grade)
Status keshahihan suatu hadis berdasarkan penilaian ulama tertentu (contoh: *Sahih*, *Hasan*, *Daif*, *Isnaad Hasan*).

### Pencarian Semantik (Semantic / Vector Search)
Metode pencarian hadis berdasarkan kemiripan makna dan relevansi konteks menggunakan perbandingan vektor (*vector similarity*), bukan sekadar perbandingan kata kunci (*exact keyword match*).

### Hadis Vektor / Embedding Hadis (Hadith Vector Embedding)
Representasi vektor numerik dimensi tinggi yang mengekstrak kandungan makna dari satu unit Hadis Kanonikal (termasuk judul bab, kitab, dan teks terjemahan).

### Penyimpanan Vektor (Vector Store)
Sistem basis data khusus berbasis file (*embedded vector database* seperti LanceDB) yang menyimpan vektor embedding hadis dan memfasilitasi kueri pencarian tetangga terdekat (*nearest neighbor search* / *cosine similarity*).

