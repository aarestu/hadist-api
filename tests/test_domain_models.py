from app.domain.book import BookDomain
from app.domain.edition import EditionDomain
from app.domain.grader import GraderDomain
from app.domain.hadith import HadithDomain
from app.domain.hadith_grade import HadithGradeDomain
from app.domain.hadith_text import HadithTextDomain
from app.domain.section import SectionDomain


def test_book_domain_creation():
    book = BookDomain(slug="bukhari", name="Sahih Bukhari", total_hadiths=7563)
    assert book.slug == "bukhari"
    assert book.name == "Sahih Bukhari"
    assert book.total_hadiths == 7563


def test_section_domain_creation():
    sec = SectionDomain(
        book_slug="bukhari",
        section_number=1,
        title="Revelation",
        hadithnumber_first=1.0,
        hadithnumber_last=7.0,
    )
    assert sec.book_slug == "bukhari"
    assert sec.section_number == 1
    assert sec.title == "Revelation"
    assert sec.hadithnumber_first == 1.0


def test_edition_domain_creation():
    ed = EditionDomain(
        name="ind-bukhari", book_slug="bukhari", language="Indonesian", iso_code="ind"
    )
    assert ed.name == "ind-bukhari"
    assert ed.language == "Indonesian"
    assert ed.direction == "ltr"


def test_hadith_domain_creation():
    h = HadithDomain(book_slug="bukhari", hadith_number=1.0, reference_book=1, reference_hadith=1)
    assert h.book_slug == "bukhari"
    assert h.hadith_number == 1.0
    assert h.reference_book == 1


def test_hadith_text_domain_creation():
    ht = HadithTextDomain(hadith_id=1, edition_name="ind-bukhari", text="Sesungguhnya amalan itu...")
    assert ht.hadith_id == 1
    assert ht.edition_name == "ind-bukhari"
    assert "amalan" in ht.text


def test_grader_domain_creation():
    g = GraderDomain(name="Al-Albani", id=1)
    assert g.name == "Al-Albani"
    assert g.id == 1


def test_hadith_grade_domain_creation():
    hg = HadithGradeDomain(hadith_id=1, grader_id=1, grade="Sahih")
    assert hg.hadith_id == 1
    assert hg.grader_id == 1
    assert hg.grade == "Sahih"
