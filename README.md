# Student Marks

A small teacher-facing markbook built with FastAPI, Jinja2, and SQLite. Student records and assessment marks are saved in `data/student_marks.db`. The Excel export is a downloadable report generated from the database.

## Features

- Teacher sign-in with a password stored as a salted PBKDF2 hash.
- Student profiles with optional unique student numbers and a grade/class.
- Assignment, test, and exam assessments, each with its own title, date, score, and maximum score.
- Per-category averages and an overall points-based percentage.
- Student search, markbook reports, and an Excel workbook with summary and detailed assessment sheets.
- Assessment and student deletion, password changes, input validation, and form CSRF tokens.

The overall mark is `sum of points earned / sum of points possible × 100`. A category average is the unweighted mean of the percentages for assessments in that category. Categories without marks are shown as empty rather than zero.

## Run locally

Requires Python 3.10 or newer.

```powershell
uv sync
$env:INITIAL_TEACHER_PASSWORD = "choose-a-password-at-least-12-chars"
$env:SESSION_SECRET = (uv run python -c "import secrets; print(secrets.token_urlsafe(32))")
uv run fastapi dev main.py
```

Open <http://127.0.0.1:8000>. The initial username is `teacher`; the password is the value set above. If `INITIAL_TEACHER_PASSWORD` is not set on a fresh database, the app generates an initial password and prints it to the server console. Change the password after signing in. Keep `SESSION_SECRET` stable between restarts and use a private value outside local development. Set `COOKIE_SECURE=true` when serving the app over HTTPS.

The root `main.py` exposes the FastAPI application for FastAPI's development CLI. You can also start it with `uv run uvicorn app.main:app --reload`.

By default, the SQLite file is created at `data/student_marks.db`. To store it elsewhere, set `DATABASE_PATH` to a full file path before starting the server.

## REST API

The versioned JSON API starts at `/api/v1`. Interactive documentation is available at `/docs` (Swagger UI), `/redoc`, and `/openapi.json`. The API uses HTTP Basic authentication with the teacher account; in Swagger UI, select **Authorize** and enter the teacher username and password. Use HTTPS when accessing the API over a network.

| Method | URL | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/students?search=&limit=50&offset=0` | Search and page through the roster |
| `POST` | `/api/v1/students` | Register a student |
| `GET` | `/api/v1/students/{student_id}` | Get a student's profile, marks, and calculated summary |
| `PATCH` | `/api/v1/students/{student_id}` | Update a student's name, grade, or number |
| `DELETE` | `/api/v1/students/{student_id}` | Delete a student and their marks |
| `GET` | `/api/v1/students/{student_id}/marks` | List the student's marks |
| `POST` | `/api/v1/students/{student_id}/marks` | Enter an assignment, test, or exam mark |
| `PATCH` | `/api/v1/students/{student_id}/marks/{mark_id}` | Update a mark |
| `DELETE` | `/api/v1/students/{student_id}/marks/{mark_id}` | Delete a mark |

For example, register a student with:

```json
{
  "full_name": "Alex Morgan",
  "grade": "Grade 10",
  "student_number": "STU-101"
}
```

Then enter a mark at `/api/v1/students/{student_id}/marks`:

```json
{
  "category": "Assignment",
  "title": "Fractions worksheet",
  "score": 18,
  "max_score": 20,
  "assessed_on": "2026-10-10"
}
```

The category must be `Assignment`, `Test`, or `Exam`; marks must be finite, non-negative, and no higher than the maximum score. The API uses `401` for missing or invalid credentials, `404` for unknown students/marks, and `409` when a student number is already registered.

## Tests

```powershell
uv run python -m unittest discover -s tests
```
