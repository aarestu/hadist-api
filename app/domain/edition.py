from dataclasses import dataclass
from typing import Optional


@dataclass
class EditionDomain:
    name: str
    book_slug: str
    language: str
    iso_code: str
    author: str = "Unknown"
    direction: str = "ltr"
    has_sections: bool = True
    source: Optional[str] = None
    comments: Optional[str] = None
    link: Optional[str] = None
    linkmin: Optional[str] = None
