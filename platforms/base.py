"""
Base platform contract for job application bots.
All job board implementations (LinkedIn, Naukri, Wellfound, Indeed) derive from BasePlatform.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.models import JobPosting, ApplicationRecord
from core.browser_engine import BrowserEngine
from core.tracker import ApplicationTracker

class BasePlatform(ABC):
    """Abstract base class for all job board platforms."""
    def __init__(
        self,
        name: str,
        engine: BrowserEngine,
        tracker: ApplicationTracker,
        dry_run: bool = True,
        limit: int = 10,
        interactive: bool = False
    ):
        self.name = name
        self.engine = engine
        self.tracker = tracker
        self.dry_run = dry_run
        self.limit = limit
        self.interactive = interactive
        self.page = None

    @abstractmethod
    async def authenticate_or_check_session(self) -> bool:
        """Verifies if the browser session is logged in to the platform."""
        pass

    @abstractmethod
    async def search_jobs(
        self,
        keyword: str,
        location: str,
        remote: bool = False,
        page_num: int = 1
    ) -> List[JobPosting]:
        """Discovers jobs matching search criteria."""
        pass

    @abstractmethod
    async def apply_to_job(self, job: JobPosting) -> bool:
        """Executes the complete application flow for a single job."""
        pass

    @abstractmethod
    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Runs the platform application lifecycle up to the limit."""
        pass
