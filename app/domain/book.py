from dataclasses import dataclass


@dataclass
class BookDomain:
    slug: str
    name: str
    total_hadiths: int = 0
