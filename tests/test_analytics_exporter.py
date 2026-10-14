import os
import unittest
import tempfile
import sqlite3
from core.analytics_exporter import AnalyticsExporter

class TestAnalyticsExporter(unittest.TestCase):
    def setUp(self):
        # Create a temporary SQLite database with mock applications
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                title TEXT,
                company TEXT,
                location TEXT,
                platform TEXT,
                workplace_type TEXT,
                hiring_manager_name TEXT,
                hiring_manager_url TEXT,
                key_skills TEXT,
                job_url TEXT,
                status TEXT,
                notes TEXT,
                screenshot_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Insert test records
        c.execute("INSERT INTO applications (job_id, title, company, platform, status) VALUES ('1', 'Data Engineer', 'Meta', 'linkedin', 'applied')")
        c.execute("INSERT INTO applications (job_id, title, company, platform, status) VALUES ('2', 'Software Engineer', 'Google', 'naukri', 'applied')")
        c.execute("INSERT INTO applications (job_id, title, company, platform, status) VALUES ('3', 'DevOps Lead', 'Netflix', 'indeed', 'dry_run_completed')")
        c.execute("INSERT INTO applications (job_id, title, company, platform, status) VALUES ('4', 'AI Engineer', 'OpenAI', 'glassdoor', 'skipped')")
        c.execute("INSERT INTO applications (job_id, title, company, platform, status) VALUES ('5', 'ML Engineer', 'Apple', 'foundit', 'applied')")
        conn.commit()
        conn.close()

        self.exporter = AnalyticsExporter(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_all_applications(self):
        apps = self.exporter.get_all_applications()
        self.assertEqual(len(apps), 5)
        titles = [a["title"] for a in apps]
        self.assertIn("Data Engineer", titles)
        self.assertIn("ML Engineer", titles)

    def test_get_analytics_summary(self):
        summary = self.exporter.get_analytics_summary()
        self.assertEqual(summary["total_applications"], 5)
        self.assertEqual(summary["applied_count"], 3)
        self.assertEqual(summary["dry_run_count"], 1)
        # (3 applied + 1 dry run) / 5 = 80.0%
        self.assertEqual(summary["conversion_rate_percent"], 80.0)

        # Platforms
        platforms = summary["platform_breakdown"]
        self.assertEqual(platforms.get("linkedin"), 1)
        self.assertEqual(platforms.get("naukri"), 1)
        self.assertEqual(platforms.get("indeed"), 1)
        self.assertEqual(platforms.get("glassdoor"), 1)
        self.assertEqual(platforms.get("foundit"), 1)

    def test_export_csv_and_json(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f_csv:
            csv_path = f_csv.name
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f_json:
            json_path = f_json.name

        try:
            res_csv = self.exporter.export_to_csv(csv_path)
            self.assertEqual(res_csv["total_exported"], 5)
            self.assertTrue(os.path.exists(csv_path))
            with open(csv_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("job_id,title,company", content)
                self.assertIn("Data Engineer", content)

            res_json = self.exporter.export_to_json(json_path)
            self.assertEqual(res_json["total_exported"], 5)
            self.assertTrue(os.path.exists(json_path))
            with open(json_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn('"company": "Meta"', content)
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
            if os.path.exists(json_path):
                os.remove(json_path)

if __name__ == "__main__":
    unittest.main()
