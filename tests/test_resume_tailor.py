import unittest
from core.resume_tailor import ResumeTailor, ResumeTailorReport

class TestResumeTailor(unittest.TestCase):
    def setUp(self):
        self.tailor = ResumeTailor()

    def test_tailor_for_job_keyword_extraction_and_scoring(self):
        jd = """
        We are seeking a Senior Data Engineer to design high-throughput ETL pipelines.
        Requirements:
        - Deep proficiency in Python, PySpark, and SQL
        - Experience building lakehouse systems with Delta Lake and Databricks
        - Strong background in AWS (S3, EMR, Redshift) and Airflow
        - Familiarity with Kafka and Docker
        """
        report = self.tailor.tailor_for_job(
            job_title="Senior Data Engineer",
            company="Databricks",
            job_description=jd
        )

        self.assertIsInstance(report, ResumeTailorReport)
        self.assertEqual(report.job_title, "Senior Data Engineer")
        self.assertEqual(report.company, "Databricks")
        self.assertIn("DE", report.target_role_tag)
        self.assertTrue(report.recommended_resume_file.endswith(".pdf"))

        # Baseline score should be valid integer between 0 and 100
        self.assertGreaterEqual(report.baseline_ats_score, 40)
        self.assertLessEqual(report.baseline_ats_score, 100)

        # Optimized score should be >= baseline score
        self.assertGreaterEqual(report.optimized_ats_score, report.baseline_ats_score)

        # Matched skills
        matched_str = " ".join(report.matched_skills).lower()
        self.assertTrue("python" in matched_str or "sql" in matched_str)

        # Tailored bullets
        self.assertGreaterEqual(len(report.tailored_achievement_bullets), 2)
        for bullet in report.tailored_achievement_bullets:
            self.assertIsInstance(bullet, str)
            self.assertGreater(len(bullet), 30)

        # Recruiter pitch note
        self.assertIn("Databricks", report.bespoke_pitch_note)

    def test_tailor_to_dict_serialization(self):
        report = self.tailor.tailor_for_job(
            job_title="Backend Developer",
            company="Acme Corp",
            job_description="Python, FastAPI, Postgres, Kubernetes"
        )
        data = report.to_dict()
        self.assertIsInstance(data, dict)
        self.assertIn("baseline_ats_score", data)
        self.assertIn("optimized_ats_score", data)
        self.assertIn("tailored_achievement_bullets", data)
        self.assertIn("bespoke_pitch_note", data)

if __name__ == "__main__":
    unittest.main()
