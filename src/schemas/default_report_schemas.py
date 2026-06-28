from dataclasses import dataclass
from typing import Protocol


class ReportLike(Protocol):
    complexity: str
    estimated_hours: float
    priority: str


@dataclass(slots=True, frozen=True)
class DefaultReport:
    complexity: str = "easy"
    estimated_hours: float = 2.0
    priority: str = "medium"