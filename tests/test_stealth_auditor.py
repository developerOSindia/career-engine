"""
Unit tests for StealthAuditor and StealthAuditReport.
"""

import unittest
from core.stealth_auditor import StealthAuditor, StealthAuditReport


class TestStealthAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = StealthAuditor()

    def test_run_audit_structure(self):
        report = self.auditor.run_audit()
        self.assertIsInstance(report, StealthAuditReport)
        self.assertGreaterEqual(report.safety_score, 0)
        self.assertLessEqual(report.safety_score, 100)
        self.assertIn(report.risk_level, ["SAFE (LOW RISK)", "MODERATE RISK", "HIGH RISK"])
        self.assertGreater(len(report.checks), 0)

    def test_audit_checks_properties(self):
        report = self.auditor.run_audit()
        categories = {c.category for c in report.checks}
        self.assertIn("browser", categories)
        self.assertIn("pacing", categories)
        self.assertIn("quota", categories)
        self.assertIn("session", categories)

        for c in report.checks:
            self.assertIn(c.status, ["PASS", "WARN", "FAIL"])
            self.assertGreaterEqual(c.score_points, 0)
            self.assertGreater(c.max_points, 0)
            self.assertTrue(len(c.finding) > 0)

    def test_to_dict_serialization(self):
        report = self.auditor.run_audit()
        d = report.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("safety_score", d)
        self.assertIn("risk_level", d)
        self.assertIn("checks", d)
        self.assertIn("platform_sessions", d)


if __name__ == "__main__":
    unittest.main()
