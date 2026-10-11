import tempfile
import unittest
from pathlib import Path

from app import database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temp_dir.name) / "test.db"
        database.initialize_database()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_student_marks_persist_and_deleting_student_cascades(self):
        with database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO students (full_name, grade) VALUES (?, ?)",
                ("Alex Morgan", "Grade 10"),
            )
            student_id = cursor.lastrowid
            connection.execute(
                """
                INSERT INTO assessments
                    (student_id, category, title, score, max_score, assessed_on)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (student_id, "Test", "Unit test", 8, 10, "2026-10-10"),
            )

        with database.connect() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM assessments WHERE student_id = ?",
                    (student_id,),
                ).fetchone()[0],
                1,
            )
            connection.execute("DELETE FROM students WHERE id = ?", (student_id,))

        with database.connect() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM assessments WHERE student_id = ?",
                    (student_id,),
                ).fetchone()[0],
                0,
            )


if __name__ == "__main__":
    unittest.main()
