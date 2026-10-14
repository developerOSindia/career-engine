"""
Glassdoor Platform Connector.
Implements BasePlatform for Glassdoor Easy Apply applications across India & Global.
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

class GlassdoorPlatform(BasePlatform):
    """Platform connector for Glassdoor (glassdoor.co.in / glassdoor.com)."""

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
        self.profile = config.profile
        self.base_url = "https://www.glassdoor.com"
        self.question_solver = question_solver
        self.question_solver.interactive = interactive
        self.screenshots_dir = config.screenshots_dir
        self.resume_selector = get_resume_selector()

    async def authenticate_or_check_session(self) -> bool:
        """Verifies if the browser session is logged in to Glassdoor."""
        if not self.engine.context:
            return False
        try:
            cookies = await self.engine.context.cookies()
            has_cookie = any(
                ("glassdoor.com" in c.get("domain", "") or "glassdoor.co.in" in c.get("domain", ""))
                and c.get("name") in ("gdId", "as", "gdl", "JSESSIONID", "user_session")
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
        """Discovers Glassdoor Easy Apply jobs matching search criteria."""
        print(f"🔍 [Glassdoor] Searching for '{keyword}' in '{location}' (Page {page_num})...")
        if not self.page:
            self.page = await self.engine.start()

        encoded_kw = urllib.parse.quote(keyword)
        encoded_loc = urllib.parse.quote(location)
        search_url = f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={encoded_kw}&locT=C&locKeyword={encoded_loc}&fromAge=14"

        try:
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3.5)

            # Dismiss modal overlays if any
            await self._dismiss_popups()

            # Extract job cards
            postings_data = await self.page.evaluate(r'''() => {
                const results = [];
                const cards = document.querySelectorAll(
                    'li[data-test="jobListing"], div[data-test="job-card-wrapper"], article[class*="JobCard"], div[class*="JobsList_wrapper"]'
                );

                for (const c of cards) {
                    const titleEl = c.querySelector('a[data-test="job-title"], a[class*="JobCard_jobTitle"], h2 a');
                    const compEl = c.querySelector('span[data-test="employer-name"], [class*="EmployerProfile"], span[class*="employer"]');
                    const locEl = c.querySelector('div[data-test="emp-location"], [class*="JobCard_location"], span[class*="location"]');
                    const salaryEl = c.querySelector('div[data-test="detailSalary"], [class*="JobCard_salary"], span[class*="salary"]');
                    const easyApplyEl = c.querySelector('[data-test="easy-apply-label"], span:has-text("Easy Apply")');

                    if (titleEl) {
                        const title = titleEl.innerText.trim();
                        let url = titleEl.href;
                        let jobId = '';

                        if (c.hasAttribute('data-jobid')) {
                            jobId = c.getAttribute('data-jobid');
                        } else if (url && url.includes('jobListingId=')) {
                            const match = url.match(/jobListingId=(\d+)/);
                            if (match) jobId = match[1];
                        }
                        if (!jobId) {
                            jobId = String(Math.random().toString(36).substring(7));
                        }

                        results.push({
                            title: title,
                            company: compEl ? compEl.innerText.trim() : 'Company',
                            location: locEl ? locEl.innerText.trim() : 'India',
                            salary_notes: salaryEl ? salaryEl.innerText.trim() : '',
                            url: url || `https://www.glassdoor.co.in/job-listing/?jl=${jobId}`,
                            job_id: jobId,
                            easy_apply: !!easyApplyEl
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
                    platform="glassdoor"
                )
                posting.salary = p.get("salary_notes", "")
                postings.append(posting)

            print(f"  ✨ [Glassdoor] Discovered {len(postings)} jobs on page {page_num}")
            return postings

        except Exception as e:
            print(f"  ⚠️ [Glassdoor] Search error: {e}")
            return []

    async def _dismiss_popups(self):
        """Dismisses common Glassdoor sign-in walls, location confirmations, or cookie prompts."""
        try:
            close_btn = self.page.locator(
                "button[aria-label='Close'], button.CloseButton, button[data-test='modal-close'], button:has-text('No thanks')"
            ).first
            if await close_btn.count() > 0 and await close_btn.is_visible():
                await close_btn.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def apply_to_job(self, job: JobPosting) -> bool:
        """Executes the Glassdoor Easy Apply modal workflow."""
        print(f"🚀 [Glassdoor] Applying to: {job.title} @ {job.company}")
        if not self.page:
            self.page = await self.engine.start()

        try:
            if job.url and self.page.url != job.url:
                await self.page.goto(job.url, wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(2.5)
            await self._dismiss_popups()

            # Check for Easy Apply button
            apply_btn = self.page.locator(
                "button[data-test='easy-apply-button'], button:has-text('Easy Apply'), button:has-text('Apply now')"
            ).first

            if await apply_btn.count() == 0:
                print("  ⏭️ [Glassdoor] External employer application. Skipping.")
                self.tracker.record_application(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    job_url=job.url,
                    platform="glassdoor",
                    status="skipped",
                    salary_notes="External application redirect"
                )
                return False

            # Click Easy Apply
            await apply_btn.click()
            await asyncio.sleep(3.0)

            # Easy Apply Dialog container
            modal = self.page.locator("div[data-test='easy-apply-modal'], div[role='dialog']").first

            # Step loop
            for step_num in range(1, 6):
                await asyncio.sleep(1.5)

                # Fill inputs in current step
                await self._fill_modal_inputs(modal, job)

                # Check for Submit / Final Review
                submit_btn = self.page.locator(
                    "button:has-text('Submit Application'), button:has-text('Submit'), button[type='submit']:has-text('Apply')"
                ).first

                is_ready = await submit_btn.count() > 0 and await submit_btn.is_visible()

                if is_ready or await self.page.locator("text='Review your application'").count() > 0:
                    shot_path = os.path.join(self.screenshots_dir, f"glassdoor_{job.job_id}_{'submitted' if not self.dry_run else 'preview'}.png")
                    await self.page.screenshot(path=shot_path)

                    if self.dry_run:
                        print(f"  🎯 [Glassdoor Dry-Run] Form filled! Preview screenshot saved: {shot_path}")
                        self.tracker.record_application(
                            job_id=job.job_id,
                            title=job.title,
                            company=job.company,
                            location=job.location,
                            job_url=job.url,
                            platform="glassdoor",
                            status="dry_run_completed",
                            screenshot=shot_path,
                            salary_notes="Verified via Dry Run"
                        )
                        await self._close_modal()
                        return True
                    else:
                        # Live Submit
                        if is_ready and await submit_btn.is_enabled():
                            await submit_btn.click()
                            await asyncio.sleep(4.0)
                            shot_final = os.path.join(self.screenshots_dir, f"glassdoor_{job.job_id}_submitted.png")
                            await self.page.screenshot(path=shot_final)
                            print(f"  ✅ [Glassdoor LIVE] Application submitted! Screenshot: {shot_final}")

                            self.tracker.record_application(
                                job_id=job.job_id,
                                title=job.title,
                                company=job.company,
                                location=job.location,
                                job_url=job.url,
                                platform="glassdoor",
                                status="applied",
                                screenshot=shot_final,
                                salary_notes="Live submitted via Glassdoor Easy Apply"
                            )
                            return True

                # Click Next / Continue
                next_btn = self.page.locator(
                    "button:has-text('Continue'), button:has-text('Next'), button[type='submit']:has-text('Continue')"
                ).first

                if await next_btn.count() > 0 and await next_btn.is_visible() and await next_btn.is_enabled():
                    await next_btn.click()
                    await asyncio.sleep(2.0)
                else:
                    break

            return False

        except Exception as e:
            print(f"  ❌ [Glassdoor] Failed to apply: {e}")
            return False

    async def _fill_modal_inputs(self, modal, job: JobPosting):
        """Answers fields inside Glassdoor Easy Apply modal."""
        personal = self.profile.get("personal_info", {})
        work = self.profile.get("work_summary", {})

        inputs = await self.page.locator("input[type='text'], input[type='tel'], input[type='number'], textarea").all()
        for inp in inputs:
            try:
                if not await inp.is_visible():
                    continue
                val = await inp.input_value()
                if val:
                    continue

                field_name = (await inp.get_attribute("name") or "").lower()
                field_id = (await inp.get_attribute("id") or "").lower()
                placeholder = (await inp.get_attribute("placeholder") or "").lower()

                ctx = f"{field_name} {field_id} {placeholder}"
                if any(k in ctx for k in ["phone", "mobile", "tel"]):
                    await inp.fill(personal.get("full_phone", "+917839453651"))
                elif any(k in ctx for k in ["city", "location"]):
                    await inp.fill(personal.get("location", "Bengaluru, Karnataka, India"))
                elif any(k in ctx for k in ["notice"]):
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
            close_btn = self.page.locator("button[aria-label='Close'], button[data-test='modal-close']").first
            if await close_btn.count() > 0:
                await close_btn.click()
        except Exception:
            pass

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Runs the autonomous Glassdoor application batch."""
        print("\n🚀 Launching Glassdoor Automated Application Engine")
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

        print(f"\n🏁 Glassdoor cycle finished. Total processed: {applied_count}/{self.limit}")
        await self.engine.close()
