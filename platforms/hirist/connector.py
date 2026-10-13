"""
Hirist (hirist.tech / iimjobs) Platform Connector.
Implements BasePlatform for tech job applications across India.
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

class HiristPlatform(BasePlatform):
    """Platform connector for Hirist.tech."""
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
            name="hirist",
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
        """Verifies if the browser session is logged in to Hirist."""
        if not self.engine.context:
            return False
        try:
            cookies = await self.engine.context.cookies()
            return any("hirist.tech" in c.get("domain", "") or "iimjobs.com" in c.get("domain", "") for c in cookies)
        except Exception:
            return False

    async def search_jobs(
        self,
        keyword: str,
        location: str,
        remote: bool = False,
        page_num: int = 1
    ) -> List[JobPosting]:
        """Discovers Data Engineering jobs on Hirist."""
        print(f"🔍 [Hirist] Searching for '{keyword}' in '{location}' (Page {page_num})...")
        if not self.page:
            self.page = await self.engine.start()

        search_url = f"https://www.hirist.tech/search/{keyword.replace(' ', '-')}-jobs-in-{location.replace(' ', '-')}.html"
        try:
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3.0)
            
            postings = await self.page.evaluate(r'''() => {
                const list = [];
                const cards = document.querySelectorAll('.job-card, [class*="job-item"], [data-job-id]');
                for (const c of cards) {
                    const titleEl = c.querySelector('.job-title, h2, a[href*="job"]');
                    const compEl = c.querySelector('.company-name, [class*="company"]');
                    const locEl = c.querySelector('.location, [class*="location"]');
                    if (titleEl && titleEl.href) {
                        list.push({
                            title: titleEl.innerText.trim(),
                            company: compEl ? compEl.innerText.trim() : 'Company',
                            location: locEl ? locEl.innerText.trim() : 'Bengaluru',
                            url: titleEl.href,
                            job_id: c.getAttribute('data-job-id') || String(Math.random().toString(36).substring(7))
                        });
                    }
                }
                return list;
            }''')
            return [
                JobPosting(
                    job_id=p["job_id"],
                    title=p["title"],
                    company=p["company"],
                    location=p["location"],
                    url=p["url"],
                    platform="hirist"
                )
                for p in postings
            ]
        except Exception as e:
            print(f"  ⚠️ [Hirist] Search error: {e}")
            return []

    async def apply_to_job(self, job: JobPosting) -> bool:
        """Executes application on Hirist job card."""
        print(f"🚀 [Hirist] Processing application for: {job.title} @ {job.company}")
        if not self.page:
            self.page = await self.engine.start()

        await self.page.goto(job.url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2.5)

        apply_btn = self.page.locator("button:has-text('Apply'), a:has-text('Apply')").first
        if await apply_btn.count() == 0 or not await apply_btn.is_visible():
            print("  ℹ️ [Hirist] No apply button found.")
            return False

        if self.dry_run:
            shot = os.path.join(self.screenshots_dir, f"hirist_{job.job_id}_preview.png")
            await self.page.screenshot(path=shot)
            print(f"  🎯 [DRY RUN] Preview saved to {shot}")
            self.tracker.record_application(
                job_id=job.job_id,
                title=job.title,
                company=job.company,
                location=job.location,
                job_url=job.url,
                platform="hirist",
                status="dry_run_completed",
                screenshot=shot
            )
            return True

        await apply_btn.click()
        await asyncio.sleep(2.0)

        shot = os.path.join(self.screenshots_dir, f"hirist_{job.job_id}_submitted.png")
        await self.page.screenshot(path=shot)
        self.tracker.record_application(
            job_id=job.job_id,
            title=job.title,
            company=job.company,
            location=job.location,
            job_url=job.url,
            platform="hirist",
            status="applied",
            screenshot=shot
        )
        return True

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Runs the autonomous Hirist application cycle."""
        print(f"\n🚀 Launching Hirist Application Engine")
        self.page = await self.engine.start()
        kw_list = keywords or self.config.search_keywords
        loc = location or self.config.search_location

        applied_count = 0
        for kw in kw_list:
            if applied_count >= self.limit:
                break
            jobs = await self.search_jobs(kw, loc)
            for job in jobs:
                if applied_count >= self.limit:
                    break
                if self.tracker.is_already_applied(job.job_id, job.title, job.company):
                    continue
                success = await self.apply_to_job(job)
                if success:
                    applied_count += 1
                await asyncio.sleep(2.0)
        await self.engine.close()
