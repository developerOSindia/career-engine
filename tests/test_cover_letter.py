"""
Unit tests for CoverLetterGenerator and CoverLetterKit.
"""

import os
import unittest
from core.cover_letter import CoverLetterGenerator, CoverLetterKit


class TestCoverLetterGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_profile = {
            "personal_info": {
                "full_name": "Kalash Jindal",
                "email": "kalash@example.com"
            },
            "work_summary": {
                "current_title": "Senior Data Engineer",
                "total_years_experience": 5,
                "top_skills": ["Python", "SQL", "PySpark", "Databricks", "AWS", "Airflow"],
                "notice_period_days": 30
            }
        }
        self.generator = CoverLetterGenerator(profile_data=self.mock_profile)

    def test_startup_cover_letter_generation(self):
        kit = self.generator.generate(
            company="Brex",
            title="Senior Platform Engineer",
            style="startup"
        )
        self.assertEqual(kit.target_company, "Brex")
        self.assertEqual(kit.target_title, "Senior Platform Engineer")
        self.assertEqual(kit.style, "startup")
        self.assertIn("Kalash Jindal", kit.full_text)
        self.assertIn("Brex", kit.full_text)
        self.assertGreater(len(kit.core_value_bullets), 0)
        self.assertIn("30-day notice period", kit.full_text)

    def test_enterprise_cover_letter_generation(self):
        kit = self.generator.generate(
            company="Goldman Sachs",
            title="Vice President - Distributed Systems",
            style="enterprise",
            hiring_manager_name="Marcus Vance"
        )
        self.assertEqual(kit.style, "enterprise")
        self.assertIn("Marcus Vance", kit.salutation)
        self.assertIn("enterprise-grade distributed architectures", kit.full_markdown.lower())
        self.assertIn("Goldman Sachs", kit.full_markdown)

    def test_concise_cover_letter_generation(self):
        kit = self.generator.generate(
            company="Vercel",
            title="Senior Backend Engineer",
            style="concise"
        )
        self.assertEqual(kit.style, "concise")
        self.assertIn("Key Highlights", kit.full_text)
        self.assertIn("Vercel", kit.full_text)

    def test_to_dict_serialization(self):
        kit = self.generator.generate(
            company="Stripe",
            title="Staff Infrastructure Engineer"
        )
        d = kit.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["target_company"], "Stripe")
        self.assertIn("full_markdown", d)
        self.assertIn("skills_matched", d)


if __name__ == "__main__":
    unittest.main()
