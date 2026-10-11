from collections import defaultdict

from app.database import connect


CATEGORIES = ("Assignment", "Test", "Exam")


def summarize_assessments(assessments):
    category_percentages = defaultdict(list)
    earned = 0.0
    possible = 0.0

    for assessment in assessments:
        score = float(assessment["score"])
        max_score = float(assessment["max_score"])
        earned += score
        possible += max_score
        category_percentages[assessment["category"]].append(score / max_score * 100)

    category_averages = {
        category: (
            sum(category_percentages[category]) / len(category_percentages[category])
            if category_percentages[category]
            else None
        )
        for category in CATEGORIES
    }
    overall = earned / possible * 100 if possible else None
    return {
        "categories": category_averages,
        "overall": overall,
        "earned": earned,
        "possible": possible,
        "assessment_count": len(assessments),
    }


def student_summaries(search=""):
    with connect() as connection:
        if search:
            pattern = f"%{search}%"
            students = connection.execute(
                """
                SELECT * FROM students
                WHERE full_name LIKE ? OR student_number LIKE ? OR grade LIKE ?
                ORDER BY full_name COLLATE NOCASE
                """,
                (pattern, pattern, pattern),
            ).fetchall()
        else:
            students = connection.execute(
                "SELECT * FROM students ORDER BY full_name COLLATE NOCASE"
            ).fetchall()

        assessments = connection.execute(
            """
            SELECT a.* FROM assessments a
            JOIN students s ON s.id = a.student_id
            ORDER BY a.assessed_on DESC, a.id DESC
            """
        ).fetchall()

    grouped = defaultdict(list)
    for assessment in assessments:
        grouped[assessment["student_id"]].append(assessment)

    result = []
    for student in students:
        record = dict(student)
        record["summary"] = summarize_assessments(grouped[student["id"]])
        result.append(record)
    return result
