import sqlite3
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import get_student_or_404, require_teacher
from app.database import connect
from app.models import Mark
from app.schemas import MarkCreate, MarkRead, MarkUpdate


router = APIRouter(
    prefix="/students/{student_id}/marks",
    tags=["Marks"],
    dependencies=[Depends(require_teacher)],
)


def mark_response(mark: Mark) -> MarkRead:
    return MarkRead(
        id=mark.id,
        student_id=mark.student_id,
        category=mark.category,
        title=mark.title,
        score=mark.score,
        max_score=mark.max_score,
        percentage=mark.score / mark.max_score * 100,
        assessed_on=mark.assessed_on,
        created_at=mark.created_at,
    )


def get_mark_or_404(student_id: int, mark_id: int) -> Mark:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM assessments WHERE id = ? AND student_id = ?",
            (mark_id, student_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Mark not found for this student.")
    return Mark.from_row(row)


@router.get(
    "",
    response_model=list[MarkRead],
    summary="List a student's marks",
    description="Lists assignment, test, and exam marks, newest first.",
)
def list_student_marks(student_id: int):
    get_student_or_404(student_id)
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM assessments WHERE student_id = ? "
            "ORDER BY assessed_on DESC, id DESC",
            (student_id,),
        ).fetchall()
    return [mark_response(Mark.from_row(row)) for row in rows]


@router.post(
    "",
    response_model=MarkRead,
    status_code=status.HTTP_201_CREATED,
    summary="Enter a student's mark",
)
def enter_student_mark(student_id: int, mark: MarkCreate):
    get_student_or_404(student_id)
    try:
        with connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO assessments
                    (student_id, category, title, score, max_score, assessed_on)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    mark.category.value,
                    mark.title,
                    mark.score,
                    mark.max_score,
                    mark.assessed_on.isoformat(),
                ),
            )
            row = connection.execute(
                "SELECT * FROM assessments WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mark does not meet the assessment data requirements.",
        ) from exc
    return mark_response(Mark.from_row(row))


@router.patch(
    "/{mark_id}",
    response_model=MarkRead,
    summary="Update a student's mark",
)
def update_student_mark(student_id: int, mark_id: int, mark_update: MarkUpdate):
    existing = get_mark_or_404(student_id, mark_id)
    changes = mark_update.model_dump(exclude_unset=True)
    score = changes.get("score", existing.score)
    max_score = changes.get("max_score", existing.max_score)
    if score is None:
        score = existing.score
    if max_score is None:
        max_score = existing.max_score
    if score > max_score:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Score cannot exceed the maximum score.",
        )

    with connect() as connection:
        connection.execute(
            """
            UPDATE assessments
            SET category = ?, title = ?, score = ?, max_score = ?, assessed_on = ?
            WHERE id = ? AND student_id = ?
            """,
            (
                changes.get("category", existing.category).value
                if "category" in changes
                else existing.category,
                changes.get("title", existing.title),
                score,
                max_score,
                changes.get("assessed_on", date.fromisoformat(existing.assessed_on)).isoformat(),
                mark_id,
                student_id,
            ),
        )
        row = connection.execute(
            "SELECT * FROM assessments WHERE id = ? AND student_id = ?",
            (mark_id, student_id),
        ).fetchone()
    return mark_response(Mark.from_row(row))


@router.delete(
    "/{mark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a student's mark",
)
def delete_student_mark(student_id: int, mark_id: int):
    get_mark_or_404(student_id, mark_id)
    with connect() as connection:
        connection.execute(
            "DELETE FROM assessments WHERE id = ? AND student_id = ?",
            (mark_id, student_id),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
