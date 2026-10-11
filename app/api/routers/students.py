import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies import get_student_or_404, require_teacher
from app.database import connect
from app.grades import summarize_assessments
from app.models import Student
from app.schemas import StudentCreate, StudentDetail, StudentListResponse, StudentRead, StudentUpdate


router = APIRouter(
    prefix="/students",
    tags=["Students"],
    dependencies=[Depends(require_teacher)],
)


@router.get(
    "",
    response_model=StudentListResponse,
    summary="List and search students",
    description="Returns registered students with limit/offset pagination. Search matches name, student number, or grade.",
)
def list_students(
    search: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    search = search.strip() if search else ""
    with connect() as connection:
        if search:
            pattern = f"%{search}%"
            where = (
                "WHERE full_name LIKE ? OR student_number LIKE ? OR grade LIKE ?"
            )
            parameters = (pattern, pattern, pattern)
            total = connection.execute(
                f"SELECT COUNT(*) FROM students {where}", parameters
            ).fetchone()[0]
            rows = connection.execute(
                f"SELECT * FROM students {where} "
                "ORDER BY full_name COLLATE NOCASE LIMIT ? OFFSET ?",
                (*parameters, limit, offset),
            ).fetchall()
        else:
            total = connection.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            rows = connection.execute(
                "SELECT * FROM students ORDER BY full_name COLLATE NOCASE "
                "LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()

    return StudentListResponse(
        items=[StudentRead.model_validate(Student.from_row(row)) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=StudentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a student",
)
def register_student(student: StudentCreate):
    try:
        with connect() as connection:
            cursor = connection.execute(
                "INSERT INTO students (student_number, full_name, grade) "
                "VALUES (?, ?, ?)",
                (student.student_number, student.full_name, student.grade),
            )
            row = connection.execute(
                "SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That student number is already in use.",
        ) from exc
    return StudentRead.model_validate(Student.from_row(row))


@router.get(
    "/{student_id}",
    response_model=StudentDetail,
    summary="Get a student and their marks",
)
def get_student(student_id: int):
    student = get_student_or_404(student_id)
    with connect() as connection:
        mark_rows = connection.execute(
            "SELECT * FROM assessments WHERE student_id = ? "
            "ORDER BY assessed_on DESC, id DESC",
            (student_id,),
        ).fetchall()

    marks = [
        {
            "id": row["id"],
            "student_id": row["student_id"],
            "category": row["category"],
            "title": row["title"],
            "score": row["score"],
            "max_score": row["max_score"],
            "percentage": row["score"] / row["max_score"] * 100,
            "assessed_on": row["assessed_on"],
            "created_at": row["created_at"],
        }
        for row in mark_rows
    ]
    grade_summary = summarize_assessments(mark_rows)

    return StudentDetail(
        **StudentRead.model_validate(student).model_dump(),
        summary={
            "category_averages": grade_summary["categories"],
            "overall_mark": grade_summary["overall"],
            "points_earned": grade_summary["earned"],
            "points_possible": grade_summary["possible"],
            "assessment_count": grade_summary["assessment_count"],
        },
        marks=marks,
    )


@router.patch(
    "/{student_id}",
    response_model=StudentRead,
    summary="Update a student registration",
)
def update_student(student_id: int, student_update: StudentUpdate):
    student = get_student_or_404(student_id)
    changes = student_update.model_dump(exclude_unset=True)
    updated_values = {
        "full_name": changes.get("full_name", student.full_name),
        "grade": changes.get("grade", student.grade),
        "student_number": changes.get("student_number", student.student_number),
    }
    try:
        with connect() as connection:
            connection.execute(
                "UPDATE students SET full_name = ?, grade = ?, student_number = ? "
                "WHERE id = ?",
                (
                    updated_values["full_name"],
                    updated_values["grade"],
                    updated_values["student_number"],
                    student_id,
                ),
            )
            row = connection.execute(
                "SELECT * FROM students WHERE id = ?", (student_id,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That student number is already in use.",
        ) from exc
    return StudentRead.model_validate(Student.from_row(row))


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a student and their marks",
)
def delete_student(student_id: int):
    get_student_or_404(student_id)
    with connect() as connection:
        connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
