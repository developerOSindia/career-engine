"""
Unit tests for Recruiter Cold Outreach and Discovery module.
"""

import unittest
from core.cold_outreach import ColdOutreachSynthesizer, cold_outreach_synthesizer


class TestColdOutreachSynthesizer(unittest.TestCase):
    def setUp(self):
        self.synthesizer = ColdOutreachSynthesizer()

    def test_domain_prediction(self):
        self.assertEqual(self.synthesizer.predict_company_domain("Razorpay"), "razorpay.com")
        self.assertEqual(self.synthesizer.predict_company_domain("Stripe Inc"), "stripe.com")
        self.assertEqual(self.synthesizer.predict_company_domain("Google Cloud LLC"), "google.com")

    def test_email_permutations_generation(self):
        emails = self.synthesizer.generate_email_permutations("Sarah Jenkins", "stripe.com")
        self.assertIn("sarah.jenkins@stripe.com", emails)
        self.assertIn("sjenkins@stripe.com", emails)
        self.assertIn("sarah@stripe.com", emails)
        self.assertIn("jenkins@stripe.com", emails)

    def test_talent_discovery_queries(self):
        queries = self.synthesizer.generate_talent_discovery_queries("Uber", "Senior Backend Engineer")
        self.assertGreaterEqual(len(queries), 3)
        channels = [q["channel"] for q in queries]
        self.assertIn("Google X-Ray (LinkedIn)", channels)
        self.assertIn("LinkedIn Talent Search", channels)

    def test_generate_outreach_kit(self):
        kit = self.synthesizer.generate_outreach_kit(
            company="Razorpay",
            job_title="Senior Data Engineer",
            target_name="Rohit Sharma"
        )
        self.assertEqual(kit.company, "Razorpay")
        self.assertEqual(kit.target_role, "Senior Data Engineer")
        self.assertEqual(len(kit.email_frameworks), 3)

        for fw in kit.email_frameworks:
            self.assertIn("name", fw)
            self.assertIn("subject", fw)
            self.assertIn("body", fw)
            self.assertIn("mailto_link", fw)
            self.assertTrue(fw["mailto_link"].startswith("mailto:"))


if __name__ == "__main__":
    unittest.main()
