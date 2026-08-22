from dataclasses import dataclass
from typing import Optional


@dataclass
class SectionDomain:
    book_slug: str
    section_number: int
    title: str = ""
    hadithnumber_first: Optional[float] = None
    hadithnumber_last: Optional[float] = None
    arabicnumber_first: Optional[float] = None
    arabicnumber_last: Optional[float] = None
