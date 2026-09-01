import gzip
import logging
import os
import shutil
import sqlite3
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default language mapping:
# Key: database suffix/filename identifier -> Value: (iso_code, language_name)
DEFAULT_LANGUAGE_MAPPINGS: Dict[str, Tuple[str, str]] = {
    "id": ("ind", "Indonesian"),
    "en": ("eng", "English"),
    "ar": ("ara", "Arabic"),
}


class HadithDbSplitterService:
    """Service to split a monolithic Hadith SQLite database into separate per-language databases."""

    def __init__(
        self,
        source_db_path: str = "hadist.db",
        output_dir: str = "data",
        chunk_size: int = 900,
    ):
        self.source_db_path = source_db_path
        self.output_dir = output_dir
        self.chunk_size = chunk_size

    def get_available_languages(self) -> List[Tuple[str, str]]:
        """Retrieve all distinct (iso_code, language) combinations from the source database."""
        if not os.path.exists(self.source_db_path):
            raise FileNotFoundError(f"Database sumber tidak ditemukan: {self.source_db_path}")

        conn = sqlite3.connect(self.source_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT iso_code, language FROM editions ORDER BY language ASC")
            return cursor.fetchall()
        finally:
            conn.close()

    def split_by_language(
        self,
        target_lang_key: str,
        iso_code: str,
        lang_name: str,
        create_gzip: bool = True,
    ) -> Dict[str, any]:
        """
        Split source database for a specific language and save to data/hadist.<target_lang_key>.db.
        Returns a summary dict with statistics.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        db_filename = f"hadist.{target_lang_key}.db"
        output_db_path = os.path.join(self.output_dir, db_filename)

        if not os.path.exists(self.source_db_path):
            raise FileNotFoundError(f"Database sumber tidak ditemukan: {self.source_db_path}")

        # Remove existing file if present
        if os.path.exists(output_db_path):
            os.remove(output_db_path)

        src_conn = sqlite3.connect(self.source_db_path)
        dst_conn = sqlite3.connect(output_db_path)

        try:
            src_c = src_conn.cursor()
            dst_c = dst_conn.cursor()

            # 1. Fetch DDL schemas (tables & indexes)
            src_c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL;")
            table_ddls = [r[0] for r in src_c.fetchall()]

            src_c.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL;")
            index_ddls = [r[0] for r in src_c.fetchall()]

            # 2. Create tables in target database
            for ddl in table_ddls:
                dst_c.execute(ddl)

            # 3. Copy Editions
            src_c.execute(
                "SELECT * FROM editions WHERE iso_code = ? OR language = ?",
                (iso_code, lang_name),
            )
            editions = src_c.fetchall()
            if not editions:
                logger.warning(f"Tidak ada edisi untuk bahasa '{lang_name}' ({iso_code}).")
                return {
                    "database": output_db_path,
                    "language": lang_name,
                    "iso_code": iso_code,
                    "books": 0,
                    "editions": 0,
                    "hadiths": 0,
                    "texts": 0,
                    "size_mb": 0,
                }

            ed_names = [e[0] for e in editions]
            book_slugs = list(set([e[1] for e in editions]))

            dst_c.executemany(
                "INSERT INTO editions VALUES (" + ",".join(["?"] * len(editions[0])) + ")",
                editions,
            )

            # 4. Copy Books
            placeholders_books = ",".join(["?"] * len(book_slugs))
            src_c.execute(
                f"SELECT * FROM books WHERE slug IN ({placeholders_books})",
                book_slugs,
            )
            books = src_c.fetchall()
            if books:
                dst_c.executemany(
                    "INSERT INTO books VALUES (" + ",".join(["?"] * len(books[0])) + ")",
                    books,
                )

            # 5. Copy Sections
            src_c.execute(
                f"SELECT * FROM sections WHERE book_slug IN ({placeholders_books})",
                book_slugs,
            )
            sections = src_c.fetchall()
            if sections:
                dst_c.executemany(
                    "INSERT INTO sections VALUES (" + ",".join(["?"] * len(sections[0])) + ")",
                    sections,
                )

            # 6. Copy Hadith Texts
            placeholders_eds = ",".join(["?"] * len(ed_names))
            src_c.execute(
                f"SELECT * FROM hadith_texts WHERE edition_name IN ({placeholders_eds})",
                ed_names,
            )
            hadith_texts = src_c.fetchall()
            hadith_ids = list(set([ht[1] for ht in hadith_texts]))

            if hadith_texts:
                dst_c.executemany(
                    "INSERT INTO hadith_texts VALUES ("
                    + ",".join(["?"] * len(hadith_texts[0]))
                    + ")",
                    hadith_texts,
                )

            # 7. Copy Hadiths (batch-by-batch)
            hadiths_count = 0
            for i in range(0, len(hadith_ids), self.chunk_size):
                chunk = hadith_ids[i : i + self.chunk_size]
                placeholders = ",".join(["?"] * len(chunk))
                src_c.execute(f"SELECT * FROM hadiths WHERE id IN ({placeholders})", chunk)
                hadiths_chunk = src_c.fetchall()
                if hadiths_chunk:
                    dst_c.executemany(
                        "INSERT INTO hadiths VALUES ("
                        + ",".join(["?"] * len(hadiths_chunk[0]))
                        + ")",
                        hadiths_chunk,
                    )
                    hadiths_count += len(hadiths_chunk)

            # 8. Copy Hadith Grades (batch-by-batch)
            all_grader_ids = set()
            for i in range(0, len(hadith_ids), self.chunk_size):
                chunk = hadith_ids[i : i + self.chunk_size]
                placeholders = ",".join(["?"] * len(chunk))
                src_c.execute(
                    f"SELECT * FROM hadith_grades WHERE hadith_id IN ({placeholders})",
                    chunk,
                )
                grades_chunk = src_c.fetchall()
                if grades_chunk:
                    for g in grades_chunk:
                        all_grader_ids.add(g[2])
                    dst_c.executemany(
                        "INSERT INTO hadith_grades VALUES ("
                        + ",".join(["?"] * len(grades_chunk[0]))
                        + ")",
                        grades_chunk,
                    )

            # 9. Copy Graders
            if all_grader_ids:
                grader_list = list(all_grader_ids)
                placeholders_graders = ",".join(["?"] * len(grader_list))
                src_c.execute(
                    f"SELECT * FROM graders WHERE id IN ({placeholders_graders})",
                    grader_list,
                )
                graders = src_c.fetchall()
                if graders:
                    dst_c.executemany(
                        "INSERT INTO graders VALUES ("
                        + ",".join(["?"] * len(graders[0]))
                        + ")",
                        graders,
                    )

            # 10. Create indexes
            for ddl in index_ddls:
                dst_c.execute(ddl)

            dst_conn.commit()

            # 11. Foreign key integrity check
            dst_c.execute("PRAGMA foreign_key_check;")
            fk_errors = dst_c.fetchall()
            if fk_errors:
                logger.error(f"Foreign key violations detected in {output_db_path}: {fk_errors}")
                raise ValueError(f"Foreign key violations in {output_db_path}: {fk_errors}")

            # 12. Vacuum and Analyze for optimal size and query planning
            dst_c.execute("VACUUM;")
            dst_c.execute("ANALYZE;")

        finally:
            src_conn.close()
            dst_conn.close()

        size_mb = os.path.getsize(output_db_path) / (1024 * 1024)
        result = {
            "database": output_db_path,
            "filename": db_filename,
            "language": lang_name,
            "iso_code": iso_code,
            "books": len(books) if "books" in locals() else 0,
            "editions": len(editions),
            "hadiths": hadiths_count,
            "texts": len(hadith_texts),
            "size_mb": round(size_mb, 2),
        }

        # 13. Create gzip compression if requested
        if create_gzip:
            gz_path = f"{output_db_path}.gz"
            if os.path.exists(gz_path):
                os.remove(gz_path)

            with open(output_db_path, "rb") as f_in, gzip.open(gz_path, "wb", compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

            gz_size_mb = os.path.getsize(gz_path) / (1024 * 1024)
            result["gzip_file"] = gz_path
            result["gzip_filename"] = f"{db_filename}.gz"
            result["gzip_size_mb"] = round(gz_size_mb, 2)

        return result

    def split_all(
        self,
        custom_mappings: Optional[Dict[str, Tuple[str, str]]] = None,
        create_gzip: bool = True,
    ) -> List[Dict[str, any]]:
        """Split all configured/supported languages."""
        mappings = custom_mappings or DEFAULT_LANGUAGE_MAPPINGS
        results = []

        for key, (iso_code, lang_name) in mappings.items():
            logger.info(f"Memproses split database untuk bahasa '{lang_name}' ({iso_code}) -> hadist.{key}.db...")
            res = self.split_by_language(
                target_lang_key=key,
                iso_code=iso_code,
                lang_name=lang_name,
                create_gzip=create_gzip,
            )
            results.append(res)
            logger.info(
                f"Selesai: {res['filename']} ({res['size_mb']} MB, {res['hadiths']} hadis)"
                + (f" -> {res.get('gzip_filename')} ({res.get('gzip_size_mb')} MB)" if create_gzip else "")
            )

        return results
