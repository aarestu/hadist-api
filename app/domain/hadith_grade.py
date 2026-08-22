from dataclasses import dataclass


@dataclass
class HadithGradeDomain:
    hadith_id: int
    grader_id: int
    grade: str
