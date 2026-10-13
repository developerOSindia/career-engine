"""
Unit tests for CareerEngine Profile Scoring & ATS Audit Engine.
"""

import unittest
from core.profile_scorer import ProfileScorer, ProfileScoreReport

class TestProfileScorer(unittest.TestCase):

    def setUp(self):
        self.sample_profile = {
            "personal_info": {
                "first_name": "Test",
                "last_name": "Candidate",
                "full_name": "Test Candidate",
                "email": "candidate@example.com",
                "full_phone": "+919876543210",
                "location": "Bengaluru, India",
                "linkedin_url": "https://www.linkedin.com/in/test-candidate/",
                "github_url": "https://github.com/test-candidate"
            },
            "work_summary": {
                "current_title": "Senior Data Engineer",
                "current_company": "Tech Corp",
                "total_years_experience": 5,
                "notice_period_days": 30,
                "current_salary_inr_lpa": "28",
                "expected_salary_inr_lpa": "38"
            },
            "experience_history": [
                {
                    "company": "Tech Corp",
                    "title": "Senior Data Engineer",
                    "details": "Engineered PySpark pipelines processing 50M+ events daily with 99.9% uptime."
                }
            ],
            "skills_years_experience": {
                "python": 5,
                "sql": 5,
                "pyspark": 5,
                "databricks": 4,
                "aws": 4,
                "docker": 3,
                "airflow": 4,
                "delta lake": 3,
                "kafka": 2,
                "snowflake": 2,
                "ci/cd": 3,
                "git": 5,
                "postgresql": 4,
                "rest apis": 3,
                "spark": 4
            },
            "screening_defaults": {
                "legally_authorized": True,
                "require_sponsorship": False,
                "willing_to_relocate": True,
                "open_to_remote": True,
                "is_notice_negotiable": True
            },
            "custom_answers": {
                f"q_{i}": f"answer_{i}" for i in range(22)
            }
        }

    def test_evaluate_complete_profile(self):
        scorer = ProfileScorer(profile_data=self.sample_profile)
        report = scorer.evaluate()

        self.assertIsInstance(report, ProfileScoreReport)
        self.assertGreaterEqual(report.total_score, 80)
        self.assertIn(report.letter_grade, ["A+", "A"])
        self.assertIn("contact", report.categories)
        self.assertIn("experience", report.categories)
        self.assertIn("skills", report.categories)
        self.assertIn("resumes", report.categories)
        self.assertIn("screening", report.categories)

        # Check category percentages
        self.assertEqual(report.categories["contact"]["percentage"], 100.0)
        self.assertEqual(report.categories["experience"]["percentage"], 100.0)
        self.assertEqual(report.categories["skills"]["percentage"], 100.0)
        self.assertEqual(report.categories["screening"]["percentage"], 100.0)

        # Role readiness
        self.assertIn("_DE", report.role_readiness)
        self.assertGreater(report.role_readiness["_DE"]["readiness_percent"], 70)

        # JSON serialization
        d = report.to_dict()
        self.assertEqual(d["total_score"], report.total_score)
        self.assertEqual(d["letter_grade"], report.letter_grade)

    def test_evaluate_sparse_profile(self):
        sparse_profile = {
            "personal_info": {"full_name": ""},
            "work_summary": {},
            "skills_years_experience": {},
            "screening_defaults": {},
            "custom_answers": {}
        }
        scorer = ProfileScorer(profile_data=sparse_profile)
        report = scorer.evaluate()

        self.assertLess(report.total_score, 50)
        self.assertEqual(report.letter_grade, "C")
        self.assertGreater(len(report.critical_gaps), 0)
        self.assertGreater(len(report.actionable_recommendations), 0)

    def test_cli_scorecard_formatting(self):
        scorer = ProfileScorer(profile_data=self.sample_profile)
        report = scorer.evaluate()
        scorecard = scorer.format_cli_scorecard(report)

        self.assertIn("CAREERENGINE CANDIDATE PROFILE AUDIT", scorecard)
        self.assertIn(str(report.total_score), scorecard)
        self.assertIn("Data Engineering", scorecard)
        self.assertIn("Candidate Strengths & Badges", scorecard)

if __name__ == "__main__":
    unittest.main()
