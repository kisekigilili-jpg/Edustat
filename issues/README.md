# Student Marks App: How It Works

This guide explains the student markbook, how its parts fit together, how to run
it, and how the project was developed. The app is a Python web application built
with FastAPI, Jinja2, SQLite, and openpyxl. Project dependencies and versions are
managed with `uv`.

## What the app does

Teachers can sign in, register students, record assignment, test, and exam
results, review calculated marks, search the roster, and download an Excel
workbook. Information is saved in a local SQLite database; Excel is an export
format, not the primary storage location.

The app has two interfaces:

1. A server-rendered website for teachers using a browser.
2. A versioned JSON API for other clients and integrations.

Both interfaces use the same SQLite records and grading calculations.

## Project layout

```text
.
├── main.py                    # Root entry point for `fastapi dev main.py`
├── pyproject.toml              # Project metadata and uv-managed dependencies
├── uv.lock                     # Locked dependency versions
├── app/
│   ├── main.py                 # FastAPI application, website routes, startup
│   ├── database.py             # SQLite connection and table setup
│   ├── grades.py               # Shared mark calculations and roster summaries
│   ├── models.py               # Typed Student and Mark database records
│   ├── schemas.py              # Validated API request/response schemas
│   ├── security.py             # Password hashing and verification
│   ├── api/
│   │   ├── dependencies.py     # API teacher authentication and lookups
│   │   └── routers/
│   │       ├── students.py     # Student registration and roster endpoints
│   │       └── marks.py        # Student mark endpoints
│   ├── templates/              # Jinja2 website pages
│   └── static/styles.css       # Website styling
├── data/
│   └── student_marks.db        # Created locally when the app first runs
├── tests/                      # Unit and application integration tests
└── issues/
    └── README.md               # This guide
```

The root [main.py](../main.py) imports the FastAPI `app` from
[app/main.py](../app/main.py). Keeping that root entry point lets FastAPI's
development command discover the app.

## How a teacher uses the website

1. Open the site and sign in with the teacher account.
2. Add a student using their name and grade/class. A student number is optional,
   but if provided it must be unique.
3. Open the student's profile from the roster.
4. Record an assessment by selecting its type, entering a title, score, maximum
   score, and date.
5. Review the assessment list, category averages, and overall result on the
   student page or in Reports.
6. Download the class workbook using **Excel export**.

The dashboard and reports are rendered with the templates in
[app/templates/](../app/templates/). Website form submissions use a session
cookie and a CSRF token. Student and mark deletion are available from the
corresponding pages and require confirmation in the browser.

## How marks are calculated

An assessment percentage is:

```text
score / maximum score * 100
```

For each category (Assignment, Test, or Exam), the displayed category average
is the unweighted mean of the percentages of assessments in that category.
Assessments with different maximum scores therefore have equal weight within
their category average.

The overall mark is points-weighted:

```text
sum of all points earned / sum of all points possible * 100
```

For example, scores of 8/10 and 18/20 produce an overall mark of
26/30 * 100 = 86.7%. A category with no assessments, or a student with no
assessments, is displayed as empty rather than as zero. The shared calculation
is implemented in [app/grades.py](../app/grades.py).

## REST API

The API is versioned under `/api/v1`. It uses HTTP Basic authentication with
the teacher username and password. In the interactive docs, choose
**Authorize** and enter those credentials.

| Method | URL | Description |
| --- | --- | --- |
| `GET` | `/api/v1/students` | List students; supports `search`, `limit`, and `offset` query parameters |
| `POST` | `/api/v1/students` | Register a student |
| `GET` | `/api/v1/students/{student_id}` | Get a student, their marks, and grade summary |
| `PATCH` | `/api/v1/students/{student_id}` | Update supplied student fields |
| `DELETE` | `/api/v1/students/{student_id}` | Delete the student and their marks |
| `GET` | `/api/v1/students/{student_id}/marks` | List that student's marks |
| `POST` | `/api/v1/students/{student_id}/marks` | Enter an assignment, test, or exam mark |
| `PATCH` | `/api/v1/students/{student_id}/marks/{mark_id}` | Update a mark |
| `DELETE` | `/api/v1/students/{student_id}/marks/{mark_id}` | Delete a mark |

Interactive API documentation is available at `/docs` (Swagger UI) and
`/redoc`; the OpenAPI document is at `/openapi.json`. Endpoints are grouped
under the **Students** and **Marks** tags.

### Register a student

Send `POST /api/v1/students` with a JSON body:

```json
{
  "full_name": "Alex Morgan",
  "grade": "Grade 10",
  "student_number": "STU-101"
}
```

The `student_number` can be omitted or set to `null`. Names and grades are
trimmed and must not be blank.

### Enter a mark

After registering a student, send `POST
/api/v1/students/{student_id}/marks`:

```json
{
  "category": "Assignment",
  "title": "Fractions worksheet",
  "score": 18,
  "max_score": 20,
  "assessed_on": "2026-10-10"
}
```

