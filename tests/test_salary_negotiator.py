"""
Unit tests for SalaryNegotiator and CompensationReport.
"""

import unittest
from core.salary_negotiator import SalaryNegotiator, CompensationReport, NegotiationStrategy


class TestSalaryNegotiator(unittest.TestCase):
    def setUp(self):
        self.mock_profile = {
            "personal_info": {
                "full_name": "Kalash Jindal"
            },
            "work_summary": {
                "current_title": "Senior Data Engineer",
                "total_years_experience": 5,
                "current_salary_inr_lpa": 30,
                "expected_salary_inr_lpa": 40
            }
        }
        self.negotiator = SalaryNegotiator(profile_data=self.mock_profile)

    def test_seniority_inference(self):
        self.assertEqual(self.negotiator.infer_seniority("Director of Engineering", 12), "principal_director")
        self.assertEqual(self.negotiator.infer_seniority("Staff Software Engineer", 8), "staff_lead")
        self.assertEqual(self.negotiator.infer_seniority("Senior Data Engineer", 5), "senior")
        self.assertEqual(self.negotiator.infer_seniority("Junior Developer", 1), "junior")

    def test_market_benchmark_retrieval(self):
        b_inr = self.negotiator.get_market_benchmark("senior", "india_inr_lpa")
        self.assertIn("p50", b_inr)
        self.assertIn("p75", b_inr)
        self.assertGreaterEqual(b_inr["p75"], b_inr["p50"])

        b_us = self.negotiator.get_market_benchmark("staff_lead", "us_remote_usd_k")
        self.assertGreater(b_us["p75"], 200)

    def test_negotiation_plan_generation(self):
        report = self.negotiator.analyze_and_plan(
            company="Razorpay",
            title="Senior Data Engineer",
            offered_comp=38.0,
            current_comp=30.0,
            market_region="india_inr_lpa"
        )
        self.assertIsInstance(report, CompensationReport)
        self.assertEqual(report.target_company, "Razorpay")
        self.assertEqual(len(report.strategies), 3)

        strat_counter = report.strategies[0]
        self.assertIn("Razorpay", strat_counter.email_body)
        self.assertIn("Kalash Jindal", strat_counter.email_body)
        self.assertGreater(len(strat_counter.phone_talking_points), 0)

    def test_to_dict_serialization(self):
        report = self.negotiator.analyze_and_plan(
            company="Coinbase",
            title="Senior Backend Engineer",
            offered_comp=180.0,
            current_comp=140.0,
            market_region="us_remote_usd_k",
            competing_offer="an offer at $210k from Kraken"
        )
        d = report.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["target_company"], "Coinbase")
        self.assertIn("market_percentiles", d)
        self.assertEqual(len(d["strategies"]), 3)


if __name__ == "__main__":
    unittest.main()
