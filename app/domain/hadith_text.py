from dataclasses import dataclass


@dataclass
class HadithTextDomain:
    hadith_id: int
    edition_name: str
    text: str
