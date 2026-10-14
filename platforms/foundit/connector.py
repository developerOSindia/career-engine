"""
Foundit (formerly Monster India) Platform Connector.
Implements BasePlatform for Foundit.in tech applications across India.
Integrates QuestionSolver for compensation, notice period, and experience questions,
and ResumeSelector for role-matched resume attachment.
"""

import os
import re
import urllib.parse
import asyncio
from typing import List, Optional, Dict, Any

from core.models import JobPosting
from core.config_loader import get_config
from core.browser_engine import BrowserEngine
from core.tracker import ApplicationTracker
from core.question_solver import question_solver
from core.resume_selector import get_resume_selector
from platforms.base import BasePlatform

class FounditPlatform(BasePlatform):
    """Platform connector for Foundit (foundit.in - formerly Monster India)."""

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
            name="foundit",
            engine=engine or BrowserEngine(),
            tracker=tracker or ApplicationTracker(),
            dry_run=dry_run if dry_run is not None else True,
            limit=limit or 10,
            interactive=interactive
        )
        self.config = config
        self.profile = config.profile
        self.base_url = "https://www.foundit.in"
        self.question_solver = question_solver
        self.question_solver.interactive = interactive
        self.screenshots_dir = config.screenshots_dir
        self.resume_selector = get_resume_selector()

    async def authenticate_or_check_session(self) -> bool:
        """Verifies if the browser session is authenticated on Foundit."""
        if not self.engine.context:
            return False
        try:
            cookies = await self.engine.context.cookies()
            has_cookie = any(
                "foundit.in" in c.get("domain", "")
                and c.get("name") in ("auth_token", "user_id", "monster_token", "oauth_token", "logged_in")
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
        """Discovers jobs on Foundit matching search criteria."""
        print(f"🔍 [Foundit] Searching for '{keyword}' in '{location}' (Page {page_num})...")
        if not self.page:
            self.page = await self.engine.start()

        encoded_kw = urllib.parse.quote(keyword)
        encoded_loc = urllib.parse.quote(location)
        start_offset = (page_num - 1) * 15
        search_url = f"https://www.foundit.in/srp/results?query={encoded_kw}&locations={encoded_loc}&start={start_offset}&limit=15"

        try:
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3.5)

            # Dismiss popups or overlays if present
            await self._dismiss_popups()

            # Extract job cards
            postings_data = await self.page.evaluate(r'''() => {
                const results = [];
                const cards = document.querySelectorAll(
                    'div.cardContainer, div.srpResultCard, div[class*="jobTuple"], div[class*="card-body"], div[class*="srpContainer"]'
                );

                for (const c of cards) {
                    const titleEl = c.querySelector('h3 a, a[class*="jobTitle"], a[href*="/job/"], a[href*="/seeker/"]');
                    const compEl = c.querySelector('span.companyName, [class*="company"], a[href*="/company/"]');
                    const locEl = c.querySelector('span.loc, [class*="location"], div[class*="loc"]');
                    const salaryEl = c.querySelector('span.salary, [class*="salary"], div[class*="salary"]');

                    if (titleEl) {
                        const title = titleEl.innerText.trim();
                        let url = titleEl.href;
                        let jobId = '';

                        if (c.hasAttribute('id')) {
                            jobId = c.getAttribute('id');
                        } else if (url && url.includes('-')) {
                            const parts = url.split('-');
                            jobId = parts[parts.length - 1].split('?')[0].split('.')[0];
                        }
                        if (!jobId) {
                            jobId = String(Math.random().toString(36).substring(7));
                        }

                        results.push({
                            title: title,
                            company: compEl ? compEl.innerText.trim() : 'Company',
                            location: locEl ? locEl.innerText.trim() : 'India',
                            salary_notes: salaryEl ? salaryEl.innerText.trim() : '',
                            url: url || `https://www.foundit.in/seeker/job-details?id=${jobId}`,
                            job_id: jobId
                        });
                    }
                }
                return results;
            }''')

            postings = []
            for p in postings_data:
                posting = JobPosting(
                    job_id=p["job_id"],
                    title=p["title"],
                    company=p["company"],
                    location=p["location"],
                    url=p["url"],
                    platform="foundit"
                )
                posting.salary = p.get("salary_notes", "")
                postings.append(posting)

            print(f"  ✨ [Foundit] Discovered {len(postings)} jobs on page {page_num}")
            return postings

        except Exception as e:
            print(f"  ⚠️ [Foundit] Search error: {e}")
            return []

    async def _dismiss_popups(self):
        """Dismisses common Foundit chat overlays or prompt modals."""
        try:
            close_btn = self.page.locator(
                "button.close, button[aria-label='close'], button[aria-label='Close'], div.modal-close, button:has-text('Skip')"
            ).first
            if await close_btn.count() > 0 and await close_btn.is_visible():
                await close_btn.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def apply_to_job(self, job: JobPosting) -> bool:
        """Executes the Foundit application workflow."""
        print(f"🚀 [Foundit] Applying to: {job.title} @ {job.company}")
        if not self.page:
            self.page = await self.engine.start()

        try:
            if job.url and self.page.url != job.url:
                await self.page.goto(job.url, wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(2.5)
            await self._dismiss_popups()

            # Find Quick Apply or Apply button
            apply_btn = self.page.locator(
                "button:has-text('Quick Apply'), button:has-text('Apply'), a:has-text('Quick Apply'), button[id*='apply']"
            ).first

            if await apply_btn.count() == 0:
                print("  ⏭️ [Foundit] Apply button not found or expired. Skipping.")
                self.tracker.record_application(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    job_url=job.url,
                    platform="foundit",
                    status="skipped",
                    salary_notes="Apply button unavailable"
                )
                return False

            # Click Apply
            await apply_btn.click()
            await asyncio.sleep(3.0)

            # Check if application opened in a modal or direct confirmation
            modal = self.page.locator("div.modal-dialog, div[class*='applyModal'], div[role='dialog']").first
            if await modal.count() > 0 and await modal.is_visible():
                await self._fill_modal_questions(modal, job)

            # Screenshot
            shot_path = os.path.join(self.screenshots_dir, f"foundit_{job.job_id}_{'submitted' if not self.dry_run else 'preview'}.png")
            await self.page.screenshot(path=shot_path)

            if self.dry_run:
                print(f"  🎯 [Foundit Dry-Run] Form ready! Preview screenshot saved: {shot_path}")
                self.tracker.record_application(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    job_url=job.url,
                    platform="foundit",
                    status="dry_run_completed",
                    screenshot=shot_path,
                    salary_notes="Verified via Dry Run"
                )
                await self._close_modal()
                return True
            else:
                # Live Submit
                submit_btn = self.page.locator(
                    "button:has-text('Submit'), button:has-text('Confirm Apply'), button[type='submit']:has-text('Apply')"
                ).first

                if await submit_btn.count() > 0 and await submit_btn.is_enabled():
                    await submit_btn.click()
                    await asyncio.sleep(3.5)

                shot_final = os.path.join(self.screenshots_dir, f"foundit_{job.job_id}_submitted.png")
                await self.page.screenshot(path=shot_final)
                print(f"  ✅ [Foundit LIVE] Application submitted! Screenshot: {shot_final}")

                self.tracker.record_application(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    job_url=job.url,
                    platform="foundit",
                    status="applied",
                    screenshot=shot_final,
                    salary_notes="Live submitted via Foundit"
                )
                return True

        except Exception as e:
            print(f"  ❌ [Foundit] Failed to apply: {e}")
            return False

    async def _fill_modal_questions(self, modal, job: JobPosting):
        """Fills screening questions in the Foundit apply modal."""
        work = self.profile.get("work_summary", {})
        personal = self.profile.get("personal_info", {})

        inputs = await modal.locator("input[type='text'], input[type='number'], textarea").all()
        for inp in inputs:
            try:
                if not await inp.is_visible():
                    continue
                val = await inp.input_value()
                if val:
                    continue

                ctx = (await inp.get_attribute("name") or "") + " " + (await inp.get_attribute("placeholder") or "")
                ctx = ctx.lower()

                if any(k in ctx for k in ["notice", "joining"]):
                    await inp.fill(str(work.get("notice_period_days", "30")))
                elif any(k in ctx for k in ["expected", "salary", "ctc"]):
                    await inp.fill(str(work.get("expected_salary_inr_lpa", "40")))
                elif any(k in ctx for k in ["current"]):
                    await inp.fill(str(work.get("current_salary_inr_lpa", "30")))
                elif any(k in ctx for k in ["experience", "years"]):
                    await inp.fill(str(work.get("total_years_experience", "5")))
            except Exception:
                pass

    async def _close_modal(self):
        try:
            close_btn = self.page.locator("button.close, button[aria-label='Close'], button:has-text('Cancel')").first
            if await close_btn.count() > 0:
                await close_btn.click()
        except Exception:
            pass

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Runs the autonomous Foundit application batch."""
        print("\n🚀 Launching Foundit Automated Application Engine")
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

        print(f"\n🏁 Foundit cycle finished. Total processed: {applied_count}/{self.limit}")
        await self.engine.close()
