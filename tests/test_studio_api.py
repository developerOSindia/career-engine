"""
Unit tests for CareerEngine Web Studio REST APIs.
"""

import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock

from core.studio.server import StudioRequestHandler

class DummyStudioHandler(StudioRequestHandler):
    def __init__(self):
        self.wfile = BytesIO()
        self.headers = {}
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

if __name__ == "__main__":
    unittest.main()
