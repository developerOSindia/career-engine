"""
Instahyre Platform Connector.
Implements BasePlatform for fast, curated tech job applications in India.
Integrates with centralized QuestionSolver for CTC (30L/40L), Notice Period (30d), and Resume selection.
"""
import os
import asyncio
from typing import List, Optional

from core.models import JobPosting
from core.config_loader import get_config
from core.browser_engine import BrowserEngine
from core.tracker import ApplicationTracker
from core.question_solver import question_solver
from core.resume_selector import get_resume_selector
from platforms.base import BasePlatform

class InstahyrePlatform(BasePlatform):
    """Platform connector for Instahyre."""
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
            name="instahyre",
            engine=engine or BrowserEngine(),
            tracker=tracker or ApplicationTracker(),
            dry_run=dry_run if dry_run is not None else True,
            limit=limit or 10,
            interactive=interactive
        )
        self.config = config
        self.profile = config.profile
        self.question_solver = question_solver
        self.question_solver.interactive = interactive
        self.screenshots_dir = config.screenshots_dir
        self.resume_selector = get_resume_selector()

    async def authenticate_or_check_session(self) -> bool:
        """Verifies if the browser session is logged in to Instahyre."""
        if not self.engine.context:
            return False
        try:
            cookies = await self.engine.context.cookies()
            has_cookie = any(
                "instahyre.com" in c.get("domain", "")
                and c.get("name") in ("sessionid", "csrftoken", "candidate_id")
                for c in cookies
            )
            if self.page:
                current_url = self.page.url
                if "login" in current_url:
                    return False
            return has_cookie
        except Exception:
            return False

    async def search_jobs(
        self,
        keyword: str,
        location: str,
        remote: bool = False,
        page_num: int = 1
    ) -> List[JobPosting]:
        """Discovers opportunities on Instahyre matching search criteria."""
        print(f"🔍 [Instahyre] Discovering jobs for '{keyword}' in '{location}'...")
        if not self.page:
            self.page = await self.engine.start()

        search_url = "https://www.instahyre.com/candidate/opportunities/?matching=true"
        try:
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3.5)

            postings = await self.page.evaluate(r'''() => {
                const list = [];
                const cards = document.querySelectorAll(
                    '.opportunity-card, [class*="opportunity"], .employer-details, div[ng-repeat*="opportunity"]'
                );
                for (const c of cards) {
                    const titleEl = c.querySelector('.job-title, [class*="title"], h3, h4');
                    const compEl = c.querySelector('.employer-name, [class*="employer"], [class*="company"]');
                    const locEl = c.querySelector('.job-locations, [class*="location"]');
                    const expEl = c.querySelector('[class*="experience"], [class*="exp"]');
                    const descEl = c.querySelector('[class*="description"], [class*="summary"], p');

                    if (titleEl && titleEl.innerText.trim()) {
                        list.push({
                            title: titleEl.innerText.trim(),
                            company: compEl ? compEl.innerText.trim() : 'Company',
                            location: locEl ? locEl.innerText.trim() : 'Bengaluru',
                            experience: expEl ? expEl.innerText.trim() : '',
                            description: descEl ? descEl.innerText.trim() : '',
                            url: window.location.href,
                            job_id: c.id || String(Math.random().toString(36).substring(7))
                        });
                    }
                }
                return list;
            }''')

            results = []
            for p in postings:
                posting = JobPosting(
                    job_id=p["job_id"],
                    title=p["title"],
                    company=p["company"],
                    location=p["location"],
                    url=p["url"],
                    platform="instahyre"
                )
                posting.salary = p.get("experience", "")
                results.append(posting)

            print(f"  ✨ [Instahyre] Discovered {len(results)} opportunities")
            return results
        except Exception as e:
            print(f"  ⚠️ [Instahyre] Search error: {e}")
            return []

    async def _handle_application_modal(self, job_title: str) -> None:
        """Solves screening questions inside Instahyre apply modal if triggered."""
        modal = self.page.locator(".modal-dialog, .application-modal, div[class*='modal'], form[name*='apply']").first
        if await modal.count() == 0 or not await modal.is_visible():
            return

        print("  📝 [Instahyre] Handling screening dialog questions...")

        # 1. Notice Period
        notice_input = self.page.locator(
            "select[name*='notice'], select[id*='notice'], input[placeholder*='notice'], [class*='notice'] select"
        ).first
        if await notice_input.count() > 0:
            work = self.profile.get("work_summary", {})
            notice_val = str(work.get("notice_period_days", 30))
            try:
                # Try selecting option containing 30 or 1 month
                await notice_input.select_option(label="30 days")
            except Exception:
                try:
                    await notice_input.select_option(index=1)
                except Exception:
                    pass

        # 2. Expected CTC & Current CTC
        expected_ctc_input = self.page.locator(
            "input[name*='expected'], input[id*='expected_ctc'], input[placeholder*='Expected']"
        ).first
        if await expected_ctc_input.count() > 0:
            sal = self.profile.get("work_summary", {}).get("expected_ctc_lakhs", 35)
            await expected_ctc_input.fill(str(sal))

        current_ctc_input = self.page.locator(
            "input[name*='current'], input[id*='current_ctc'], input[placeholder*='Current']"
        ).first
        if await current_ctc_input.count() > 0:
            sal = self.profile.get("work_summary", {}).get("current_ctc_lakhs", 25)
            await current_ctc_input.fill(str(sal))

        # 3. File upload if present
        file_input = self.page.locator("input[type='file']").first
        if await file_input.count() > 0:
            chosen_resume = self.resume_selector.select_resume_for_job(job_title)
            if os.path.exists(chosen_resume):
                try:
                    await file_input.set_input_files(chosen_resume)
                    await asyncio.sleep(1.0)
                except Exception:
                    pass

    async def apply_to_job(self, job: JobPosting) -> bool:
        """Executes 1-click apply or question-handled application on Instahyre."""
        print(f"🚀 [Instahyre] Applying to: {job.title} @ {job.company}")
        if not self.page:
            self.page = await self.engine.start()

        apply_btn = self.page.locator(
            "button:has-text('Apply'), button:has-text('Interested'), a:has-text('Apply'), button:has-text('Show Interest')"
        ).first

        if await apply_btn.count() == 0:
            print("  ℹ️ [Instahyre] Apply button not found or already submitted.")
            return False

        if self.dry_run:
            shot = os.path.join(self.screenshots_dir, f"instahyre_{job.job_id}_preview.png")
            await self.page.screenshot(path=shot)
            print(f"  🎯 [DRY RUN] Preview saved to {shot}")
            self.tracker.record_application(
                job_id=job.job_id,
                title=job.title,
                company=job.company,
                location=job.location,
                job_url=job.url,
                platform="instahyre",
                status="dry_run_completed",
                screenshot=shot
            )
            return True

        # Live Click
        await apply_btn.click()
        await asyncio.sleep(2.0)

        # Handle any secondary questionnaire popup
        await self._handle_application_modal(job.title)

        # Look for confirm / send button in modal
        confirm_btn = self.page.locator(
            ".modal button:has-text('Submit'), .modal button:has-text('Send'), button:has-text('Confirm')"
        ).first
        if await confirm_btn.count() > 0 and await confirm_btn.is_visible():
            await confirm_btn.click()
            await asyncio.sleep(2.0)

        shot = os.path.join(self.screenshots_dir, f"instahyre_{job.job_id}_submitted.png")
        await self.page.screenshot(path=shot)
        self.tracker.record_application(
            job_id=job.job_id,
            title=job.title,
            company=job.company,
            location=job.location,
            job_url=job.url,
            platform="instahyre",
            status="applied",
            screenshot=shot
        )
        print(f"  ✅ [Instahyre] Applied successfully! Screenshot: {shot}")
        return True

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Runs the autonomous Instahyre application cycle."""
        print(f"\n🚀 Launching Instahyre Application Engine")
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
                    print(f"  ⏭️ Already applied to {job.title} @ {job.company}, skipping.")
                    continue
                success = await self.apply_to_job(job)
                if success:
                    applied_count += 1
                await asyncio.sleep(2.5)

        print(f"\n🏁 Instahyre cycle finished. Total processed: {applied_count}/{self.limit}")
        await self.engine.close()
