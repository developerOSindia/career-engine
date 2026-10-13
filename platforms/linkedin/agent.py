"""
LinkedIn Job Application Agent.
Coordinates job search scanning, multi-step application form filling,
safe review checkpoints, and database/spreadsheet persistence.
"""
import os
import re
import sys
import asyncio
from typing import Dict, List, Optional
from playwright.async_api import Locator, Page

from core.models import JobPosting
from core.config_loader import get_config
from core.browser_engine import BrowserEngine
from core.tracker import ApplicationTracker
from platforms.base import BasePlatform
from platforms.linkedin.scanner import LinkedInJobScanner
from platforms.linkedin.form_filler import LinkedInFormFiller

class LinkedInApplicationAgent(BasePlatform):
    def __init__(
        self,
        engine: Optional[BrowserEngine] = None,
        tracker: Optional[ApplicationTracker] = None,
        dry_run: Optional[bool] = None,
        limit: Optional[int] = None,
        interactive: bool = False
    ):
        config = get_config()
        engine = engine or BrowserEngine()
        tracker = tracker or ApplicationTracker()
        
        is_dry_run = dry_run if dry_run is not None else config.yaml_config.get("settings", {}).get("dry_run", False)
        max_limit = limit if limit is not None else config.default_max_applications

        super().__init__(
            name="linkedin",
            engine=engine,
            tracker=tracker,
            dry_run=is_dry_run,
            limit=max_limit,
            interactive=interactive
        )

        self.config = config
        self.profile_data = config.profile
        self.screenshots_dir = config.screenshots_dir
        self.filler = LinkedInFormFiller(self.profile_data, dry_run=self.dry_run, profile_path=str(config.profile_path))
        self.filler.question_solver.interactive = interactive
        self.scanner = None
        self.session_submitted_jobs = []
        self.jobs_needing_review = []

    async def authenticate_or_check_session(self) -> bool:
        """Verifies if the user is authenticated on LinkedIn."""
        return await self.engine.check_linkedin_logged_in()

    async def search_jobs(
        self,
        keyword: str,
        location: str,
        remote: bool = False,
        page_num: int = 1
    ) -> List[JobPosting]:
        """Discovers jobs on LinkedIn matching criteria."""
        if not self.scanner:
            self.scanner = LinkedInJobScanner(self.page)
        
        start_offset = (page_num - 1) * 25
        search_url = self.scanner.build_search_url(
            keywords=keyword,
            location=location,
            easy_apply=True,
            date_posted="past-week",
            remote=remote,
            start=start_offset
        )
        await self.scanner.search(search_url)
        raw_jobs = await self.scanner.extract_jobs_on_page()
        
        postings = []
        for r in raw_jobs:
            postings.append(JobPosting(
                job_id=r["job_id"],
                title=r["title"],
                company=r["company"],
                location=r["location"],
                url=r["job_url"],
                platform="linkedin",
                easy_apply=r.get("is_easy_apply", True)
            ))
        return postings

    async def _extract_job_details(self) -> dict:
        """Extracts hiring manager, workplace type, and key skills from detail view."""
        info = await self.page.evaluate(r'''() => {
            // 1. Job Description text
            const jdEl = document.querySelector('#job-details, .jobs-description__content, .jobs-box__html-content');
            const jd = jdEl ? jdEl.innerText.trim() : '';

            // 2. Hiring Manager details
            let hirerName = '';
            let hirerLink = '';
            const allH2 = Array.from(document.querySelectorAll('h2, h3, div, span'));
            const hirerH2 = allH2.find(el => el.innerText && el.innerText.toLowerCase().includes('meet the hiring team'));
            if (hirerH2) {
                const parent = hirerH2.closest('section, div');
                if (parent) {
                    const links = Array.from(parent.querySelectorAll('a[href*="/in/"]'));
                    for (const a of links) {
                        const t = a.innerText.trim();
                        if (t && !t.toLowerCase().includes('message') && !t.toLowerCase().includes('connect')) {
                            const lines = t.split('\n').map(l => l.trim()).filter(Boolean);
                            hirerName = lines[0];
                            hirerLink = a.href;
                            break;
                        }
                    }
                }
            }

            // 3. Workplace type
            let workplace = 'On-site';
            const body = document.body.innerText;
            const badges = Array.from(document.querySelectorAll('span, div')).map(e => e.innerText ? e.innerText.trim() : '');
            if (badges.includes('Remote') || body.includes('Remote') || jd.includes('Remote')) {
                workplace = 'Remote';
            } else if (badges.includes('Hybrid') || body.includes('Hybrid') || jd.includes('Hybrid')) {
                workplace = 'Hybrid';
            }

            return {
                hiring_manager_name: hirerName,
                hiring_manager_url: hirerLink,
                workplace_type: workplace,
                job_description: jd
            };
        }''')

        KNOWN_SKILLS = [
            "Python", "PySpark", "Spark", "Databricks", "Delta Lake", "AWS", "Azure", "GCP",
            "Airflow", "Kafka", "PostgreSQL", "MySQL", "Snowflake", "Redshift", "BigQuery",
            "SQL", "Scala", "Java", "Docker", "Kubernetes", "CI/CD", "Terraform", "Git",
            "React", "Node.js", "ETL", "ELT", "Data Pipeline", "Data Modeling", "Hadoop",
            "Hive", "Flink", "dbt", "Presto", "Trino", "NoSQL", "MongoDB", "Cassandra"
        ]
        jd_lower = (info.get("job_description") or "").lower()
        extracted = [s for s in KNOWN_SKILLS if re.search(rf"\b{re.escape(s.lower())}\b", jd_lower)]
        info["key_skills"] = ", ".join(extracted)
        return info

    async def apply_to_job(self, job: JobPosting) -> bool:
        """Navigates to job view, extracts details, fills questionnaire, and submits."""
        job_id = job.job_id
        title = job.title
        company = job.company
        loc = job.location
        url = job.url

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(2.5)

            details = await self._extract_job_details()
            workplace = details.get("workplace_type", "On-site")
            hirer_name = details.get("hiring_manager_name", "")
            hirer_url = details.get("hiring_manager_url", "")
            key_skills = details.get("key_skills", "")
            jd_text = details.get("job_description", "")

            print(f"  🏢 Workplace Type     : {workplace}")
            if hirer_name:
                print(f"  👤 Hiring Manager      : {hirer_name} ({hirer_url})")
            else:
                print(f"  👤 Hiring Manager      : Not publicly listed")
            if key_skills:
                print(f"  🛠️ Required Skills     : {key_skills}")

            apply_button = self.page.locator("button:has-text('Easy Apply'), button.jobs-apply-button").first
            if await apply_button.count() == 0 or not await apply_button.is_visible():
                print(f"  ℹ️ No Easy Apply available. Skipping.")
                self.tracker.record_application(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=loc,
                    job_url=url,
                    platform="linkedin",
                    workplace_type=workplace,
                    hiring_manager_name=hirer_name,
                    hiring_manager_url=hirer_url,
                    key_skills=key_skills,
                    job_description=jd_text,
                    status="skipped",
                    notes="External redirect / No Easy Apply"
                )
                return False

            print(f"  ✨ Found Easy Apply! Opening application...")
            await apply_button.click()
            await asyncio.sleep(1.5)

            modal = self.page.locator("dialog, [role='dialog'], div.jobs-easy-apply-modal").first
            if await modal.count() == 0:
                print("  ❌ Could not find application modal dialog.")
                return False

            # Multi-step questionnaire loop (max 10 steps)
            for step in range(10):
                await asyncio.sleep(1.0)
                await self.filler.fill_current_step(modal)
                await asyncio.sleep(1.0)

                # Scroll to reveal buttons
                try:
                    await modal.evaluate(r'''el => {
                        const s = el.querySelector('div[tabindex="0"], .jobs-easy-apply-modal__content, div[class*="content"]') || el;
                        s.scrollTop = s.scrollHeight;
                    }''')
                except Exception:
                    pass

                # Check for Submit Application button
                submit_btn = modal.locator("button:has-text('Submit application'), button[aria-label*='Submit application'], button:has-text('Submit'), button[aria-label*='Submit']").first
                if await submit_btn.count() > 0 and await submit_btn.is_visible():
                    screenshot_path = os.path.join(self.screenshots_dir, f"job_{job_id}_review.png")
                    await self.page.screenshot(path=screenshot_path)
                    print(f"  📸 Saved review screenshot: {screenshot_path}")

                    job_answers = self.filler.get_and_clear_job_answers()

                    if self.dry_run:
                        print(f"  🎯 [DRY RUN] Review reached. Not submitting.")
                        self.tracker.record_application(
                            job_id=job_id,
                            title=title,
                            company=company,
                            location=loc,
                            job_url=url,
                            platform="linkedin",
                            workplace_type=workplace,
                            hiring_manager_name=hirer_name,
                            hiring_manager_url=hirer_url,
                            key_skills=key_skills,
                            job_description=jd_text,
                            status="dry_run_completed",
                            notes="Dry run review reached",
                            answers_filled=job_answers,
                            screenshot=screenshot_path
                        )
                        await self._close_modal(modal, discard=True)
                        return True
                    else:
                        print(f"  🚀 Submitting application for {title} @ {company}...")
                        await submit_btn.click()
                        await asyncio.sleep(2.0)
                        
                        submitted_shot = os.path.join(self.screenshots_dir, f"job_{job_id}_submitted.png")
                        await self.page.screenshot(path=submitted_shot)
                        print(f"  ✅ Application Submitted! Saved to {submitted_shot}")
                        if job_answers:
                            print(f"\n  📝 [Q&A Log for {title}]:")
                            for q, a in job_answers.items():
                                print(f"     • Question: {q}")
                                print(f"       Answer  : {a}")
                            print(f"     🔗 Job Link: {url}\n")
                        
                        record = {
                            "title": title,
                            "company": company,
                            "workplace_type": workplace,
                            "hiring_manager_name": hirer_name,
                            "hiring_manager_url": hirer_url,
                            "key_skills": key_skills,
                            "url": url,
                            "answers_filled": job_answers,
                            "screenshot": submitted_shot
                        }
                        self.session_submitted_jobs.append(record)

                        self.tracker.record_application(
                            job_id=job_id,
                            title=title,
                            company=company,
                            location=loc,
                            job_url=url,
                            platform="linkedin",
                            workplace_type=workplace,
                            hiring_manager_name=hirer_name,
                            hiring_manager_url=hirer_url,
                            key_skills=key_skills,
                            job_description=jd_text,
                            status="applied",
                            notes="Successfully submitted",
                            answers_filled=job_answers,
                            screenshot=submitted_shot
                        )
                        await self._close_modal(modal, discard=False)
                        return True

                # Check for Review button
                review_btn = modal.locator("footer button.artdeco-button--primary:has-text('Review'), button:has-text('Review'), button[aria-label*='Review']").first
                if await review_btn.count() > 0 and await review_btn.is_visible():
                    print("  ➡️ Reviewing application...")
                    await review_btn.click()
                    await asyncio.sleep(0.8)
                    continue

                # Check for Next button
                next_btn = modal.locator("footer button.artdeco-button--primary:has-text('Next'), button:has-text('Next'), button[aria-label*='Next']").first
                if await next_btn.count() > 0 and await next_btn.is_visible():
                    print("  ➡️ Next step...")
                    await next_btn.click()
                    await asyncio.sleep(0.8)
                    continue

                # Check if submission occurred automatically
                header_text = await modal.inner_text()
                if "application sent" in header_text.lower() or "submitted" in header_text.lower():
                    submitted_shot = os.path.join(self.screenshots_dir, f"job_{job_id}_submitted.png")
                    await self.page.screenshot(path=submitted_shot)
                    print(f"  ✅ Application Submitted! Saved to {submitted_shot}")
                    self.tracker.record_application(
                        job_id=job_id,
                        title=title,
                        company=company,
                        location=loc,
                        job_url=url,
                        platform="linkedin",
                        workplace_type=workplace,
                        status="applied",
                        screenshot=submitted_shot
                    )
                    await self._close_modal(modal, discard=False)
                    return True

            # If unsubmitted after 10 steps, discard cleanly (never save draft)
            print("  ❌ Incomplete form. Discarding application (never saving drafts)...")
            self.jobs_needing_review.append({
                "title": title,
                "company": company,
                "url": url,
                "reason": "Complex assessment / multi-step form"
            })
            self.tracker.record_application(
                job_id=job_id,
                title=title,
                company=company,
                location=loc,
                job_url=url,
                platform="linkedin",
                workplace_type=workplace,
                hiring_manager_name=hirer_name,
                hiring_manager_url=hirer_url,
                key_skills=key_skills,
                job_description=jd_text,
                status="needs_review",
                notes="Flagged for manual review / complex form"
            )
            await self._close_modal(modal, discard=True)
            return False

        except Exception as e:
            print(f"  ❌ Error applying to {title}: {e}")
            try:
                modal = self.page.locator("dialog, [role='dialog'], div.jobs-easy-apply-modal").first
                await self._close_modal(modal, discard=True)
            except Exception:
                pass
            return False

    async def _close_modal(self, modal: Locator, discard: bool = True):
        """Dismisses the modal. If discard=True, clicks Discard so drafts are never saved."""
        try:
            close_btn = modal.locator("button[aria-label*='Dismiss'], button[data-test-modal-close-btn], button.artdeco-modal__dismiss").first
            if await close_btn.count() > 0 and await close_btn.is_visible():
                await close_btn.click()
                await asyncio.sleep(0.5)

            if discard:
                for _ in range(5):
                    confirm_dialog = self.page.locator("div[role='alertdialog'], div[data-test-modal], div.artdeco-modal").first
                    if await confirm_dialog.count() == 0 or not await confirm_dialog.is_visible():
                        break
                    
                    discard_btn = confirm_dialog.locator(
                        "button[data-control-name='discard_application_confirm_btn'], "
                        "button:has-text('Discard'), "
                        "button.artdeco-button--primary:has-text('Discard')"
                    ).first
                    
                    if await discard_btn.count() > 0 and await discard_btn.is_visible():
                        await discard_btn.click()
                        print("  🗑️ Clicked 'Discard' - draft was NOT saved.")
                        await asyncio.sleep(0.5)
                        break
        except Exception as e:
            print(f"  ⚠️ Modal close note: {e}")

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Executes the complete LinkedIn job application session."""
        print(f"\n{'='*60}")
        print(f"🚀 Launching LinkedIn Easy Apply Agent")
        print(f"  • Mode: {'DRY RUN (Preview)' if self.dry_run else 'LIVE AUTO-APPLY'}")
        print(f"  • Session Limit: {self.limit} applications")
        print(f"{'='*60}\n")

        self.page = await self.engine.start()
        is_logged_in = await self.authenticate_or_check_session()
        if not is_logged_in:
            print("❌ Error: LinkedIn is not logged in on the Chrome session.")
            print("👉 Please log into LinkedIn in the opened Chrome window and re-run.")
            await self.engine.close()
            return

        print("✅ Authenticated on LinkedIn.")
        self.scanner = LinkedInJobScanner(self.page)

        keywords_list = keywords or self.config.search_keywords
        preference = self.config.search_preference

        search_targets = []
        if location:
            search_targets.append({"location": location, "remote": False, "label": location})
        else:
            if preference == "remote_first":
                search_targets.append({"location": "India", "remote": True, "label": "Remote (India) [1st Preference]"})
                search_targets.append({"location": self.config.search_location, "remote": False, "label": "Bengaluru [2nd Preference]"})
            else:
                search_targets.append({"location": self.config.search_location, "remote": False, "label": "Bengaluru"})

        total_processed = 0

        for target in search_targets:
            if total_processed >= self.limit:
                break

            target_loc = target["location"]
            target_remote = target["remote"]
            target_label = target["label"]

            for keyword in keywords_list:
                if total_processed >= self.limit:
                    break

                for page_num in [1, 2, 3, 4]:
                    if total_processed >= self.limit:
                        break

                    print(f"\n🔍 Searching for: '{keyword}' in '{target_label}' (Page {page_num})")
                    postings = await self.search_jobs(keyword, target_loc, remote=target_remote, page_num=page_num)
                    print(f"📋 Found {len(postings)} potential job listings on this page.")
                    if not postings:
                        break

                    for job in postings:
                        if total_processed >= self.limit:
                            print("🛑 Application session limit reached.")
                            break

                        if self.tracker.is_already_applied(job.job_id, job.title, job.company):
                            print(f"⏭️ Already processed: {job.title} @ {job.company}")
                            continue

                        print(f"\n👉 [{total_processed + 1}/{self.limit}] Opening: {job.title} at {job.company}")
                        success = await self.apply_to_job(job)
                        if success:
                            total_processed += 1

                        await asyncio.sleep(3.5)

        self._print_summary()
        await self.engine.close()

    def _print_summary(self):
        """Displays formatted session summary and per-job Q&A audit."""
        summary = self.tracker.get_summary()
        print("\n" + "="*60)
        print("📊 Application Session Summary")
        print(f"  • Total Tracked Records : {summary['total_records']}")
        print(f"  • Live Submitted Jobs   : {summary['applied']}")
        print(f"  • Dry Run Verified      : {summary['dry_run']}")
        print(f"  • Skipped               : {summary['skipped']}")
        print(f"  • Incomplete / Blocked  : {summary['failed']}")
        print(f"  • Database File         : {self.tracker.db_path}")
        print(f"  • Spreadsheet File      : {self.tracker.csv_path}")
        print("="*60)

        if self.session_submitted_jobs:
            print("\n📋 Submitted Applications in this Batch:")
            for idx, job in enumerate(self.session_submitted_jobs, 1):
                print(f"\n[{idx}] {job['title']} @ {job['company']}")
                print(f"    🏢 Workplace  : {job.get('workplace_type', 'N/A')}")
                if job.get('hiring_manager_name'):
                    print(f"    👤 Hirer      : {job['hiring_manager_name']} ({job.get('hiring_manager_url', '')})")
                else:
                    print(f"    👤 Hirer      : Not publicly listed")
                if job.get('key_skills'):
                    print(f"    🛠️ Skills     : {job['key_skills']}")
                print(f"    🔗 URL        : {job['url']}")
                print(f"    📸 Screenshot : {job['screenshot']}")
                if job.get("answers_filled"):
                    print("    📝 Questions & Answers Filled:")
                    for q, a in job["answers_filled"].items():
                        print(f"       • {q[:50]}: {a}")
            print("\n" + "="*60 + "\n")

        if self.jobs_needing_review:
            print("\n" + "!"*60)
            print("📝 Jobs Flagged for Your Manual Review (Complex Questions / Use-Cases):")
            for idx, job in enumerate(self.jobs_needing_review, 1):
                print(f"[{idx}] {job['title']} @ {job['company']}")
                print(f"    🔗 URL: {job['url']}")
                print(f"    💡 Reason: {job['reason']}")
            print("!"*60 + "\n")

# Alias for backward compatibility
JobApplicationAgent = LinkedInApplicationAgent
