from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Student:
    id: int
    full_name: str
    grade: str
    student_number: str | None
    created_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> "Student":
        return cls(
            id=row["id"],
            full_name=row["full_name"],
            grade=row["grade"],
            student_number=row["student_number"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


@dataclass(frozen=True)
class Mark:
    id: int
    student_id: int
    category: str
    title: str
    score: float
    max_score: float
    assessed_on: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> "Mark":
        return cls(
            id=row["id"],
            student_id=row["student_id"],
            category=row["category"],
            title=row["title"],
            score=float(row["score"]),
            max_score=float(row["max_score"]),
            assessed_on=row["assessed_on"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