Allowed categories are exactly `Assignment`, `Test`, and `Exam`. Scores must be
finite numbers, at least zero, and no greater than a positive maximum score.
Dates use the ISO format `YYYY-MM-DD`. `PATCH` requests accept only the fields
being changed.

The API schemas in [app/schemas.py](../app/schemas.py) validate request and
response data. [app/models.py](../app/models.py) maps SQLite rows to typed
`Student` and `Mark` records. The router modules under
[app/api/routers/](../app/api/routers/) define endpoint URLs and tags.

Typical error responses include:

- `401 Unauthorized` for missing or incorrect teacher credentials.
- `404 Not Found` for an unknown student or a mark that does not belong to the
  requested student.
- `409 Conflict` when a student number is already in use.
- `422 Unprocessable Entity` for invalid input, such as an out-of-range score.

## Database and Excel

[app/database.py](../app/database.py) creates these SQLite tables the first time
the app starts:

- **teachers** — username and password salt/hash for teacher sign-in.
- **students** — name, grade/class, optional unique student number, and creation
  timestamp.
- **assessments** — student, category, title, score, maximum score, date, and
  creation timestamp.

Each assessment references a student. Deleting a student removes their related
assessments through SQLite's foreign-key cascade.

By default, the database lives at `data/student_marks.db`. Set `DATABASE_PATH`
to a different full path before startup to change its location.

The `/export.xlsx` website route builds an `.xlsx` workbook from the database
using openpyxl. It contains:

- **Student Summary** — student details, category averages, overall mark, and
  assessment count.
- **Assessments** — one row per mark with category, score, possible score,
  percentage, and date.

Names and titles beginning with spreadsheet formula characters are escaped in
the workbook export to prevent them being interpreted as formulas.

## Authentication and deployment notes

The first application startup initializes the database and creates a teacher
account if none exists. Set `INITIAL_TEACHER_USERNAME` and
`INITIAL_TEACHER_PASSWORD` to choose the initial credentials. The password must
have at least 12 characters. If no initial password is configured, the app
generates one and logs it once at startup; change it in **Settings** after
signing in. Existing teacher accounts are not replaced on later startups.

Teacher passwords are stored as salted PBKDF2-HMAC-SHA256 hashes; plaintext
passwords are not stored. The browser session is signed with `SESSION_SECRET`.
Set a private, stable secret for real use; otherwise the app generates a
temporary secret for the current process. Set `COOKIE_SECURE=true` when
serving through HTTPS.

The API uses HTTP Basic credentials on every request. Use HTTPS for connections
outside local development so credentials are encrypted in transit. The current
app has a single teacher account and does not implement teacher roles,
self-service account registration, password recovery, or per-teacher data
separation.

## Install and run with uv

Requires Python 3.10 or newer and `uv`.

From the project root in PowerShell:

```powershell
uv sync
$env:INITIAL_TEACHER_PASSWORD = "choose-a-password-at-least-12-chars"
$env:SESSION_SECRET = (uv run python -c "import secrets; print(secrets.token_urlsafe(32))")
uv run fastapi dev main.py
```

Open <http://127.0.0.1:8000>. Alternatively, start the server with:

```powershell
uv run uvicorn app.main:app --reload
```

`uv sync` reads [pyproject.toml](../pyproject.toml) and
[uv.lock](../uv.lock), installs the pinned project dependencies into the
project's virtual environment, and keeps the environment consistent with the
lockfile.

## Tests

Run the suite from the project root:

```powershell
uv run python -m unittest discover -s tests
```

Tests cover mark calculations, SQLite persistence and cascading deletes,
teacher sign-in and password updates, browser workflows, API authentication and
validation, reports, and Excel export. Test databases are temporary and do not
overwrite the working database.

## How the project was created

The implementation follows the provided Student Mark System and system-design
documents. Those documents describe teacher access, student details, assignment
and exam results, database persistence, reports, and a mark-entry screen. The
application turns those requirements into a working browser app and API:

1. The folder's design documents were read to identify the users and workflows.
2. A FastAPI/Jinja2 website and SQLite tables were created for teachers,
   students, and assessments.
3. Mark validation and shared grade-summary calculations were implemented so
   the dashboard, student pages, reports, and API use consistent scoring.
4. Teacher sessions, password hashing, and CSRF protection were added for
   browser forms.
5. A versioned JSON API was organized into student and mark routers with
   validated Pydantic schemas, typed database record models, authentication,
   and OpenAPI tags.
6. An Excel workbook export and tests for both website and API workflows were
   added.
7. The root `main.py` entry point was added after FastAPI's development command
   reported that it could not find `Edustat\main.py`.
8. `uv` became the project and dependency manager; setup and run instructions
   were updated for `uv sync` and `uv run`.

The supplied architecture diagram mentions other server/database technologies;
the running implementation uses FastAPI and SQLite, as requested for this
project. This guide describes the code that is currently implemented.
