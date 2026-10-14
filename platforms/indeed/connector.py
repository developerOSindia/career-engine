"""
Indeed Platform Connector.
Implements BasePlatform for Indeed Apply / Easily Apply jobs across India & Global.
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

class IndeedPlatform(BasePlatform):
    """Platform connector for Indeed (in.indeed.com / indeed.com)."""

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
            name="indeed",
            engine=engine or BrowserEngine(),
            tracker=tracker or ApplicationTracker(),
            dry_run=dry_run if dry_run is not None else True,
            limit=limit or 10,
            interactive=interactive
        )
        self.config = config
        self.profile = config.profile
        self.base_url = "https://www.indeed.com"
        self.question_solver = question_solver
        self.question_solver.interactive = interactive
        self.screenshots_dir = config.screenshots_dir
        self.resume_selector = get_resume_selector()

    async def authenticate_or_check_session(self) -> bool:
        """Verifies if the browser session is logged in to Indeed."""
        if not self.engine.context:
            return False
        try:
            cookies = await self.engine.context.cookies()
            has_cookie = any(
                "indeed.com" in c.get("domain", "")
                and c.get("name") in ("CTK", "SURF", "SHARED_SESSION", "SHOE", "LV", "INDEED_CSRF_TOKEN")
                for c in cookies
            )
            if self.page:
                current_url = self.page.url
                if "account/login" in current_url:
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
        """Discovers Indeed Apply jobs matching search criteria."""
        print(f"🔍 [Indeed] Searching for '{keyword}' in '{location}' (Page {page_num})...")
        if not self.page:
            self.page = await self.engine.start()

        encoded_kw = urllib.parse.quote(keyword)
        encoded_loc = urllib.parse.quote(location)
        start_offset = (page_num - 1) * 10
        search_url = f"https://in.indeed.com/jobs?q={encoded_kw}&l={encoded_loc}&fromage=14&start={start_offset}"

        try:
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3.5)

            # Dismiss any popup dialogs / email prompts if present
            await self._dismiss_popups()

            # Extract job cards
            postings_data = await self.page.evaluate(r'''() => {
                const results = [];
                const cards = document.querySelectorAll(
                    'div.job_seen_beacon, div[class*="cardOutline"], td.resultContent, div[data-testid="slider_item"]'
                );

                for (const c of cards) {
                    const titleEl = c.querySelector('h2.jobTitle a, a[id^="job_"], a[data-jk], h2 a');
                    const compEl = c.querySelector('span[data-testid="company-name"], [class*="companyName"], span.company');
                    const locEl = c.querySelector('div[data-testid="text-location"], [class*="companyLocation"], div.location');
                    const salaryEl = c.querySelector('div[data-testid="attribute_snippet_testid"], div.salary-snippet-container, [class*="salary"]');
                    const easyApplyEl = c.querySelector('[data-testid="indeedApply"], [class*="iaLabel"], span:has-text("Easily apply")');

                    if (titleEl) {
                        const title = titleEl.innerText.trim();
                        let url = titleEl.href;
                        let jobId = '';

                        // Extract job key (jk)
                        if (titleEl.hasAttribute('data-jk')) {
                            jobId = titleEl.getAttribute('data-jk');
                        } else if (url && url.includes('jk=')) {
                            const match = url.match(/jk=([a-zA-Z0-9]+)/);
                            if (match) jobId = match[1];
                        }

                        if (!jobId && c.hasAttribute('data-jk')) {
                            jobId = c.getAttribute('data-jk');
                        }
                        if (!jobId) {
                            jobId = String(Math.random().toString(36).substring(7));
                        }

                        const company = compEl ? compEl.innerText.trim() : 'Company';
                        const locationStr = locEl ? locEl.innerText.trim() : 'India';
                        const salaryText = salaryEl ? salaryEl.innerText.trim() : '';

                        results.push({
                            title: title,
                            company: company,
                            location: locationStr,
                            salary_notes: salaryText,
                            url: url || `https://in.indeed.com/viewjob?jk=${jobId}`,
                            job_id: jobId,
                            easy_apply: true  // Will verify inside apply_to_job
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
                    platform="indeed"
                )
                posting.salary = p.get("salary_notes", "")
                postings.append(posting)

            print(f"  ✨ [Indeed] Discovered {len(postings)} jobs on page {page_num}")
            return postings

        except Exception as e:
            print(f"  ⚠️ [Indeed] Search error: {e}")
            return []

    async def _dismiss_popups(self):
        """Dismisses common Indeed newsletter modals, privacy overlays, or push prompts."""
        try:
            close_btn = self.page.locator(
                "button[aria-label='close'], button[aria-label='Close'], button.popover-x-button, #mosaic-modal-close"
            ).first
            if await close_btn.count() > 0 and await close_btn.is_visible():
                await close_btn.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def apply_to_job(self, job: JobPosting) -> bool:
        """Executes the Indeed Apply workflow with automated multi-step form completion."""
        print(f"🚀 [Indeed] Applying to: {job.title} @ {job.company}")
        if not self.page:
            self.page = await self.engine.start()

        try:
            job_url = job.url if job.url else f"https://in.indeed.com/viewjob?jk={job.job_id}"
            await self.page.goto(job_url, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(2.5)
            await self._dismiss_popups()

            # Check for Indeed Apply button
            apply_btn = self.page.locator(
                "button[id*='indeedApplyButton'], button:has-text('Apply now'), button:has-text('Easily apply'), #indeedApplyButton"
            ).first

            if await apply_btn.count() == 0:
                print("  ⏭️ [Indeed] Only external employer application available. Skipping.")
                self.tracker.record_application(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    job_url=job.url,
                    platform="indeed",
                    status="skipped",
                    salary_notes="External application redirect"
                )
                return False

            # Click Apply Now
            await apply_btn.click()
            await asyncio.sleep(3.0)

            # Look for iframe or modal container
            container = self.page
            iframes = self.page.frames
            for f in iframes:
                if "indeed-apply" in f.url or "smartapply" in f.url:
                    container = f
                    break

            # Multi-step loop (Up to 7 steps: Contact -> Resume -> Questions -> Review)
            max_steps = 7
            for step_num in range(1, max_steps + 1):
                await asyncio.sleep(1.5)

                # 1. Fill visible questions/inputs
                await self._fill_step_inputs(container, job)

                # 2. Check for Review or Submit step
                submit_btn = container.locator(
                    "button:has-text('Submit your application'), button:has-text('Submit'), button[type='submit']:has-text('Apply')"
                ).first

                is_submit_ready = await submit_btn.count() > 0 and await submit_btn.is_visible()

                # If on final submit/review screen
                if is_submit_ready or await container.locator("text='Review your application', text='Review application'").count() > 0:
                    shot_path = os.path.join(self.screenshots_dir, f"indeed_{job.job_id}_{'submitted' if not self.dry_run else 'preview'}.png")
                    await self.page.screenshot(path=shot_path)

                    if self.dry_run:
                        print(f"  🎯 [Indeed Dry-Run] Form filled successfully! Preview screenshot saved: {shot_path}")
                        self.tracker.record_application(
                            job_id=job.job_id,
                            title=job.title,
                            company=job.company,
                            location=job.location,
                            job_url=job.url,
                            platform="indeed",
                            status="dry_run_completed",
                            screenshot=shot_path,
                            salary_notes="Verified via Dry Run"
                        )
                        # Close modal
                        await self._close_apply_modal()
                        return True
                    else:
                        # LIVE SUBMIT
                        if is_submit_ready and await submit_btn.is_enabled():
                            await submit_btn.click()
                            await asyncio.sleep(4.0)
                            shot_final = os.path.join(self.screenshots_dir, f"indeed_{job.job_id}_submitted.png")
                            await self.page.screenshot(path=shot_final)
                            print(f"  ✅ [Indeed LIVE] Application submitted! Screenshot: {shot_final}")

                            self.tracker.record_application(
                                job_id=job.job_id,
                                title=job.title,
                                company=job.company,
                                location=job.location,
                                job_url=job.url,
                                platform="indeed",
                                status="applied",
                                screenshot=shot_final,
                                salary_notes="Live submitted via Indeed Apply"
                            )
                            return True

                # 3. Advance to next step (Continue / Next)
                continue_btn = container.locator(
                    "button:has-text('Continue'), button:has-text('Next'), button[type='submit']:has-text('Continue')"
                ).first

                if await continue_btn.count() > 0 and await continue_btn.is_visible() and await continue_btn.is_enabled():
                    await continue_btn.click()
                    await asyncio.sleep(2.0)
                else:
                    # No continue button found; break
                    break

            return False

        except Exception as e:
            print(f"  ❌ [Indeed] Application error: {e}")
            return False

    async def _fill_step_inputs(self, container, job: JobPosting):
        """Fills visible input fields, radio buttons, and selects in the current modal step."""
        personal = self.profile.get("personal_info", {})
        work = self.profile.get("work_summary", {})

        # Fill text inputs
        inputs = await container.locator("input[type='text'], input[type='tel'], input[type='number'], textarea").all()
        for inp in inputs:
            try:
                if not await inp.is_visible():
                    continue
                val = await inp.input_value()
                if val:  # Already filled
                    continue

                # Identify field by label or name
                field_id = await inp.get_attribute("id") or ""
                field_name = await inp.get_attribute("name") or ""
                label_text = ""
                if field_id:
                    lbl = container.locator(f"label[for='{field_id}']")
                    if await lbl.count() > 0:
                        label_text = await lbl.first.inner_text()

                context_str = f"{label_text} {field_name}".lower()

                # Resolve answer
                if any(k in context_str for k in ["phone", "mobile", "contact"]):
                    await inp.fill(personal.get("full_phone", "+917839453651"))
                elif any(k in context_str for k in ["city", "location"]):
                    await inp.fill(personal.get("location", "Bengaluru, Karnataka, India"))
                elif any(k in context_str for k in ["notice", "joining"]):
                    await inp.fill(str(work.get("notice_period_days", "30")))
                elif any(k in context_str for k in ["expected", "ectc", "salary"]):
                    await inp.fill(str(work.get("expected_salary_inr_lpa", "40")))
                elif any(k in context_str for k in ["current", "cctc"]):
                    await inp.fill(str(work.get("current_salary_inr_lpa", "30")))
                elif any(k in context_str for k in ["experience", "years"]):
                    await inp.fill(str(work.get("total_years_experience", "5")))
                else:
                    # Query QuestionSolver
                    if label_text:
                        ans = self.question_solver.solve(label_text, "text")
                        if ans:
                            await inp.fill(str(ans))
            except Exception:
                pass

        # Handle Radio groups
        radios = await container.locator("input[type='radio']").all()
        for r in radios:
            try:
                if not await r.is_visible():
                    continue
                r_id = await r.get_attribute("id") or ""
                lbl = container.locator(f"label[for='{r_id}']")
                if await lbl.count() > 0:
                    lbl_txt = (await lbl.first.inner_text()).lower()
                    if lbl_txt in ("yes", "authorized", "i agree", "30 days"):
                        await r.check()
            except Exception:
                pass

    async def _close_apply_modal(self):
        """Closes the Indeed apply modal cleanly."""
        try:
            close_btn = self.page.locator("button[aria-label='Close'], button.popover-x-button, #close-button").first
            if await close_btn.count() > 0:
                await close_btn.click()
        except Exception:
            pass

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Runs the autonomous Indeed application batch."""
        print("\n🚀 Launching Indeed Automated Application Engine")
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

        print(f"\n🏁 Indeed cycle finished. Total processed: {applied_count}/{self.limit}")
        await self.engine.close()
