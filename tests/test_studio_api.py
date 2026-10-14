"""
Unit tests for CareerEngine Web Studio REST APIs.
"""

import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock

from core.studio.server import StudioRequestHandler

class DummyStudioHandler(StudioRequestHandler):
    def __init__(self, method="GET", path="/", body_bytes=b""):
        self.wfile = BytesIO()
        self.rfile = BytesIO(body_bytes)
        self.path = path
        self.command = method
        self.headers = {"Content-Length": str(len(body_bytes))}
        self.status = 200
        self.response_headers = {}

    def send_response(self, status):
        self.status = status

    def send_header(self, k, v):
        self.response_headers[k] = v

    def end_headers(self):
        pass


class TestStudioApi(unittest.TestCase):

    def test_api_profile_score(self):
        handler = DummyStudioHandler()
        handler.handle_get_profile_score()

        self.assertEqual(handler.status, 200)
        self.assertEqual(handler.response_headers.get("Content-Type"), "application/json; charset=utf-8")
        
        body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("total_score", body)
        self.assertIn("letter_grade", body)
        self.assertIn("categories", body)
        self.assertIn("role_readiness", body)
        self.assertIn("resumes_detected", body)
        self.assertGreaterEqual(body["total_score"], 0)
        self.assertLessEqual(body["total_score"], 100)

    def test_api_dedup_audit(self):
        handler = DummyStudioHandler("GET", "/api/dedup/audit")
        handler.do_GET()

        self.assertEqual(handler.status, 200)
        body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("total_duplicate_groups", body)
        self.assertIn("groups", body)
        self.assertIsInstance(body["groups"], list)

    def test_api_outreach_generate(self):
        payload = json.dumps({
            "company": "Stripe",
            "job_title": "Senior Backend Engineer",
            "target_name": "Patrick Collison"
        }).encode("utf-8")
        handler = DummyStudioHandler("POST", "/api/outreach/generate", payload)
        handler.do_POST()

        self.assertEqual(handler.status, 200)
        body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(body["company"], "Stripe")
        self.assertIn("email_frameworks", body)
        self.assertEqual(len(body["email_frameworks"]), 3)

    def test_api_interview_prep(self):
        payload = json.dumps({
            "company": "Databricks",
            "job_title": "Senior Solutions Architect",
            "job_description": "Apache Spark, Delta Lake, cloud distributed systems."
        }).encode("utf-8")
        handler = DummyStudioHandler("POST", "/api/interview/prep", payload)
        handler.do_POST()

        self.assertEqual(handler.status, 200)
        body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(body["company"], "Databricks")
        self.assertIn("system_design_challenge", body)
        self.assertIn("technical_drills", body)
        self.assertIn("behavioral_star_stories", body)


if __name__ == "__main__":
    unittest.main()
