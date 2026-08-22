from dataclasses import dataclass
from typing import Optional


@dataclass
class HadithDomain:
    book_slug: str
    hadith_number: float
    section_id: Optional[int] = None
    arabic_number: Optional[float] = None
    reference_book: Optional[int] = None
    reference_hadith: Optional[int] = None
