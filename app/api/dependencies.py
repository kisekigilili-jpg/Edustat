from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.database import connect
from app.models import Student
from app.security import verify_password


basic_auth = HTTPBasic(auto_error=False)
TeacherCredentials = Annotated[HTTPBasicCredentials | None, Depends(basic_auth)]


def require_teacher(credentials: TeacherCredentials) -> int:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Teacher authentication is required.",
            headers={"WWW-Authenticate": "Basic"},
        )

    with connect() as connection:
        teacher = connection.execute(
            "SELECT id, username, password_salt, password_hash "
            "FROM teachers WHERE username = ?",
            (credentials.username.strip(),),
        ).fetchone()

    password_valid = (
        verify_password(
            credentials.password,
            teacher["password_salt"],
            teacher["password_hash"],
        )
        if teacher is not None
        else False
    )
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid teacher username or password.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return int(teacher["id"])


def get_student_or_404(student_id: int) -> Student:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM students WHERE id = ?", (student_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    return Student.from_row(row)
