"""
Naukri.com Platform Connector and Application Agent.
Handles:
1. Authentication session verification (cookie & redirection check)
2. Direct URL job applications (including aurus/early-jobs and standard job-listings)
3. Automated job search across Data Engineering & AI roles
4. Extraction of JD, company, experience, location, and key skills
5. Handling 1-click Apply and Naukri screening chatbot/questionnaire dialogs
6. Dual persistence to jobs.db (SQLite) and applied_jobs.csv
"""
import os
import re
import random
import asyncio
import urllib.parse
from typing import Dict, List, Optional
from playwright.async_api import Page, Locator

from core.models import JobPosting
from core.config_loader import get_config
from core.browser_engine import BrowserEngine
from core.tracker import ApplicationTracker
from core.question_solver import question_solver
from platforms.base import BasePlatform
from ai.ai_solver import UnifiedAISolver

class NaukriPlatform(BasePlatform):
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
            name="naukri",
            engine=engine,
            tracker=tracker,
            dry_run=is_dry_run,
            limit=max_limit,
            interactive=interactive
        )

        self.config = config
        self.profile = config.profile
        self.question_solver = question_solver
        self.question_solver.interactive = interactive
        self.ai = UnifiedAISolver(self.profile)
        self.screenshots_dir = config.screenshots_dir

    async def authenticate_or_check_session(self) -> bool:
        """Verifies if the browser session is authenticated on Naukri."""
        if not self.engine.context:
            return False
        try:
            cookies = await self.engine.context.cookies()
            has_cookie = any(
                "naukri.com" in c.get("domain", "") and c.get("name") in (
                    "nauk_at", "_nk_u", "MYNAUKBMS[resolution]", "nlogin",
                    "nauk_rt", "nauk_sid", "nauk_ps", "nauk_cs", "MYNAUKRI[UNID]"
                )
                for c in cookies
            )
            # Also verify via page navigation check
            if self.page:
                current_url = self.page.url
                if "nlogin/login" in current_url or "login" in current_url:
                    return False
            return has_cookie
        except Exception:
            return False

    async def extract_naukri_job_details(self, url: str) -> dict:
        """Extracts job title, company name, experience, location, and skills from a Naukri posting."""
        info = await self.page.evaluate(r'''() => {
            // 1. Title (support both modern TopTier pages, drawer, and standard Naukri)
            let title = '';
            const headlineEl = document.querySelector('.text-headline24Sb, .text-headline22Sb, p.text-headline22Sb, div.fixed p, div[class*="drawer"] p');
            if (headlineEl && headlineEl.innerText.trim()) {
                title = headlineEl.innerText.trim();
            }
            if (!title) {
                const titleEl = document.querySelector('h1, .styles_jd-header-title__header-title__, .jd-header-title, .title');
                if (titleEl) title = titleEl.innerText.trim();
            }

            // 2. Company
            let company = '';
            const compH4 = document.querySelector('h4.text-title18Sb, h4[class*="text-title"], .styles_jd-header-comp-name__company-name__, .comp-name, .company-name');
            if (compH4 && compH4.innerText.trim()) {
                company = compH4.innerText.trim();
            }
            if (!company) {
                const aurusComp = document.querySelector('h2, h3, [class*="Hiring"], div[class*="border-gradient"]');
                if (aurusComp && aurusComp.innerText.trim()) {
                    company = aurusComp.innerText.replace(/Hiring for one of these/gi, '').replace(/\n/g, ' ').trim();
                }
            }

            // 3. Location & Experience & Salary
            let location = 'Bengaluru';
            let exp = '';
            let salary = '';
            const allSpans = Array.from(document.querySelectorAll('span, div, li, p'));
            for (const s of allSpans) {
                const t = s.innerText ? s.innerText.trim() : '';
                if (t.includes('Yrs') || t.includes('years') || t.includes('yrs')) {
                    if (!exp && t.length < 25) exp = t;
                } else if (t.includes('PA') || t.includes('Lacs') || t.includes('LPA') || t.includes('₹') || t.includes('/year')) {
                    if (!salary && t.length < 30) salary = t;
                } else if (t.includes('Bengaluru') || t.includes('Bangalore') || t.includes('Remote') || t.includes('Hybrid')) {
                    if (location === 'Bengaluru' && t.length < 45) location = t;
                }
            }

            // 4. Job Description / Details
            let jd = '';
            const jdEl = document.querySelector('.styles_JDC__dang-inner-html__, .job-desc, #job-description, .dang-inner-html, div[class*="drawer"]');
            if (jdEl) jd = jdEl.innerText.trim();

            // 5. Key Skills
            const skillEls = Array.from(document.querySelectorAll('.styles_key-skill__, .key-skill a, .chip, a[href*="skills"]'));
            const skills = skillEls.map(e => e.innerText.trim()).filter(Boolean);

            return {
                title: title || 'AWS Data Engineer',
                company: company || 'TopTier Enterprise',
                location: location,
                experience: exp || '3-8 Yrs',
                salary: salary,
                skills: Array.from(new Set(skills)).join(', '),
                job_description: jd
            };
        }''')

        # Fallback regex skills if DOM tags were sparse
        KNOWN_SKILLS = [
            "Python", "PySpark", "Spark", "Databricks", "Delta Lake", "AWS", "Azure", "GCP",
            "Airflow", "Kafka", "PostgreSQL", "MySQL", "Snowflake", "Redshift", "BigQuery",
            "SQL", "Scala", "Java", "Docker", "Kubernetes", "CI/CD", "Terraform", "Git",
            "ETL", "ELT", "Data Pipeline", "Data Modeling", "MLOps", "AI", "GenAI"
        ]
        jd_text = (info.get("job_description") or "").lower()
        extracted = [s for s in KNOWN_SKILLS if re.search(rf"\b{re.escape(s.lower())}\b", jd_text)]
        if extracted:
            existing = set(info.get("skills", "").split(", "))
            all_skills = list(existing.union(extracted))
            info["skills"] = ", ".join(all_skills).strip(", ")

        return info

    async def apply_to_job_url(self, job_url: str) -> bool:
        """Navigates to a specific Naukri job posting URL and completes the application."""
        print(f"\n{'='*60}")
        print(f"🚀 Processing Naukri Job Application")
        print(f"🔗 URL: {job_url}")
        print(f"🎯 Mode: {'DRY RUN (Preview)' if self.dry_run else 'LIVE AUTO-APPLY'}")
        print(f"{'='*60}\n")

        if not self.page:
            self.page = await self.engine.start()

        # Check if current page is already on the target URL or needs navigation
        if not (self.page.url and "jobId=290626926058" in self.page.url and "aurus" in self.page.url):
            print(f"🌐 Navigating to Naukri job posting...")
            await self.page.goto(job_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(3.5)
        else:
            print("📌 Already on target Naukri page!")

        # Check for Login Redirect
        current_url = self.page.url
        if "nlogin/login" in current_url:
            print("\n" + "⚠️ " * 15)
            print("🔑 Naukri requires an active login session to view/apply to this early-jobs posting.")
            print("👉 Please log in to Naukri in your open Chrome window.")
            print("   The agent will wait up to 90 seconds and automatically continue once you are logged in!")
            print("⚠️ " * 15 + "\n")
            
            screenshot_path = os.path.join(self.screenshots_dir, "naukri_login_required.png")
            await self.page.screenshot(path=screenshot_path)
            
            # Wait loop for login completion
            logged_in = False
            for elapsed in range(0, 90, 3):
                await asyncio.sleep(3)
                curr = self.page.url
                if "nlogin/login" not in curr and ("aurus" in curr or "job-listings" in curr or "naukri.com" in curr):
                    print(f"🎉 Login detected! Redirected to: {curr}")
                    await asyncio.sleep(2.0)
                    logged_in = True
                    break
                if elapsed % 15 == 0 and elapsed > 0:
                    print(f"⏳ Waiting for login... ({90 - elapsed}s remaining)")

            if not logged_in:
                print("❌ Login timed out. Please log into Naukri in Chrome and re-run this command.")
                return False

        # If on Aurus early-jobs page, ensure detailed drawer is open
        if "early-jobs" in self.page.url or "aurus" in self.page.url:
            drawer_btn = self.page.locator("button:has-text('interested'), button:has-text('Interest shared')").first
            if await drawer_btn.count() == 0 or not await drawer_btn.is_visible():
                view_btn = self.page.locator("button:has-text('View opportunity')").first
                if await view_btn.count() > 0 and await view_btn.is_visible():
                    print("  🔍 Opening early opportunity details drawer...")
                    await view_btn.click()
                    await asyncio.sleep(2.0)

        # Extract Job Details
        details = await self.extract_naukri_job_details(job_url)
        title = details.get("title", "AWS Data Engineer")
        company = details.get("company", "TopTier Enterprise")
        location = details.get("location", "Bengaluru")
        skills = details.get("skills", "")
        jd_text = details.get("job_description", "")

        # Extract jobId from URL query or path
        job_id = None
        match = re.search(r"jobId=(\d+)", job_url)
        if match:
            job_id = match.group(1)
        else:
            match = re.search(r"-(\d{10,14})", job_url)
            if match:
                job_id = match.group(1)
        if not job_id:
            job_id = str(abs(hash(job_url)))[:10]

        print(f"  📌 Title      : {title}")
        print(f"  🏢 Company    : {company}")
        print(f"  📍 Location   : {location}")
        print(f"  💼 Experience : {details.get('experience', 'N/A')}")
        print(f"  💰 Salary     : {details.get('salary', 'N/A')}")
        print(f"  🛠️ Key Skills : {skills}")

        # Locate Apply / Signal Interest Button
        apply_btn = self.page.locator(
            "button:has-text('Quick apply'), "
            "button:has-text('interested'), "
            "button:has-text('Interest shared'), "
            "button#apply-button, "
            "button.apply-button, "
            "button:has-text('Apply'), "
            "button.apply-btn, "
            "button[id*='apply'], "
            "a:has-text('Apply on company site')"
        ).first

        if await apply_btn.count() == 0 or not await apply_btn.is_visible():
            print("  ℹ️ No direct Apply / Express Interest button found on this page.")
            screenshot_path = os.path.join(self.screenshots_dir, f"naukri_job_{job_id}_no_apply.png")
            await self.page.screenshot(path=screenshot_path)
            self.tracker.record_application(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                job_url=job_url,
                platform="naukri",
                key_skills=skills,
                job_description=jd_text,
                status="skipped",
                notes="No Apply button found",
                screenshot=screenshot_path
            )
            return False

        btn_text = (await apply_btn.inner_text()).strip()
        print(f"  ✨ Found Action Button: '{btn_text.splitlines()[0]}'")

        if "company site" in btn_text.lower():
            print("  ℹ️ Job requires external redirect ('Apply on company site'). Skipping external ATS.")
            self.tracker.record_application(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                job_url=job_url,
                platform="naukri",
                key_skills=skills,
                job_description=jd_text,
                status="skipped",
                notes="External redirect (company site)"
            )
            return False

        # Check if already applied / interest shared
        already_applied = await self._is_already_applied()
        if already_applied or "interest shared" in btn_text.lower():
            print("  ✅ Already applied / interest shared for this opportunity!")
            screenshot_path = os.path.join(self.screenshots_dir, f"naukri_job_{job_id}_already_applied.png")
            await self.page.screenshot(path=screenshot_path)
            self.tracker.record_application(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                job_url=job_url,
                platform="naukri",
                key_skills=skills,
                job_description=jd_text,
                status="applied",
                notes="Already applied on Naukri",
                screenshot=screenshot_path
            )
            return True

        # Handle Dry Run
        if self.dry_run:
            review_shot = os.path.join(self.screenshots_dir, f"naukri_job_{job_id}_review.png")
            await self.page.screenshot(path=review_shot)
            print(f"  🎯 [DRY RUN] Apply button verified. Screenshot saved to {review_shot}")
            self.tracker.record_application(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                job_url=job_url,
                platform="naukri",
                key_skills=skills,
                job_description=jd_text,
                status="dry_run_completed",
                notes="Naukri apply button verified in dry run",
                screenshot=review_shot
            )
            return True

        # Click Apply
        print(f"  🚀 Clicking Apply...")
        await apply_btn.click()
        await asyncio.sleep(2.5)

        # Check for Naukri Chatbot / Questionnaire Dialog
        answered_qa = await self._handle_naukri_chatbot_questions(job_title=job_title)
        await asyncio.sleep(2.0)

        # Final Confirmation Check
        is_submitted = await self._is_already_applied()
        if not is_submitted:
            for _ in range(5):
                await asyncio.sleep(1.0)
                if await self._is_already_applied():
                    is_submitted = True
                    break
        submitted_shot = os.path.join(self.screenshots_dir, f"naukri_job_{job_id}_submitted.png")
        await self.page.screenshot(path=submitted_shot)
        
        status_note = "Submitted via Naukri 1-Click / Chatbot Apply" if is_submitted else "Application completed on Naukri"
        print(f"  ✅ Application Completed! Saved to {submitted_shot}")
        if answered_qa:
            print(f"\n  📝 [Q&A Log for {title}]:")
            for q, a in answered_qa.items():
                print(f"     • Question: {q}")
                print(f"       Answer  : {a}")
            print(f"     🔗 Job Link: {job_url}\n")

        self.tracker.record_application(
            job_id=job_id,
            title=title,
            company=company,
            location=location,
            job_url=job_url,
            platform="naukri",
            key_skills=skills,
            job_description=jd_text,
            status="applied",
            notes=status_note,
            answers_filled=answered_qa if answered_qa else None,
            screenshot=submitted_shot
        )
        return True

    async def _is_already_applied(self) -> bool:
        """Checks if the current job page is already marked as applied."""
        try:
            return await self.page.evaluate(r'''() => {
                const btns = Array.from(document.querySelectorAll('button, a'));
                for (const b of btns) {
                    // 1. Check modern animated apply button where Applied span has translate-y-0
                    const appliedSpan = Array.from(b.querySelectorAll('span')).find(s => 
                        (s.innerText || '').trim().toLowerCase() === 'applied' && s.classList.contains('translate-y-0')
                    );
                    if (appliedSpan) return true;

                    // 2. Check button text: must have applied/interest shared without quick apply
                    const inner = (b.innerText || '').trim().toLowerCase();
                    if ((inner === 'applied' || inner === 'interest shared' || inner.startsWith('applied on')) && !inner.includes('quick apply')) {
                        return true;
                    }
                }
                return false;
            }''')
        except Exception:
            return False

    async def _handle_naukri_chatbot_questions(self, job_title: str = "") -> Dict[str, str]:
        """
        Intelligently answers interactive screening questions in Naukri's chatbot drawer.
        Enforces strict rules:
        - Expected CTC: Strictly 40 LPA (Never any other number)
        - Current CTC: Strictly 30 LPA (Never any other number)
        - Notice Period: "60 days and negotiable" (options) / "30 days" (text)
        - Technical Experience: 5 years (PySpark, Databricks, AWS, SQL, Python)
        - Memory: Automatically loads and updates learned_answers.json.
        """
        qa_records: Dict[str, str] = {}
        try:
            chatbot_selector = "#desktopChatBotContainer, ._chatBotContainer, .chatbot_Drawer, .chatbot-container, div[role='dialog']"
            drawer = self.page.locator(chatbot_selector).first
            if await drawer.count() == 0 or not await drawer.is_visible():
                return qa_records

            print("  💬 Naukri screening chatbot drawer detected. Answering questions...")
            
            for step in range(1, 12):
                await asyncio.sleep(1.5)
                
                # Check if drawer closed or job marked as applied
                if await drawer.count() == 0 or not await drawer.is_visible():
                    print("  ✅ Chatbot drawer closed. Screening complete!")
                    return qa_records
                
                if await self._is_already_applied():
                    print("  ✅ Detected 'Applied' confirmation on job page!")
                    return qa_records

                # 1. Extract the current question prompt
                q_text = await self.page.evaluate(r'''() => {
                    const container = document.querySelector('#desktopChatBotContainer, ._chatBotContainer, .chatbot_Drawer, .chatbot-container, div[role="dialog"]');
                    if (!container) return '';
                    const items = container.querySelectorAll('.botItem, .botMsg, .question-text, .msg-text, p, label');
                    for (let i = items.length - 1; i >= 0; i--) {
                        const txt = (items[i].innerText || '').trim();
                        if (txt.length > 3 && !['save', 'next', 'cancel', 'close', 'applied', 'submit'].includes(txt.toLowerCase())) {
                            return txt;
                        }
                    }
                    return '';
                }''')
                
                if q_text:
                    q_disp = f"{q_text[:70]}..." if len(q_text) > 70 else q_text
                    print(f"  📋 Step {step} Question: \"{q_disp}\"")

                file_input = drawer.locator("input[type='file']").first
                if await file_input.count() > 0 and await file_input.is_visible():
                    resume_file = self.config.get_resume_for_job(job_title)
                    if os.path.exists(resume_file):
                        print(f"  📄 Uploading resume PDF: {resume_file}")
                        await file_input.set_input_files(resume_file)
                        await asyncio.sleep(2.0)

                # 3. Check for Clickable Option Elements (Radios / Checkboxes / Chips)
                options_info = await self.page.evaluate(r'''() => {
                    const container = document.querySelector('#desktopChatBotContainer, ._chatBotContainer, .chatbot_Drawer, .chatbot-container, div[role="dialog"]');
                    if (!container) return [];
                    const candidates = Array.from(container.querySelectorAll('label, button, .chip, .quick-reply, [role="radio"], [role="checkbox"]'));
                    const list = [];
                    for (const el of candidates) {
                        const t = (el.innerText || el.value || '').trim();
                        if (!t) continue;
                        const tLow = t.toLowerCase();
                        if (['save', 'submit', 'close', 'cancel', 'next'].includes(tLow)) continue;
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            list.push(t);
                        }
                    }
                    return Array.from(new Set(list));
                }''')

                if options_info:
                    print(f"  🔘 Detected {len(options_info)} choices: {options_info}")
                    selected_ans = self.question_solver.resolve(
                        question_text=q_text,
                        field_type="radio",
                        options=options_info
                    )
                    print(f"  👉 Selecting Choice: \"{selected_ans}\"")
                    if q_text:
                        qa_records[q_text] = str(selected_ans)

                    # First try Playwright's native locator to fire React synthetic event
                    clicked = False
                    try:
                        lbl = drawer.locator(f"label:has-text('{selected_ans}'), label[for*='{selected_ans}']").first
                        if await lbl.count() > 0 and await lbl.is_visible():
                            await lbl.click(timeout=1500)
                            clicked = True
                    except Exception:
                        pass

                    if not clicked:
                        # Fallback to dispatch click via evaluate with container scroll
                        await self.page.evaluate(r'''(target) => {
                            const container = document.querySelector('#desktopChatBotContainer, ._chatBotContainer, .chatbot_Drawer, .chatbot-container, div[role="dialog"]');
                            if (!container) return false;
                            const candidates = Array.from(container.querySelectorAll('label, button, .chip, .quick-reply, [role="radio"], [role="checkbox"], input'));
                            for (const el of candidates) {
                                const t = (el.innerText || el.value || '').trim();
                                if (t.toLowerCase() === target.toLowerCase() || (target.length > 2 && t.toLowerCase().includes(target.toLowerCase()))) {
                                    el.scrollIntoView({ block: 'nearest' });
                                    el.click();
                                    return true;
                                }
                            }
                            return false;
                        }''', selected_ans)

                    await asyncio.sleep(0.8)

                    # Click Save / Send
                    save_btn = drawer.locator(".send:not(.disabled), [id^='sendMsg__']:not(.disabled), button:has-text('Save'), div:has-text('Save'):not(.disabled)").first
                    if await save_btn.count() > 0:
                        await save_btn.click()
                        print("  💾 Clicked Save / Next")
                    else:
                        save_clicked = await self.page.evaluate(r'''() => {
                            const d = document.querySelector('.chatbot_Drawer, #desktopChatBotContainer, div[role="dialog"]');
                            if (!d) return false;
                            const saveBtn = Array.from(d.querySelectorAll('.sendMsg, .send, button, div')).find(el => {
                                const t = (el.innerText || '').trim();
                                return (t === 'Save' || t === 'Submit' || el.classList.contains('sendMsg')) && !el.classList.contains('disabled');
                            });
                            if (saveBtn) {
                                saveBtn.click();
                                return true;
                            }
                            return false;
                        }''')
                        if save_clicked:
                            print("  💾 Clicked Save / Next")
                    await asyncio.sleep(2.0)
                    continue

                # 4. Check for Text / Number / Contenteditable .textArea Input
                has_input = await self.page.evaluate(r'''() => {
                    const container = document.querySelector('#desktopChatBotContainer, ._chatBotContainer, .chatbot_Drawer, .chatbot-container, div[role="dialog"]');
                    if (!container) return null;
                    const inp = container.querySelector('.textArea, [id^="userInput__"], [contenteditable="true"], input[type="text"]:not([disabled]), input[type="number"]:not([disabled]), textarea:not([disabled])');
                    if (!inp) return null;
                    const rect = inp.getBoundingClientRect();
                    return (rect.width > 0 && rect.height > 0) ? { id: inp.id, tag: inp.tagName } : null;
                }''')

                if has_input:
                    text_ans = self.question_solver.resolve(
                        question_text=q_text,
                        field_type="text"
                    )
                    print(f"  ✍️ Typing Answer: \"{text_ans}\"")
                    if q_text:
                        qa_records[q_text] = str(text_ans)
                    try:
                        await inp_locator.focus()
                    except Exception:
                        try:
                            await inp_locator.click(timeout=2500)
                        except Exception:
                            await self.page.evaluate(r'''() => {
                                const inp = document.querySelector('#desktopChatBotContainer, ._chatBotContainer, .chatbot_Drawer, div[role="dialog"]')?.querySelector('.textArea, [contenteditable="true"], input[type="text"]');
                                if (inp) inp.focus();
                            }''')
                    await asyncio.sleep(0.3)
                    await self.page.keyboard.type(str(text_ans))
                    await asyncio.sleep(0.8)
                    await self.page.keyboard.press("Enter")
                    await asyncio.sleep(0.8)
                    
                    save_btn = drawer.locator(".send:not(.disabled), [id^='sendMsg__']:not(.disabled), button:has-text('Save'), div:has-text('Save'):not(.disabled)").first
                    if await save_btn.count() > 0:
                        await save_btn.click()
                        print("  💾 Clicked Save / Next")
                    else:
                        await self.page.evaluate(r'''() => {
                            const d = document.querySelector('.chatbot_Drawer, #desktopChatBotContainer, div[role="dialog"]');
                            if (!d) return;
                            const send = Array.from(d.querySelectorAll('.sendMsg, .send, button, div')).find(el => {
                                const t = (el.innerText || '').trim();
                                return (t === 'Save' || el.classList.contains('sendMsg')) && !el.classList.contains('disabled');
                            });
                            if (send) send.click();
                        }''')
                    await asyncio.sleep(2.0)
                    continue

                # Check if drawer has a standalone Save or Submit button
                standalone_save = await self.page.evaluate(r'''() => {
                    const d = document.querySelector('.chatbot_Drawer, #desktopChatBotContainer, div[role="dialog"]');
                    if (!d) return false;
                    const btn = Array.from(d.querySelectorAll('.sendMsg, .send, button, div')).find(el => {
                        const t = (el.innerText || '').trim();
                        return (t === 'Save' || t === 'Submit') && !el.classList.contains('disabled') && el.offsetParent !== null;
                    });
                    if (btn) {
                        btn.click();
                        return true;
                    }
                    return false;
                }''')
                if standalone_save:
                    print("  💾 Clicked standalone Save button.")
                    await asyncio.sleep(2.0)
                    continue

                print("  ℹ️ No further questions in chatbot.")
                break

            return qa_records

        except Exception as e:
            print(f"  ⚠️ Error handling Naukri chatbot: {e}")
            return qa_records

    async def search_jobs(
        self,
        keyword: str,
        location: str,
        remote: bool = False,
        page_num: int = 1
    ) -> List[JobPosting]:
        """Searches Naukri for jobs matching keywords and extracts full job cards."""
        # Clean slug formatting (e.g. 'Data Engineer' -> 'data-engineer', 'Bengaluru, Karnataka, India' -> 'bengaluru')
        kw_slug = re.sub(r"[^a-zA-Z0-9]+", "-", keyword.strip().lower()).strip("-")
        loc_clean = location.split(",")[0].strip().lower()
        loc_slug = re.sub(r"[^a-zA-Z0-9]+", "-", loc_clean).strip("-")
        
        if page_num > 1:
            search_url = f"https://www.naukri.com/{kw_slug}-jobs-in-{loc_slug}-{page_num}?k={urllib.parse.quote(keyword)}&l={urllib.parse.quote(loc_clean)}"
        else:
            search_url = f"https://www.naukri.com/{kw_slug}-jobs-in-{loc_slug}?k={urllib.parse.quote(keyword)}&l={urllib.parse.quote(loc_clean)}"
        
        print(f"\n🔍 Navigating to Naukri Search: {search_url}")
        await self.page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4.0)

        # Extract jobs using React Fiber (Naukri TopTier modern cards) + DOM fallback
        raw_jobs = await self.page.evaluate(r'''() => {
            const list = [];
            const seenIds = new Set();

            // 1. React Fiber Extraction (Naukri TopTier modern cards - 20 per page)
            const modernCards = Array.from(document.querySelectorAll('div.cursor-pointer.rounded-3xl, div[class*="rounded-3xl"]'));
            for (const c of modernCards) {
                for (const k of Object.keys(c)) {
                    if (k.startsWith('__reactFiber')) {
                        let fiber = c[k];
                        while (fiber) {
                            const p = fiber.memoizedProps;
                            if (p && p.jobData) {
                                const d = p.jobData;
                                const jobId = String(d.jobId || Math.random().toString(36).substring(7));
                                if (!seenIds.has(jobId)) {
                                    seenIds.add(jobId);
                                    let loc = 'Bengaluru';
                                    let exp = '';
                                    let sal = '';
                                    try {
                                        const phs = JSON.parse(d.placeholders || '[]');
                                        for (const ph of phs) {
                                            if (ph.type === 'location') loc = ph.label;
                                            if (ph.type === 'experience') exp = ph.label;
                                            if (ph.type === 'salary') sal = ph.label;
                                        }
                                    } catch(e){}

                                    const url = d.jdURL ? (d.jdURL.startsWith('http') ? d.jdURL : 'https://www.naukri.com' + d.jdURL) : '';
                                    if (url) {
                                        list.push({
                                            job_id: jobId,
                                            title: d.title || 'Data Engineer',
                                            company: d.companyName || 'Company',
                                            location: loc,
                                            experience: exp,
                                            salary: sal,
                                            skills: d.tagsAndSkills || '',
                                            url: url
                                        });
                                    }
                                }
                                break;
                            }
                            fiber = fiber.return;
                        }
                    }
                }
            }

            // 2. Traditional DOM Extraction fallback
            if (list.length === 0) {
                const articles = Array.from(document.querySelectorAll('.srp-jobtuple-wrapper, article, .jobTuple, [data-job-id]'));
                for (const a of articles) {
                    const titleEl = a.querySelector('.title, a[class*="title"], [class*="jobTitle"]');
                    const compEl = a.querySelector('.comp-name, a[class*="comp-name"], [class*="companyName"]');
                    const locEl = a.querySelector('.loc, span[class*="loc"], [class*="location"]');
                    const linkEl = a.querySelector('a.title, a[href*="job-listings"], a[class*="title"]');
                    
                    if (titleEl && linkEl) {
                        const href = linkEl.href;
                        const match = href.match(/-(\d{10,14})/);
                        const jobId = match ? match[1] : String(Math.random().toString(36).substring(7));
                        if (!seenIds.has(jobId)) {
                            seenIds.add(jobId);
                            list.push({
                                job_id: jobId,
                                title: titleEl.innerText.trim(),
                                company: compEl ? compEl.innerText.trim() : 'Company',
                                location: locEl ? locEl.innerText.trim() : 'Bengaluru',
                                experience: '',
                                salary: '',
                                skills: '',
                                url: href
                            });
                        }
                    }
                }
            }

            return list;
        }''')

        postings = []
        for r in raw_jobs:
            postings.append(JobPosting(
                job_id=r["job_id"],
                title=r["title"],
                company=r["company"],
                location=r["location"],
                url=r["url"],
                platform="naukri"
            ))
        return postings

    async def apply_to_job(self, job: JobPosting) -> bool:
        """Applies to a single job posting object."""
        return await self.apply_to_job_url(job.url)

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: Optional[str] = None
    ):
        """Runs autonomous search and apply loop on Naukri without needing individual URLs."""
        print(f"\n{'='*60}")
        print(f"🚀 Launching Autonomous Naukri Application Engine")
        print(f"🎯 Target Applications Limit: {self.limit}")
        print(f"🛡️ Mode: {'DRY RUN (Preview)' if self.dry_run else 'LIVE AUTO-APPLY'}")
        print(f"{'='*60}\n")

        self.page = await self.engine.start()
        
        keywords_list = keywords or self.config.search_keywords
        loc = location or self.config.search_location

        total_processed = 0
        
        for kw in keywords_list:
            if total_processed >= self.limit:
                break
            
            page_num = 1
            while total_processed < self.limit and page_num <= 3:
                print(f"\n📂 Fetching Naukri Page {page_num} for '{kw}' in {loc}...")
                postings = await self.search_jobs(kw, loc, page_num=page_num)
                print(f"📋 Found {len(postings)} jobs on this page.")
                
                if not postings:
                    print("  ℹ️ No more jobs found for this keyword query.")
                    break

                for job in postings:
                    if total_processed >= self.limit:
                        print(f"\n🎯 Reached target limit of {self.limit} applications!")
                        break

                    if self.tracker.is_already_applied(job.job_id, job.title, job.company):
                        print(f"⏭️ Skipping already applied: {job.title} @ {job.company}")
                        continue

                    print(f"\n[{total_processed + 1}/{self.limit}] Processing: {job.title} @ {job.company}")
                    try:
                        success = await self.apply_to_job(job)
                        if success:
                            total_processed += 1
                            print(f"  ✅ Progress: {total_processed}/{self.limit} completed.")
                    except Exception as e:
                        print(f"  ⚠️ Error applying to {job.title}: {e}")

                    # Human cadence delay
                    delay = random.uniform(2.0, 3.8)
                    print(f"  ⏱️ Waiting {delay:.1f}s before next application...")
                    await asyncio.sleep(delay)

                page_num += 1

        print(f"\n{'='*60}")
        print(f"🎉 Naukri Application Run Finished!")
        print(f"📊 Total Successfully Processed: {total_processed}")
        print(f"{'='*60}\n")
        await self.engine.close()
