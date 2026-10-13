"""
Wellfound (formerly AngelList Talent) Platform Connector.
Implements BasePlatform for high-growth tech startups and venture-backed companies.
Integrates Dynamic Pitch Generation (founder/recruiter note) and Semantic AI matching.
"""
import os
import asyncio
from typing import List, Optional

from core.models import JobPosting
from core.config_loader import get_config
from core.browser_engine import BrowserEngine
from core.tracker import ApplicationTracker
from core.semantic_matcher import semantic_matcher
from core.resume_selector import get_resume_selector
from platforms.base import BasePlatform

class WellfoundPlatform(BasePlatform):
    """Platform connector for Wellfound startup jobs."""

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
            name="wellfound",
            engine=engine or BrowserEngine(),
            tracker=tracker or ApplicationTracker(),
            dry_run=dry_run if dry_run is not None else True,
            limit=limit or 10,
            interactive=interactive
        )
        self.config = config
        self.profile = config.profile
        self.screenshots_dir = config.screenshots_dir
        self.resume_selector = get_resume_selector()

    async def authenticate_or_check_session(self) -> bool:
        """Verifies if the browser session is authenticated on Wellfound."""
        if not self.engine.context:
            return False
        try:
            cookies = await self.engine.context.cookies()
            has_cookie = any(
                ("wellfound.com" in c.get("domain", "") or "angel.co" in c.get("domain", ""))
                and c.get("name") in ("_angel_session", "ajs_user_id", "user_id", "remember_user_token")
                for c in cookies
            )
            if self.page:
                current_url = self.page.url
                if "login" in current_url or "join" in current_url:
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
        """Discovers startup opportunities on Wellfound matching search criteria."""
        print(f"🔍 [Wellfound] Searching jobs for '{keyword}' in '{location}'...")
        if not self.page:
            self.page = await self.engine.start()

        import urllib.parse
        encoded_kw = urllib.parse.quote(keyword)
        search_url = f"https://wellfound.com/jobs?keywords={encoded_kw}"

        try:
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(4.0)

            # Extract job listings from Wellfound search page
            postings_data = await self.page.evaluate(r'''() => {
                const results = [];
                // Query cards using modern Wellfound CSS classes and data attributes
                const cards = document.querySelectorAll(
                    '[data-test="JobSearchResult"], [class*="styles_result__"], [class*="jobListing"], div[class*="JobCard"], div[class*="styles_jobListing__"]'
                );

                for (const c of cards) {
                    const titleEl = c.querySelector('a[href*="/jobs/"], [class*="title"], h2, h3');
                    const compEl = c.querySelector('a[href*="/company/"], [class*="companyName"], [class*="startup"], h4');
                    const compLoc = c.querySelector('[class*="location"], [class*="compensation"], span');
                    const linkEl = c.querySelector('a[href*="/jobs/"]');

                    if (titleEl) {
                        const title = titleEl.innerText.trim();
                        const company = compEl ? compEl.innerText.trim() : 'Startup';
                        const url = linkEl ? linkEl.href : window.location.href;
                        
                        // Extract salary/equity notes if available
                        let salaryText = '';
                        const textContent = c.innerText;
                        const match = textContent.match(/(\$[\d,kK]+|\₹[\d,lL]+|\b[\d]+% equity\b)/g);
                        if (match) {
                            salaryText = match.slice(0, 2).join(' • ');
                        }

                        results.push({
                            title: title,
                            company: company,
                            location: compLoc ? compLoc.innerText.trim() : 'Remote / Bengaluru',
                            url: url,
                            salary_notes: salaryText,
                            job_id: url.includes('/jobs/') ? url.split('/jobs/')[1].split('?')[0].split('/')[0] : String(Math.random().toString(36).substring(7))
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
                    platform="wellfound"
                )
                posting.salary = p.get("salary_notes", "")
                postings.append(posting)

            print(f"  ✨ [Wellfound] Found {len(postings)} job postings")
            return postings

        except Exception as e:
            print(f"  ⚠️ [Wellfound] Search encountered error: {e}")
            return []

    async def apply_to_job(self, job: JobPosting) -> bool:
        """
        Executes Wellfound apply drawer with dynamic pitch note and resume attachment.
        """
        print(f"🚀 [Wellfound] Applying to: {job.title} @ {job.company}")
        if not self.page:
            self.page = await self.engine.start()

        try:
            # Navigate to job URL if distinct
            if job.url and "wellfound.com/jobs/" in job.url and self.page.url != job.url:
                await self.page.goto(job.url, wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(2.5)

            # Extract job description context from the page
            jd_text = await self.page.evaluate(r'''() => {
                const el = document.querySelector('[data-test="JobDescription"], [class*="description"], [class*="jobDetails"], article');
                return el ? el.innerText.trim().slice(0, 2000) : '';
            }''')

            # Generate bespoke founder/recruiter pitch note
            pitch_note = semantic_matcher.generate_pitch_note(
                job_title=job.title,
                company=job.company,
                job_description=jd_text
            )

            # Choose appropriate resume
            resume_path = self.resume_selector.select_resume_for_job(
                job_title=job.title,
                job_description=jd_text
            )

            # Locate Apply button
            apply_btn = self.page.locator(
                "button:has-text('Apply'), a:has-text('Apply'), [data-test*='apply-button'], button:has-text('Quick Apply')"
            ).first

            if await apply_btn.count() == 0:
                print(f"  ℹ️ [Wellfound] Apply button not found or already applied for {job.title}")
                return False

            await apply_btn.click()
            await asyncio.sleep(2.0)

            # Check if application drawer / modal appeared
            modal = self.page.locator("div[role='dialog'], [data-test='JobApplicationModal'], [class*='styles_modal__'], [class*='modal']").first
            is_modal_visible = await modal.count() > 0

            # Insert pitch note in the note textarea
            note_area = self.page.locator(
                "textarea[name='note'], textarea[placeholder*='note'], textarea[placeholder*='pitch'], textarea[placeholder*='message'], textarea"
            ).first

            if await note_area.count() > 0 and await note_area.is_visible():
                print(f"  ✍️ [Wellfound] Inserting dynamic pitch note: \"{pitch_note[:60]}...\"")
                await note_area.fill(pitch_note)
                await asyncio.sleep(1.0)

            # Attach resume file if upload input present
            file_input = self.page.locator("input[type='file']").first
            if await file_input.count() > 0 and os.path.exists(resume_path):
                print(f"  📄 [Wellfound] Uploading resume: {os.path.basename(resume_path)}")
                try:
                    await file_input.set_input_files(resume_path)
                    await asyncio.sleep(1.5)
                except Exception as e:
                    print(f"  ⚠️ [Wellfound] Resume upload notice: {e}")

            # DRY RUN Handling
            if self.dry_run:
                shot = os.path.join(self.screenshots_dir, f"wellfound_{job.job_id}_preview.png")
                await self.page.screenshot(path=shot)
                print(f"  🎯 [DRY RUN] Preview saved to {shot}")

                self.tracker.record_application(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    job_url=job.url,
                    platform="wellfound",
                    status="dry_run_completed",
                    screenshot=shot,
                    salary_notes=f"Pitch: {pitch_note[:100]}..."
                )

                # Close modal if open so next job can be processed
                close_btn = self.page.locator("button[aria-label='Close'], [data-test='ModalCloseButton'], button:has-text('Cancel')").first
                if await close_btn.count() > 0:
                    try:
                        await close_btn.click()
                    except Exception:
                        pass
                return True

            # LIVE Submission
            submit_btn = self.page.locator(
                "button:has-text('Send Application'), button:has-text('Submit Application'), button[type='submit']:has-text('Apply')"
            ).first

            if await submit_btn.count() > 0 and await submit_btn.is_enabled():
                await submit_btn.click()
                await asyncio.sleep(3.0)

                shot = os.path.join(self.screenshots_dir, f"wellfound_{job.job_id}_submitted.png")
                await self.page.screenshot(path=shot)
                print(f"  ✅ [Wellfound] Application submitted! Screenshot: {shot}")

                self.tracker.record_application(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    job_url=job.url,
                    platform="wellfound",
                    status="applied",
                    screenshot=shot,
                    salary_notes=f"Pitch: {pitch_note[:100]}..."
                )
                return True
            else:
                print("  ⚠️ [Wellfound] Submit button not found or disabled.")
                return False

        except Exception as e:
            print(f"  ❌ [Wellfound] Failed to apply: {e}")
            return False

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Runs the autonomous Wellfound application cycle."""
        print("\n🚀 Launching Wellfound Application Engine")
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

        print(f"\n🏁 Wellfound cycle finished. Total processed: {applied_count}/{self.limit}")
        await self.engine.close()
