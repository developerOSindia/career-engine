"""
High-Speed Form Filler for LinkedIn Easy Apply dialogs.
Supports dynamic learning: answers questions from memory (profile_config.json),
uses Gemini AI (gemini-3.6-flash) for unknown questions, handles dropdowns,
radio groups, text/number inputs, and records learned answers.
"""
import asyncio
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional
from playwright.async_api import Locator
from ai.ai_solver import UnifiedAISolver as AISolver
from core.config_loader import get_config

from core.question_solver import question_solver

class LinkedInFormFiller:
    def __init__(self, profile_data: Optional[dict] = None, dry_run: bool = False, profile_path: Optional[str] = None):
        config = get_config()
        self.profile = profile_data or config.profile
        self.profile_path = profile_path or str(config.profile_path)
        self.dry_run = dry_run
        self.personal = self.profile.get("personal_info", {})
        self.work = self.profile.get("work_summary", {})
        self.education = self.profile.get("education", {})
        self.skills = self.profile.get("skills_years_experience", {})
        self.defaults = self.profile.get("screening_defaults", {})
        self.custom_answers = self.profile.get("custom_answers", {})
        self.question_solver = question_solver
        self.ai = AISolver(self.profile)
        self.current_job_answers = {}

    def get_and_clear_job_answers(self) -> dict:
        """Returns the dictionary of questions and answers filled for the current job."""
        ans = dict(self.current_job_answers)
        self.current_job_answers.clear()
        return ans

    def record_job_answer(self, question: str, answer: str):
        """Records a question and filled answer for audit/reporting."""
        if question and answer:
            self.current_job_answers[question.strip()] = str(answer).strip()

    def save_learned_answer(self, question: str, answer: str):
        """Persists learned answers to profile_config.json so it is remembered forever."""
        clean_q = question.strip()
        clean_ans = str(answer).strip()
        if clean_ans.lower() in ("on", "true"):
            clean_ans = "Yes"
        self.custom_answers[clean_q] = clean_ans
        self.profile["custom_answers"] = self.custom_answers
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=2, ensure_ascii=False)
            print(f"  💾 Saved to memory for future jobs: '{clean_q[:40]}' -> '{clean_ans}'")
        except Exception as e:
            print(f"  ⚠️ Could not save custom answer: {e}")

    def resolve_question_answer(
        self,
        question_text: str,
        field_type: str = "text",
        options: Optional[List[str]] = None,
        is_long_form: bool = False
    ) -> Optional[str]:
        """Infers the best answer using centralized QuestionSolver, candidate facts, and AI."""
        if not question_text:
            return None
        q = question_text.strip().lower()

        # Handle long-form scenarios / complex architectural questions via Gemini
        if is_long_form:
            for saved_q, saved_ans in self.custom_answers.items():
                if saved_q.strip().lower() == q:
                    return str(saved_ans)
            try:
                ai_ans = self.ai.solve_question(question_text, field_type=field_type, is_long_form=True)
                if ai_ans and len(ai_ans.strip()) > 20:
                    self.save_learned_answer(question_text, ai_ans)
                    return ai_ans
            except Exception as e:
                print(f"  ⚠️ Gemini scenario error: {e}")
            return None

        # Strict rules enforcement via centralized QuestionSolver:
        # - Expected CTC: 40 LPA (Never any other number)
        # - Current CTC: 30 LPA (Never any other number)
        # - Notice period: "60 days and negotiable" (options) / "30 days" (text)
        # - Experience: 5 years (PySpark, AWS, Databricks, SQL)
        ans = self.question_solver.resolve(
            question_text=question_text,
            field_type=field_type,
            options=options
        )
        if ans:
            return str(ans)

        # Fallback to AI solver if needed
        try:
            ai_ans = self.ai.solve_question(question_text, field_type=field_type, options=options)
            if ai_ans:
                self.save_learned_answer(question_text, ai_ans)
                return str(ai_ans)
        except Exception as e:
            print(f"  ⚠️ AI fallback note: {e}")

        return None

    async def fill_current_step(self, modal: Locator) -> bool:
        """Fills all fields in current step with auto-scrolling."""
        # Scroll modal to top first
        try:
            await modal.evaluate(r'''el => {
                const scrollable = el.querySelector('div[tabindex="0"], .jobs-easy-apply-modal__content, div[class*="content"]') || el;
                scrollable.scrollTop = 0;
            }''')
        except Exception:
            pass

        # 1. Handle ALL Dropdowns (<select>)
        await self._fill_select_dropdowns(modal)

        # 2. Fill Phone Number specifically
        await self._fill_phone_inputs(modal)

        # 3. Fill Text & Number Inputs
        await self._fill_text_inputs(modal)

        # 4. Handle Fieldsets (Radio buttons)
        await self._fill_radio_groups(modal)

        # 5. Handle Checkboxes (Uncheck 'Follow company')
        await self._fill_checkboxes(modal)

        # 6. Resume file upload if needed
        await self._handle_resume_upload(modal)

        return True

    async def _fill_select_dropdowns(self, modal: Locator):
        """Intelligently handles all <select> elements in the modal dialog."""
        try:
            selects = await modal.locator("select").all()
            for sel in selects:
                if not await sel.is_visible():
                    await sel.scroll_into_view_if_needed()

                options = await sel.evaluate(r'''el => Array.from(el.options).map(o => ({ value: o.value, text: o.text.trim() }))''')
                if not options:
                    continue

                curr_val = await sel.input_value()
                curr_text = await sel.evaluate(r'''el => el.options[el.selectedIndex] ? el.options[el.selectedIndex].text.trim() : '' ''')

                # Get question text associated with select
                q_text = await sel.evaluate(r'''el => {
                    let label = el.labels && el.labels[0] ? el.labels[0].innerText : '';
                    if (label) return label;
                    let p = el.parentElement;
                    while (p && p.tagName !== 'DIALOG' && p.tagName !== 'FORM') {
                        let text = p.innerText || '';
                        let lines = text.split('\n').map(l => l.trim()).filter(l => l && !l.includes('characters') && !l.includes('Select an option'));
                        if (lines.length > 0) return lines[0];
                        p = p.parentElement;
                    }
                    return '';
                }''')
                q_lower = q_text.lower()

                # Check if it's country code
                is_country_code = any("india (+91)" in o["text"].lower() or ("india" in o["text"].lower() and "91" in o["text"]) for o in options)
                if is_country_code:
                    for opt in options:
                        t = opt["text"].lower()
                        if "india (+91)" in t or ("india" in t and "91" in t):
                            if curr_val != opt["value"]:
                                await sel.select_option(opt["value"])
                                print("  🇮🇳 Selected Country Code: India (+91)")
                            break
                    continue

                # If already selected to a valid option (not placeholder), continue
                if curr_val and curr_text and not any(ph in curr_text.lower() for ph in ["select an option", "please select", "choose"]):
                    continue

                # Determine best option to select
                matched_val = None
                opt_texts = [o["text"] for o in options if o["text"]]

                ans = self.resolve_question_answer(q_text, field_type="select", options=opt_texts)
                if ans:
                    ans_lower = ans.lower()
                    for opt in options:
                        opt_lower = opt["text"].lower()
                        if ans_lower == opt_lower or ans_lower in opt_lower or opt_lower in ans_lower:
                            matched_val = opt["value"]
                            break

                # If no direct match, check common question categories
                if not matched_val:
                    if any(term in q_lower for term in ["sponsorship", "require visa"]):
                        for opt in options:
                            if opt["text"].lower() == "no" or opt["text"].lower().startswith("no"):
                                matched_val = opt["value"]
                                break
                    elif any(term in q_lower for term in ["authorized", "bachelor", "degree", "relocate", "commute"]):
                        for opt in options:
                            t = opt["text"].lower()
                            if t == "yes" or "bachelor" in t:
                                matched_val = opt["value"]
                                break
                    elif "notice" in q_lower:
                        notice_ans = self.question_solver.resolve_notice_period(q_text, field_type="select", options=opt_texts)
                        for opt in options:
                            if notice_ans.lower() in opt["text"].lower() or opt["text"].lower() in notice_ans.lower():
                                matched_val = opt["value"]
                                break
                    elif "english" in q_lower or "proficiency" in q_lower:
                        for opt in options:
                            t = opt["text"].lower()
                            if any(w in t for w in ["professional", "fluent", "native", "advanced"]):
                                matched_val = opt["value"]
                                break

                # Fallback to first non-empty option
                if not matched_val:
                    for opt in options:
                        if opt["value"] and not any(ph in opt["text"].lower() for ph in ["select an option", "choose"]):
                            matched_val = opt["value"]
                            break

                if matched_val:
                    await sel.select_option(matched_val)
                    selected_label = [o["text"] for o in options if o["value"] == matched_val]
                    lbl = selected_label[0] if selected_label else matched_val
                    self.record_job_answer(q_text or "Dropdown", lbl)
                    print(f"  🔽 Dropdown '{q_text[:35]}...' -> {lbl}")
        except Exception as e:
            print(f"  ⚠️ Error handling dropdown: {e}")

    async def _fill_phone_inputs(self, modal: Locator):
        """Fills phone number using native Playwright typing."""
        try:
            phone_inputs = await modal.locator("input[type='tel']").all()
            for p_inp in phone_inputs:
                phone = str(self.personal.get("phone_number", "7839453651"))
                self.record_job_answer("Phone Number", phone)
                curr_val = await p_inp.input_value()
                if curr_val != phone:
                    await p_inp.click()
                    await p_inp.fill(phone)
                    print(f"  📞 Phone Number: {phone}")
        except Exception:
            pass

    async def _fill_text_inputs(self, modal: Locator):
        """Fills text, number, and textarea inputs."""
        try:
            text_inputs = await modal.locator("input[type='text'], input[type='number'], textarea").all()
            for inp in text_inputs:
                if not await inp.is_visible():
                    await inp.scroll_into_view_if_needed()

                max_len_attr = await inp.get_attribute("maxlength")
                max_len = int(max_len_attr) if max_len_attr and max_len_attr.isdigit() else 9999

                q_text = await inp.evaluate(r'''el => {
                    let labelEl = (el.labels && el.labels[0]) ||
                        (el.id ? document.querySelector('label[for="' + el.id + '"]') : null) ||
                        el.closest('.fb-single-line-text, .fb-form-element, .jobs-easy-apply-form-element, div[class*="form-element"]')?.querySelector('label');
                    if (labelEl) return labelEl.innerText.replace(/\s+/g, ' ').trim();

                    let p = el.parentElement;
                    while (p && p.tagName !== 'DIALOG' && p.tagName !== 'FORM') {
                        let lbl = p.querySelector('label');
                        if (lbl) return lbl.innerText.replace(/\s+/g, ' ').trim();
                        let text = (p.innerText || '').replace(/\s+/g, ' ').trim();
                        if (text && (text.includes('?') || text.toLowerCase().includes('how many') || text.toLowerCase().includes('experience'))) {
                            text = text.replace(/\d+\/\d+\s*characters?/gi, '').replace(/\d+\s*of\s*\d+\s*characters?/gi, '').trim();
                            return text;
                        }
                        p = p.parentElement;
                    }
                    return '';
                }''')

                q_lower = q_text.lower()
                is_number = (await inp.get_attribute("type") == "number")
                tag_name = await inp.evaluate("el => el.tagName.toLowerCase()")
                is_textarea = (tag_name == "textarea")
                field_type = "number" if is_number else ("textarea" if is_textarea else "text")

                is_years_question = any(term in q_lower for term in ["how many", "years", "year of", "experience"])

                curr_val = await inp.input_value()
                if curr_val and len(curr_val.strip()) > 0:
                    # Overwrite if current value exceeds maxlength or is non-numeric in a years question
                    if len(curr_val.strip()) <= max_len and not (is_years_question and len(curr_val.strip()) > 4):
                        continue

                # Handle city / location autocomplete specifically
                placeholder = (await inp.get_attribute("placeholder") or "").lower()
                if "city" in q_text.lower() or "city" in placeholder or "location" in placeholder:
                    city = self.personal.get("current_city", "Bengaluru")
                    await inp.click()
                    await inp.fill(city)
                    await asyncio.sleep(0.5)
                    await inp.press("ArrowDown")
                    await inp.press("Enter")
                    print(f"  🏙️ Selected City: {city}")
                    continue

                # Detect if this is a long-form technical scenario (NEVER for years questions or fields with max_len <= 30)
                is_long_form = is_textarea or (
                    max_len > 100 and len(q_text) > 75 and not is_years_question and any(
                        kw in q_lower for kw in [
                            "describe", "explain", "how would you", "what would you", 
                            "pipeline issue", "optimize", "architecture", "what broke", 
                            "use case", "scenario", "cover letter"
                        ]
                    )
                )

                ans = self.resolve_question_answer(q_text, field_type=field_type, is_long_form=is_long_form)
                if ans is None:
                    # If running in an interactive terminal, ask the user directly
                    if sys.stdin and sys.stdin.isatty():
                        try:
                            print(f"\n❓ [Question Query]: '{q_text}' (field: {field_type})")
                            user_ans = input("   👉 Please enter your answer: ").strip()
                            if user_ans:
                                ans = user_ans
                                self.save_learned_answer(q_text, ans)
                        except Exception:
                            pass
                    if ans is None:
                        # For long-form / scenarios, DO NOT fill a naive generic answer like 'Yes'
                        if is_long_form:
                            print(f"  ⚠️ Skipping naive fill for long-form scenario: '{q_text[:50]}...'")
                            continue
                        ans = "5" if is_number else "Yes"

                self.record_job_answer(q_text or "Text Input", str(ans))
                await inp.click()
                await inp.fill(str(ans))
                print(f"  ✍️ Answering '{q_text.strip()[:45]}...' -> {ans}")
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"  ⚠️ Error filling text inputs: {e}")

    async def _fill_radio_groups(self, modal: Locator):
        """Selects appropriate radio button in fieldsets without timeout."""
        try:
            fieldsets = await modal.locator("fieldset").all()
            for fs in fieldsets:
                await fs.scroll_into_view_if_needed()
                radios = await fs.locator("input[type='radio']").all()
                if not radios:
                    continue

                # If already selected, skip
                is_checked = False
                for r in radios:
                    if await r.is_checked():
                        is_checked = True
                        break
                if is_checked:
                    continue

                fs_q = await fs.evaluate(r'''el => {
                    let legend = el.querySelector('legend');
                    if (legend && legend.innerText.trim()) return legend.innerText.trim();
                    return el.previousElementSibling ? el.previousElementSibling.innerText : el.parentElement.innerText;
                }''')
                fs_q_lower = fs_q.lower()

                # Get available radio option labels using accurate multi-level selector
                opt_labels = []
                for r in radios:
                    lbl = await r.evaluate(r'''el => {
                        let lbl = el.closest('label');
                        if (lbl && lbl.innerText.trim()) return lbl.innerText.trim();
                        if (el.id) {
                            let labelEl = document.querySelector('label[for="' + el.id + '"]');
                            if (labelEl && labelEl.innerText.trim()) return labelEl.innerText.trim();
                        }
                        let parent = el.parentElement;
                        if (parent) {
                            let siblingLbl = parent.querySelector('label');
                            if (siblingLbl && siblingLbl.innerText.trim()) return siblingLbl.innerText.trim();
                        }
                        let container = el.closest('.fb-radio, [data-test-form-builder-radio], div');
                        if (container) {
                            let cLbl = container.querySelector('label');
                            if (cLbl && cLbl.innerText.trim()) return cLbl.innerText.trim();
                        }
                        return el.value || '';
                    }''')
                    opt_labels.append(lbl.strip())

                # Consult AI (Gemini first) with exact question and available radio choices
                target_ans = self.resolve_question_answer(fs_q, field_type="radio", options=opt_labels)
                target = target_ans.lower().strip() if target_ans else None

                if not target:
                    if any(w in fs_q_lower for w in ["sponsorship", "require visa", "felony", "crime", "interviewed", "applied before", "previously worked"]):
                        target = "no"
                    elif any(w in fs_q_lower for w in ["gender", "sex"]):
                        target = "male"
                    elif any(w in fs_q_lower for w in ["disability", "handicap"]):
                        target = "no"
                    elif any(w in fs_q_lower for w in ["veteran"]):
                        target = "no"
                    else:
                        target = "yes"

                matched_radio = None
                chosen_text = target
                for idx, r in enumerate(radios):
                    r_text = opt_labels[idx].lower().strip()
                    if target == r_text or (len(target) > 1 and target in r_text) or (target == "no" and "no" in r_text.split()):
                        matched_radio = r
                        chosen_text = opt_labels[idx]
                        print(f"  🔘 Selected '{chosen_text}' for: {fs_q.strip()[:40]}...")
                        break

                if not matched_radio and radios:
                    if target == "no":
                        # Search specifically for radio with 'no'
                        for idx, r in enumerate(radios):
                            if "no" in opt_labels[idx].lower():
                                matched_radio = r
                                chosen_text = opt_labels[idx]
                                break
                    if not matched_radio:
                        matched_radio = radios[0]
                        chosen_text = opt_labels[0] if opt_labels else "Default"
                    print(f"  🔘 Selected '{chosen_text}' for: {fs_q.strip()[:40]}...")

                if matched_radio:
                    self.record_job_answer(fs_q or "Radio Option", chosen_text)
                    # Native in-page event dispatch + label click (avoids hidden element visibility timeout)
                    await matched_radio.evaluate(r'''el => {
                        el.checked = true;
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        const lbl = el.closest('label') || document.querySelector(`label[for="${el.id}"]`) || (el.parentElement ? el.parentElement.querySelector('label') : null);
                        if (lbl) lbl.click();
                    }''')
        except Exception as e:
            print(f"  ⚠️ Error filling radio groups: {e}")

    async def _fill_checkboxes(self, modal: Locator):
        """Unchecks follow company and checks required agreements."""
        try:
            checkboxes = await modal.locator("input[type='checkbox']").all()
            for cb in checkboxes:
                cb_text = await cb.evaluate(r"el => (el.closest('div')?.innerText || '').toLowerCase()")
                if "follow" in cb_text and await cb.is_checked():
                    await cb.uncheck()
                elif any(w in cb_text for w in ["certify", "agree", "confirm", "acknowledge"]) and not await cb.is_checked():
                    await cb.check()
        except Exception:
            pass

    async def _handle_resume_upload(self, modal: Locator, job_title: str = ""):
        """Uploads candidate resume matching the job role if file input is present."""
        try:
            file_inputs = await modal.locator("input[type='file']").all()
            for file_inp in file_inputs:
                resume_path = self.config.get_resume_for_job(job_title)
                abs_path = os.path.abspath(resume_path)
                if os.path.exists(abs_path):
                    await file_inp.set_input_files(abs_path)
                    print(f"  📎 Attached resume: {os.path.basename(abs_path)}")
        except Exception:
            pass

# Backward compatibility alias
FormFiller = LinkedInFormFiller
