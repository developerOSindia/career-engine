"""
Glassdoor Platform Connector.
Implements BasePlatform for Glassdoor Easy Apply applications.
Integrates with centralized QuestionSolver for CTC (30L/40L) and Notice Period (60d/30d).
"""
import os
import asyncio
from typing import List, Optional

from core.models import JobPosting
from core.config_loader import get_config
from core.browser_engine import BrowserEngine
from core.tracker import ApplicationTracker
from core.question_solver import question_solver
from platforms.base import BasePlatform

class GlassdoorPlatform(BasePlatform):
    """Platform connector for Glassdoor."""
    def __init__(
        self,
        engine: Optional[BrowserEngine] = None,
        tracker: Optional[ApplicationTracker] = None,
        dry_run: Optional[bool] = None,
        limit: Optional[int] = None,
        interactive: bool = False
    ):
        config = get_config()
        super().__init__(
            name="glassdoor",
            engine=engine or BrowserEngine(),
            tracker=tracker or ApplicationTracker(),
            dry_run=dry_run if dry_run is not None else True,
            limit=limit or 10,
            interactive=interactive
        )
        self.config = config
        self.question_solver = question_solver
        self.question_solver.interactive = interactive
        self.screenshots_dir = config.screenshots_dir

    async def authenticate_or_check_session(self) -> bool:
        """Verifies if the browser session is logged in to Glassdoor."""
        if not self.engine.context:
            return False
        try:
            cookies = await self.engine.context.cookies()
            return any("glassdoor.com" in c.get("domain", "") or "glassdoor.co.in" in c.get("domain", "") for c in cookies)
        except Exception:
            return False

    async def search_jobs(
        self,
        keyword: str,
        location: str,
        remote: bool = False,
        page_num: int = 1
    ) -> List[JobPosting]:
        """Discovers jobs on Glassdoor."""
        print(f"🔍 [Glassdoor] Searching for '{keyword}' in '{location}'...")
        return []

    async def apply_to_job(self, job: JobPosting) -> bool:
        """Applies to a Glassdoor Easy Apply job."""
        print(f"🚀 [Glassdoor] Applying to: {job.title} @ {job.company}")
        return False

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Runs the Glassdoor application cycle."""
        print(f"\n🚀 [Glassdoor] Connector scaffold ready.")
