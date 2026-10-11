import math
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MarkCategory(str, Enum):
    ASSIGNMENT = "Assignment"
    TEST = "Test"
    EXAM = "Exam"


class StudentCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    grade: str = Field(min_length=1, max_length=60)
    student_number: str | None = Field(default=None, max_length=40)

    @field_validator("full_name", "grade")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value must not be blank.")
        return value

    @field_validator("student_number")
    @classmethod
    def strip_student_number(cls, value: str | None) -> str | None:
        value = value.strip() if value else None
        return value or None


class StudentUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    grade: str | None = Field(default=None, min_length=1, max_length=60)
    student_number: str | None = Field(default=None, max_length=40)

    @field_validator("full_name", "grade")
    @classmethod
    def strip_optional_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Value must not be blank.")
        return value

    @field_validator("student_number")
    @classmethod
    def strip_optional_student_number(cls, value: str | None) -> str | None:
        value = value.strip() if value else None
        return value or None

    @model_validator(mode="after")
    def require_a_change(self) -> "StudentUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        if any(
            getattr(self, field) is None
            for field in self.model_fields_set
            if field != "student_number"
        ):
            raise ValueError("Student name and grade cannot be null.")
        return self


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    grade: str
    student_number: str | None
    created_at: datetime


class StudentListResponse(BaseModel):
    items: list[StudentRead]
    total: int
    limit: int
    offset: int


class GradeSummary(BaseModel):
    category_averages: dict[MarkCategory, float | None]
    overall_mark: float | None
    points_earned: float
    points_possible: float
    assessment_count: int


class MarkCreate(BaseModel):
    category: MarkCategory
    title: str = Field(min_length=1, max_length=120)
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    assessed_on: date

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Assessment title must not be blank.")
        return value

    @field_validator("score", "max_score")
    @classmethod
    def require_finite_score(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Score must be a finite number.")
        return value

    @model_validator(mode="after")
    def score_must_not_exceed_maximum(self) -> "MarkCreate":
        if self.score > self.max_score:
            raise ValueError("Score cannot exceed the maximum score.")
        return self


class MarkUpdate(BaseModel):
    category: MarkCategory | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)
    score: float | None = Field(default=None, ge=0)
    max_score: float | None = Field(default=None, gt=0)
    assessed_on: date | None = None

    @field_validator("title")
    @classmethod
    def strip_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Assessment title must not be blank.")
        return value

    @field_validator("score", "max_score")
    @classmethod
    def require_finite_optional_score(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("Score must be a finite number.")
        return value

    @model_validator(mode="after")
    def require_a_change_and_consistent_scores(self) -> "MarkUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Mark fields cannot be null.")
        if (
            self.score is not None
            and self.max_score is not None
            and self.score > self.max_score
        ):
            raise ValueError("Score cannot exceed the maximum score.")
        return self


class MarkRead(BaseModel):
    id: int
    student_id: int
    category: MarkCategory
    title: str
    score: float
    max_score: float
    percentage: float
    assessed_on: date
    created_at: datetime


class StudentDetail(StudentRead):
    summary: GradeSummary
    marks: list[MarkRead]
