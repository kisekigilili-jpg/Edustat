import unittest

from app.grades import summarize_assessments


class GradeSummaryTests(unittest.TestCase):
    def test_categories_and_overall_use_documented_calculations(self):
        assessments = [
            {"category": "Assignment", "score": 8, "max_score": 10},
            {"category": "Assignment", "score": 15, "max_score": 20},
            {"category": "Test", "score": 45, "max_score": 50},
            {"category": "Exam", "score": 60, "max_score": 100},
        ]

        result = summarize_assessments(assessments)

        self.assertAlmostEqual(result["categories"]["Assignment"], 77.5)
        self.assertAlmostEqual(result["categories"]["Test"], 90)
        self.assertAlmostEqual(result["categories"]["Exam"], 60)
        self.assertAlmostEqual(result["overall"], 128 / 180 * 100)
        self.assertEqual(result["assessment_count"], 4)

    def test_empty_assessments_have_no_percentage(self):
        result = summarize_assessments([])

        self.assertIsNone(result["overall"])
        self.assertEqual(result["categories"], {
            "Assignment": None,
            "Test": None,
            "Exam": None,
        })
        self.assertEqual(result["assessment_count"], 0)

    def test_only_recorded_categories_contribute(self):
        result = summarize_assessments(
            [{"category": "Exam", "score": 18, "max_score": 20}]
        )

        self.assertIsNone(result["categories"]["Assignment"])
        self.assertIsNone(result["categories"]["Test"])
        self.assertEqual(result["categories"]["Exam"], 90)
        self.assertEqual(result["overall"], 90)


if __name__ == "__main__":
    unittest.main()
