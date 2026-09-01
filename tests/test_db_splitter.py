import gzip
import os
import sqlite3
import pytest
from app.services.db_splitter_service import HadithDbSplitterService


@pytest.fixture
def temp_hadith_db(tmp_path):
    db_file = tmp_path / "sample_hadist.db"
    conn = sqlite3.connect(str(db_file))
    c = conn.cursor()

    # DDL
    c.executescript("""
    CREATE TABLE books (
        slug VARCHAR(50) NOT NULL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        total_hadiths INTEGER NOT NULL,
        created_at DATETIME NOT NULL
    );
    CREATE TABLE graders (
        id INTEGER NOT NULL PRIMARY KEY,
        name VARCHAR(150) NOT NULL UNIQUE
    );
    CREATE TABLE editions (
        name VARCHAR(100) NOT NULL PRIMARY KEY,
        book_slug VARCHAR(50) NOT NULL,
        language VARCHAR(50) NOT NULL,
        iso_code VARCHAR(10) NOT NULL,
        author VARCHAR(255) NOT NULL,
        direction VARCHAR(3) NOT NULL,
        has_sections BOOLEAN NOT NULL,
        source TEXT,
        comments TEXT,
        link TEXT,
        linkmin TEXT,
        created_at DATETIME NOT NULL,
        FOREIGN KEY(book_slug) REFERENCES books (slug)
    );
    CREATE TABLE sections (
        id INTEGER NOT NULL PRIMARY KEY,
        book_slug VARCHAR(50) NOT NULL,
        section_number INTEGER NOT NULL,
        title TEXT NOT NULL,
        hadithnumber_first NUMERIC(10, 2),
        hadithnumber_last NUMERIC(10, 2),
        arabicnumber_first NUMERIC(10, 2),
        arabicnumber_last NUMERIC(10, 2),
        created_at DATETIME NOT NULL,
        FOREIGN KEY(book_slug) REFERENCES books (slug)
    );
    CREATE TABLE hadiths (
        id INTEGER NOT NULL PRIMARY KEY,
        book_slug VARCHAR(50) NOT NULL,
        section_id INTEGER,
        hadith_number NUMERIC(10, 2) NOT NULL,
        arabic_number NUMERIC(10, 2),
        reference_book INTEGER,
        reference_hadith INTEGER,
        created_at DATETIME NOT NULL,
        FOREIGN KEY(book_slug) REFERENCES books (slug),
        FOREIGN KEY(section_id) REFERENCES sections (id)
    );
    CREATE TABLE hadith_grades (
        id INTEGER NOT NULL PRIMARY KEY,
        hadith_id INTEGER NOT NULL,
        grader_id INTEGER NOT NULL,
        grade VARCHAR(255) NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY(hadith_id) REFERENCES hadiths (id),
        FOREIGN KEY(grader_id) REFERENCES graders (id)
    );
    CREATE TABLE hadith_texts (
        id INTEGER NOT NULL PRIMARY KEY,
        hadith_id INTEGER NOT NULL,
        edition_name VARCHAR(100) NOT NULL,
        text TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY(hadith_id) REFERENCES hadiths (id),
        FOREIGN KEY(edition_name) REFERENCES editions (name)
    );
    """)

    # Seed data
    c.execute("INSERT INTO books VALUES ('bukhari', 'Sahih Bukhari', 7000, '2026-01-01 00:00:00')")
    c.execute("INSERT INTO graders VALUES (1, 'Al-Albani')")
    c.execute(
        "INSERT INTO editions VALUES ('ind-bukhari', 'bukhari', 'Indonesian', 'ind', 'Author', 'ltr', 1, null, null, null, null, '2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO editions VALUES ('ara-bukhari', 'bukhari', 'Arabic', 'ara', 'Author', 'rtl', 1, null, null, null, null, '2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO sections VALUES (10, 'bukhari', 1, 'Iman', 1, 10, 1, 10, '2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO hadiths VALUES (100, 'bukhari', 10, 1.0, 1.0, 1, 1, '2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO hadith_grades VALUES (1, 100, 1, 'Sahih', '2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO hadith_texts VALUES (1, 100, 'ind-bukhari', 'Sesungguhnya amal itu tergantung niat.', '2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO hadith_texts VALUES (2, 100, 'ara-bukhari', 'إنما الأعمال بالنيات', '2026-01-01 00:00:00')"
    )

    conn.commit()
    conn.close()
    return str(db_file)


def test_get_available_languages(temp_hadith_db):
    splitter = HadithDbSplitterService(source_db_path=temp_hadith_db)
    langs = splitter.get_available_languages()
    assert len(langs) == 2
    assert ("ara", "Arabic") in langs
    assert ("ind", "Indonesian") in langs


def test_split_by_language(temp_hadith_db, tmp_path):
    output_dir = str(tmp_path / "data")
    splitter = HadithDbSplitterService(
        source_db_path=temp_hadith_db,
        output_dir=output_dir,
    )

    res = splitter.split_by_language(
        target_lang_key="id",
        iso_code="ind",
        lang_name="Indonesian",
        create_gzip=True,
    )

    assert res["language"] == "Indonesian"
    assert res["hadiths"] == 1
    assert res["texts"] == 1
    assert os.path.exists(res["database"])
    assert os.path.exists(res["gzip_file"])

    # Verify foreign key integrity in generated DB
    conn = sqlite3.connect(res["database"])
    c = conn.cursor()
    c.execute("PRAGMA foreign_key_check;")
    assert c.fetchall() == []

    # Verify content
    c.execute("SELECT name FROM editions;")
    assert c.fetchall() == [("ind-bukhari",)]

    c.execute("SELECT text FROM hadith_texts;")
    assert c.fetchone()[0] == "Sesungguhnya amal itu tergantung niat."

    conn.close()

    # Test gzip uncompression
    with gzip.open(res["gzip_file"], "rb") as gz:
        content = gz.read()
        assert len(content) > 0


def test_split_missing_source_db():
    splitter = HadithDbSplitterService(source_db_path="non_existent.db")
    with pytest.raises(FileNotFoundError):
        splitter.get_available_languages()
