"""
Unit tests for Technical Interview Preparation and STAR Simulator module.
"""

import unittest
from core.interview_prep import InterviewPrepSimulator, interview_prep_simulator


class TestInterviewPrepSimulator(unittest.TestCase):
    def setUp(self):
        self.simulator = InterviewPrepSimulator()

    def test_generate_prep_kit_heuristic(self):
        kit = self.simulator.generate_prep_kit(
            job_title="Senior Data Engineer",
            company="Swiggy",
            job_description="Looking for an experienced Data Engineer to build high-throughput real-time Kafka pipelines and Spark batch workloads with Snowflake."
        )
        self.assertEqual(kit.job_title, "Senior Data Engineer")
        self.assertEqual(kit.company, "Swiggy")
        self.assertTrue(bool(kit.role_focus_summary))

        # Check System Design challenge
        sd = kit.system_design_challenge
        self.assertIn("title", sd)
        self.assertIn("problem_statement", sd)
        self.assertGreaterEqual(len(sd.get("scale_requirements", [])), 2)
        self.assertGreaterEqual(len(sd.get("key_tradeoffs", [])), 2)

        # Check Technical drills
        self.assertGreaterEqual(len(kit.technical_drills), 4)
        for drill in kit.technical_drills:
            self.assertIn("question", drill)
            self.assertIn("ideal_answer_rubric", drill)

        # Check STAR stories
        self.assertGreaterEqual(len(kit.behavioral_star_stories), 3)
        for star in kit.behavioral_star_stories:
            self.assertIn("situation", star)
            self.assertIn("task", star)
            self.assertIn("action", star)
            self.assertIn("result", star)

        # Check Reverse Interview Questions
        self.assertGreaterEqual(len(kit.reverse_interview_questions), 3)

    def test_prep_kit_serialization(self):
        kit = self.simulator.generate_prep_kit(
            job_title="Staff Backend Engineer",
            company="Zepto",
            job_description="Microservices in Go and Python with Redis caching and PostgreSQL."
        )
        d = kit.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("system_design_challenge", d)
        self.assertIn("technical_drills", d)
        self.assertIn("behavioral_star_stories", d)


if __name__ == "__main__":
    unittest.main()
