from dataclasses import dataclass
from typing import Optional


@dataclass
class GraderDomain:
    name: str
    id: Optional[int] = None
