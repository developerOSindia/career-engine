"""
Unit tests for Smart Cross-Platform Deduplication module.
"""

import unittest
from core.smart_dedup import SmartDeduplicator, smart_deduplicator


class TestSmartDeduplicator(unittest.TestCase):
    def setUp(self):
        self.dedup = SmartDeduplicator()

    def test_clean_company_name(self):
        self.assertEqual(self.dedup.clean_company_name("Google LLC"), "google")
        self.assertEqual(self.dedup.clean_company_name("Razorpay Technologies Inc."), "razorpay")
        self.assertEqual(self.dedup.clean_company_name("Uber Technologies Private Limited"), "uber")
        self.assertEqual(self.dedup.clean_company_name("Stripe, Inc."), "stripe")

    def test_clean_job_title(self):
        cleaned = self.dedup.clean_job_title("Senior Software Engineer - Backend (Immediate Joiner) [Urgent]")
        self.assertIn("senior", cleaned)
        self.assertIn("software", cleaned)
        self.assertIn("engineer", cleaned)
        self.assertNotIn("immediate joiner", cleaned)
        self.assertNotIn("urgent", cleaned)

    def test_exact_and_fuzzy_matches(self):
        # Case 1: Same role, same company on different platforms
        match1 = self.dedup.is_match(
            title_a="Senior Backend Engineer",
            company_a="Stripe Inc",
            title_b="Senior Backend Engineer - Core Payments",
            company_b="Stripe LLC"
        )
        self.assertTrue(match1)

        # Case 2: Different companies should NOT match
        match2 = self.dedup.is_match(
            title_a="Senior Backend Engineer",
            company_a="Stripe",
            title_b="Senior Backend Engineer",
            company_b="Airbnb"
        )
        self.assertFalse(match2)

        # Case 3: Completely different titles at same company should NOT match
        match3 = self.dedup.is_match(
            title_a="Product Manager",
            company_a="Google",
            title_b="Staff Site Reliability Engineer",
            company_b="Google Inc"
        )
        self.assertFalse(match3)

    def test_similarity_score_bounds(self):
        score = self.dedup.title_similarity("Software Engineer", "Software Engineer")
        self.assertGreaterEqual(score, 0.95)

        score_diff = self.dedup.title_similarity("Data Analyst", "VP Engineering")
        self.assertLess(score_diff, 0.3)


if __name__ == "__main__":
    unittest.main()
