import unittest
from platforms.indeed.connector import IndeedPlatform
from platforms.glassdoor.connector import GlassdoorPlatform
from platforms.foundit.connector import FounditPlatform
from platforms.wellfound.connector import WellfoundPlatform
from platforms.instahyre.connector import InstahyrePlatform
from core.models import JobPosting

class TestPlatformConnectors(unittest.TestCase):
    def test_indeed_platform_init(self):
        indeed = IndeedPlatform(dry_run=True, limit=5, interactive=False)
        self.assertEqual(indeed.name, "indeed")
        self.assertTrue(indeed.dry_run)
        self.assertEqual(indeed.limit, 5)
        self.assertFalse(indeed.interactive)
        self.assertEqual(indeed.base_url, "https://www.indeed.com")

    def test_glassdoor_platform_init(self):
        gd = GlassdoorPlatform(dry_run=True, limit=10, interactive=True)
        self.assertEqual(gd.name, "glassdoor")
        self.assertTrue(gd.dry_run)
        self.assertEqual(gd.limit, 10)
        self.assertTrue(gd.interactive)
        self.assertEqual(gd.base_url, "https://www.glassdoor.com")

    def test_foundit_platform_init(self):
        foundit = FounditPlatform(dry_run=True, limit=7, interactive=False)
        self.assertEqual(foundit.name, "foundit")
        self.assertTrue(foundit.dry_run)
        self.assertEqual(foundit.limit, 7)
        self.assertEqual(foundit.base_url, "https://www.foundit.in")

    def test_wellfound_platform_init(self):
        wf = WellfoundPlatform(dry_run=True, limit=3)
        self.assertEqual(wf.name, "wellfound")
        self.assertTrue(wf.dry_run)

    def test_instahyre_platform_init(self):
        ih = InstahyrePlatform(dry_run=True, limit=4)
        self.assertEqual(ih.name, "instahyre")
        self.assertTrue(ih.dry_run)

    def test_job_posting_model_compatibility(self):
        job = JobPosting(
            job_id="test_ind_123",
            title="Senior Python Architect",
            company="Global Tech",
            location="Bangalore",
            url="https://in.indeed.com/viewjob?jk=test_ind_123"
        )
        self.assertEqual(job.job_id, "test_ind_123")
        self.assertEqual(job.platform, "linkedin")  # default model platform

if __name__ == "__main__":
    unittest.main()
