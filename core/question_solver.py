"""
Universal Question Solver & Candidate Knowledge Engine.
Provides centralized question-answering across all job boards:
Naukri, LinkedIn, Hirist, Instahyre, Indeed, Glassdoor.

Enforced Strict Business Rules:
- Expected CTC: Strictly 40 LPA (40 Lakhs). Never any other number.
- Current CTC: Strictly 30 LPA (30 Lakhs). Never any other number.
- Notice Period:
  - Selectable / Options / Dropdown: Strictly "60 days and negotiable" (or best 60-day match).
  - Text / Number Column: Strictly "30 days" (or "30").
- Memory: Automatically loads and updates learned_answers.json.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("applywise.solver")
logger.setLevel(logging.INFO)

RESUME_ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = RESUME_ROOT / "profile_config.json"
LEARNED_ANSWERS_PATH = RESUME_ROOT / "learned_answers.json"


class QuestionSolver:
    """Centralized inference engine for job application screening forms."""

    def __init__(
        self,
        profile_path: Path = PROFILE_PATH,
        learned_path: Path = LEARNED_ANSWERS_PATH,
        interactive: bool = False,
    ):
        self.profile_path = profile_path
        self.learned_path = learned_path
        self.interactive = interactive
        self.profile: Dict[str, Any] = self._load_json(self.profile_path)
        self.learned_answers: Dict[str, str] = self._load_json(self.learned_path)

        self.personal = self.profile.get("personal_info", {})
        self.work = self.profile.get("work_summary", {})
        self.education = self.profile.get("education", {})
        self.skills = self.profile.get("skills_years_experience", {})
        self.defaults = self.profile.get("screening_defaults", {})

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading {path}: {e}")
        return {}

    def save_learned_answer(self, question: str, answer: str) -> None:
        """Persists a new question-answer pair so it is remembered forever."""
        clean_q = question.strip()
        clean_ans = str(answer).strip()
        self.learned_answers[clean_q] = clean_ans
        try:
            with open(self.learned_path, "w", encoding="utf-8") as f:
                json.dump(self.learned_answers, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Learned new Q&A: '{clean_q[:45]}' -> '{clean_ans}'")
        except Exception as e:
            logger.warning(f"Could not persist learned answer: {e}")

    # =========================================================================
    # Strict Rule Resolvers
    # =========================================================================

    def resolve_notice_period(
        self,
        question_text: str,
        field_type: str = "text",
        options: Optional[List[str]] = None,
    ) -> str:
        """
        Rule:
        - Selectable options: "60 days and negotiable" (or best 60-day / 2-month match)
        - Text column: "30 days" (or "30")
        """
        q = question_text.lower()
        is_options = field_type in ("radio", "select", "dropdown") or (options and len(options) > 1)

        if is_options and options:
            # 1. Look for explicit "60 days and negotiable"
            for opt in options:
                opt_l = opt.lower()
                if "60" in opt_l and "negotiable" in opt_l:
                    return opt

            # 2. Look for "60 days" or "2 months" or "serving"
            for opt in options:
                opt_l = opt.lower()
                if "60 days" in opt_l or "60" in opt_l or "2 month" in opt_l:
                    return opt

            # 3. Look for "serving notice" or "negotiable"
            for opt in options:
                opt_l = opt.lower()
                if "serving" in opt_l or "negotiable" in opt_l:
                    return opt

            # 4. Fallback to 1 month or 30 days if only shorter choices exist
            for opt in options:
                opt_l = opt.lower()
                if "30" in opt_l or "1 month" in opt_l:
                    return opt

            return options[0]

        # Text input rules
        if "month" in q:
            return "1"
        if "day" in q:
            return "30"
        return "30 days"

    def resolve_ctc(
        self,
        question_text: str,
        field_type: str = "text",
        options: Optional[List[str]] = None,
    ) -> str:
        """
        Rule:
        - Expected CTC: Strictly 40 LPA
        - Current CTC: Strictly 30 LPA
        - Never return any other number!
        """
        q = question_text.lower()
        is_expected = any(k in q for k in ["expect", "desired", "target", "looking for", "budget"])

        target_num = "40" if is_expected else "30"
        target_full = "4000000" if is_expected else "3000000"
        target_lpa_text = f"{target_num} LPA"

        # Check options matching
        if options:
            # 1. Exact number/LPA match
            for opt in options:
                opt_l = opt.lower().strip()
                if opt_l in [f"{target_num} lpa", f"{target_num} lakhs", f"{target_num}l", target_num, target_full]:
                    return opt

            # 2. Starting range for target (e.g. "40-50", "40 to 50", "30-40")
            for opt in options:
                opt_l = opt.lower().strip()
                if opt_l.startswith(f"{target_num}-") or opt_l.startswith(f"{target_num} -") or opt_l.startswith(f"{target_num} to"):
                    return opt

            # 3. Range enclosing target
            if is_expected:
                for opt in options:
                    if any(r in opt for r in ["40-50", "40 - 50", "35-45", "30-45", "30-50", "30-40"]):
                        return opt
            else:
                for opt in options:
                    if any(r in opt for r in ["30-40", "30 - 40", "25-35", "20-30"]):
                        return opt

            for opt in options:
                opt_l = opt.lower()
                if target_num in opt_l:
                    return opt

            return options[0]

        # Text input formatting
        if "inr" in q or "rupee" in q or "full" in q or "annual" in q and "lpa" not in q and "lakh" not in q:
            # Check if placeholder requires full amount
            if "000" in q or "digits" in q:
                return target_full
        return target_num

    def resolve_experience(
        self,
        question_text: str,
        field_type: str = "text",
        options: Optional[List[str]] = None,
    ) -> str:
        """
        Matches years of experience from candidate facts:
        - Total: 5.5 years (5 in Data Engineering)
        - Big Data / PySpark / AWS / Databricks / SQL: 5 years
        - Kafka / Snowflake: 2-3 years
        """
        q = question_text.lower()
        if any(term in q for term in ["total", "overall"]):
            years_num = int(self.work.get("total_years_experience", 5))
        else:
            years_num = 5
            # Sort skills by length descending so multi-word skills like 'cortex ai' match before 'ai'
            sorted_skills = sorted(self.skills.items(), key=lambda item: len(item[0]), reverse=True)
            for skill, yrs in sorted_skills:
                if re.search(rf"\b{re.escape(skill)}\b", q):
                    years_num = int(yrs)
                    break

        if options:
            # 1. Check if any option contains explicit range starting/ending with digit
            for opt in options:
                opt_l = opt.lower()
                if "no experience" in opt_l or "none" in opt_l:
                    continue
                if f"{years_num}-{years_num+1}" in opt_l or f"{years_num}-{years_num+2}" in opt_l or f"{years_num} to" in opt_l or f"{years_num}-" in opt_l:
                    return opt
                if f"-{years_num}" in opt_l or f"to {years_num}" in opt_l:
                    return opt

            # 2. Check for > or +
            for opt in options:
                opt_l = opt.lower()
                m = re.search(r'(?:>|\+)\s*(\d+)', opt_l) or re.search(r'(\d+)\s*\+', opt_l)
                if m:
                    val = int(m.group(1))
                    if years_num >= val:
                        return opt

            # 3. Check for exact digit
            for opt in options:
                opt_l = opt.lower()
                if "no experience" in opt_l:
                    continue
                if str(years_num) in opt_l:
                    return opt

            # 4. Check for range enclosing years_num
            for opt in options:
                opt_l = opt.lower()
                m = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)', opt_l)
                if m:
                    low, high = int(m.group(1)), int(m.group(2))
                    if low <= years_num <= high:
                        return opt

            # 5. Non-zero fallback
            non_zero = [o for o in options if not any(k in o.lower() for k in ["no experience", "none", "0 years"])]
            if non_zero:
                return non_zero[-1] if years_num >= 4 else non_zero[0]
            return options[0]

        return str(years_num)

    # =========================================================================
    # Universal Resolver
    # =========================================================================

    def resolve(
        self,
        question_text: str,
        field_type: str = "text",
        options: Optional[List[str]] = None,
    ) -> str:
        """
        Unified question-solving entrypoint.
        Executes strict precedence rules, memory lookups, and AI/interactive fallback.
        """
        if not question_text:
            return ""

        clean_q = question_text.strip()
        q = clean_q.lower()

        # 1. Check persistent learned answers memory
        for saved_q, saved_ans in self.learned_answers.items():
            if saved_q.strip().lower() == q or (len(saved_q) > 25 and saved_q.strip().lower() in q):
                if options:
                    # Map to exact option if option list provided
                    for opt in options:
                        if saved_ans.lower() == opt.strip().lower():
                            return opt
                return saved_ans

        # 2. Notice period strict rule
        if "notice" in q:
            return self.resolve_notice_period(clean_q, field_type=field_type, options=options)

        # 3. CTC / Salary strict rule
        if any(term in q for term in ["ctc", "salary", "compensation", "package", "remuneration", "earning"]):
            return self.resolve_ctc(clean_q, field_type=field_type, options=options)

        # 4. Total experience & skill experience
        if any(term in q for term in ["experience", "years", "how long", "how many years"]):
            return self.resolve_experience(clean_q, field_type=field_type, options=options)

        # 5. Work authorization & Sponsorship
        if any(term in q for term in ["authorized to work", "legally authorized", "citizenship", "work permit", "right to work"]):
            return self._match_yes_no(options, default_yes=True)

        if any(term in q for term in ["sponsorship", "visa sponsorship", "require visa", "need sponsorship"]):
            return self._match_yes_no(options, default_yes=False)

        # 6. Relocation / Commute / Remote / Shifts
        if any(term in q for term in [
            "relocate", "willing to relocate", "commute", "rotational", "shift",
            "night shift", "hybrid", "on-site", "remote", "comfortable with"
        ]):
            return self._match_yes_no(options, default_yes=True)

        # 7. Location / City
        if any(term in q for term in ["city", "current location", "where are you located", "current address"]):
            city = self.personal.get("current_city", "Bengaluru")
            if options:
                for opt in options:
                    if city.lower() in opt.lower():
                        return opt
            return city

        # 8. Education / Degree
        if any(term in q for term in ["degree", "education", "qualification", "graduation"]):
            deg = self.education.get("degree", "Bachelor of Technology")
            if options:
                for opt in options:
                    if any(d in opt.lower() for d in ["bachelor", "b.tech", "graduate", "engineering"]):
                        return opt
            return deg

        # 9. Cloud Platforms & Primary Technologies
        if any(term in q for term in ["which cloud", "cloud platform", "azure/aws/gcp", "aws/azure/gcp", "what cloud", "cloud experience"]):
            if options:
                for opt in options:
                    if "aws" in opt.lower():
                        return opt
                return options[0]
            return "AWS, Azure"

        if any(term in q for term in ["primary skill", "key skill", "primary technology"]):
            return "PySpark, AWS, Databricks, SQL"

        # 9. Fallback: Interactive prompt if enabled
        if self.interactive and sys.stdin.isatty():
            print(f"\n❓ New / Unknown Question: \"{clean_q}\"")
            if options:
                print("Options available:")
                for i, opt in enumerate(options, 1):
                    print(f"  [{i}] {opt}")
                user_choice = input("Enter choice number or custom answer: ").strip()
                if user_choice.isdigit() and 1 <= int(user_choice) <= len(options):
                    ans = options[int(user_choice) - 1]
                else:
                    ans = user_choice or options[0]
            else:
                ans = input("Enter your answer: ").strip()

            if ans:
                self.save_learned_answer(clean_q, ans)
                return ans

        # 10. Default safe fallback
        if options:
            # Check for positive affirmative option
            for opt in options:
                if opt.lower() in ["yes", "true", "agree", "confirmed"]:
                    return opt
            return options[0]

        return "Yes"

    def _match_yes_no(self, options: Optional[List[str]], default_yes: bool = True) -> str:
        target = "Yes" if default_yes else "No"
        if options:
            for opt in options:
                if opt.strip().lower() == target.lower():
                    return opt
            return options[0]
        return target


# Global shared instance
question_solver = QuestionSolver()
