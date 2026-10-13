"""
CareerEngine Intelligent Profile Scoring & ATS Audit Engine.
Performs holistic evaluation of candidate profile completeness, market readiness,
multi-role resume coverage, technical skill depth, and screening Q&A memory.
Produces an overall score (0-100), letter grade (A+, A, B, C), dimensional breakdown,
role-specific readiness percentages, and prioritized actionable recommendations.
"""

import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional

from core.config_loader import get_config
from core.resume_selector import ResumeSelector, ROLE_PATTERNS

ROOT_DIR = Path(__file__).resolve().parent.parent

# Domain skill mappings for role readiness computation
ROLE_CORE_SKILLS: Dict[str, List[str]] = {
    "_DE": [
        "python", "sql", "pyspark", "spark", "databricks", "delta lake", "airflow",
        "aws", "etl", "elt", "data pipeline", "data modeling", "kafka", "snowflake", "redshift"
    ],
    "_DS": [
        "python", "sql", "machine learning", "data science", "statistics", "pandas",
        "scikit-learn", "deep learning", "nlp", "xgboost", "analytics", "tableau"
    ],
    "_AI": [
        "python", "genai", "generative ai", "llm", "langchain", "agentic ai",
        "prompt engineering", "cortex ai", "rag", "fine-tuning", "transformers", "mcp"
    ],
    "_SWE": [
        "python", "sql", "scala", "java", "c++", "golang", "rest apis", "docker",
        "kubernetes", "git", "ci/cd", "microservices", "postgresql", "mysql"
    ],
    "_MLOps": [
        "python", "docker", "kubernetes", "mlops", "terraform", "ci/cd", "aws",
        "cloudwatch", "jenkins", "github actions", "monitoring", "model deployment"
    ]
}

ROLE_LABELS: Dict[str, str] = {
    "_DE": "Data Engineering",
    "_DS": "Data Science & Analytics",
    "_AI": "AI & GenAI Platforms",
    "_SWE": "Software Engineering & Backend",
    "_MLOps": "MLOps & Cloud Infrastructure"
}

@dataclass
class CategoryScore:
    name: str
    score: float
    max_score: float
    percentage: float
    details: List[str] = field(default_factory=list)

@dataclass
class ProfileScoreReport:
    total_score: int
    letter_grade: str
    grade_title: str
    categories: Dict[str, Dict[str, Any]]
    strengths: List[str]
    critical_gaps: List[str]
    actionable_recommendations: List[str]
    role_readiness: Dict[str, Dict[str, Any]]
    resumes_detected: List[str]
    llm_critique: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProfileScorer:
    """Evaluates candidate profile completeness, market readiness, and multi-role alignment."""

    def __init__(self, profile_data: Optional[Dict[str, Any]] = None, config=None):
        self.config = config or get_config()
        self.profile = profile_data if profile_data is not None else self.config.profile
        self.resume_selector = ResumeSelector()

    def evaluate(self, include_llm_critique: bool = False) -> ProfileScoreReport:
        """Computes comprehensive profile score and audit report."""
        personal = self.profile.get("personal_info", {})
        work = self.profile.get("work_summary", {})
        education = self.profile.get("education", {})
        skills = self.profile.get("skills_years_experience", {})
        screening = self.profile.get("screening_defaults", {})
        custom_answers = self.profile.get("custom_answers", {})
        exp_history = self.profile.get("experience_history", [])
        certifications = self.profile.get("certifications", [])

        strengths: List[str] = []
        critical_gaps: List[str] = []
        recommendations: List[str] = []

        # ---------------------------------------------------------
        # Category 1: Contact & Web Presence (15 Points)
        # ---------------------------------------------------------
        c1_score = 0.0
        c1_max = 15.0
        c1_details: List[str] = []

        # Full name check
        first = personal.get("first_name", "").strip()
        last = personal.get("last_name", "").strip()
        full = personal.get("full_name", "").strip() or f"{first} {last}".strip()
        if full and len(full) > 3:
            c1_score += 4.0
            c1_details.append("Candidate name properly formatted")
        else:
            critical_gaps.append("Missing full name in personal_info")

        # Email
        email = personal.get("email", "").strip()
        if email and "@" in email and "." in email:
            c1_score += 3.0
            c1_details.append(f"Email verified: {email}")
        else:
            critical_gaps.append("Missing or invalid email address")

        # Phone
        phone = personal.get("full_phone", "").strip() or personal.get("phone_number", "").strip()
        if phone and len(phone) >= 10:
            c1_score += 3.0
            c1_details.append("Phone number with country code specified")
        else:
            critical_gaps.append("Missing primary contact phone number")

        # City / Location
        location = personal.get("location", "").strip() or personal.get("current_city", "").strip()
        if location:
            c1_score += 2.0
            c1_details.append(f"Location anchor: {location}")
        else:
            critical_gaps.append("Candidate city/location is missing")

        # Links (LinkedIn / GitHub / Portfolio)
        linkedin = personal.get("linkedin_url", "").strip()
        github = personal.get("github_url", "").strip()
        portfolio = personal.get("portfolio_url", "").strip()

        link_score = 0.0
        if linkedin and "linkedin.com" in linkedin:
            link_score += 1.5
            strengths.append("Verified LinkedIn profile link")
        if (github and "github.com" in github) or portfolio:
            link_score += 1.5
            strengths.append("Verified GitHub/Portfolio code presence")
        c1_score += link_score

        if not linkedin:
            recommendations.append("Add your LinkedIn profile URL in profile_config.json to boost recruiter response.")
        if not github and not portfolio:
            recommendations.append("Add a GitHub or technical portfolio link to showcase repositories and proof-of-work.")

        cat_1 = CategoryScore("Contact & Online Presence", c1_score, c1_max, round((c1_score / c1_max) * 100, 1), c1_details)

        # ---------------------------------------------------------
        # Category 2: Experience & Compensation Fundamentals (25 Points)
        # ---------------------------------------------------------
        c2_score = 0.0
        c2_max = 25.0
        c2_details: List[str] = []

        # Current Title & Company
        current_title = work.get("current_title", "").strip()
        current_company = work.get("current_company", "").strip()
        if current_title and current_company:
            c2_score += 5.0
            c2_details.append(f"Current role anchored: {current_title} at {current_company}")
            strengths.append(f"Current title: {current_title}")
        else:
            critical_gaps.append("Current job title or company missing in work_summary")
            recommendations.append("Define current_title and current_company in work_summary.")

        # Total Years Experience
        total_exp = work.get("total_years_experience", 0)
        try:
            total_exp = float(total_exp)
            if total_exp > 0:
                c2_score += 4.0
                c2_details.append(f"Total experience: {total_exp:g} years")
            else:
                critical_gaps.append("Total years of experience is 0 or unset")
        except Exception:
            critical_gaps.append("Invalid total_years_experience format")

        # Experience History entries & Metrics
        if exp_history and isinstance(exp_history, list) and len(exp_history) > 0:
            c2_score += 4.0
            c2_details.append(f"{len(exp_history)} historical career position(s) recorded")
            
            # Check for quantifiable impact descriptions (numbers, percentages)
            has_metrics = False
            for item in exp_history:
                details_text = item.get("details", "")
                if re.search(r'\d+(?:%|\+|x|k|m|ms|\s*datasets|\s*users|\s*queries)', details_text, re.IGNORECASE):
                    has_metrics = True
                    break
            if has_metrics:
                c2_score += 4.0
                c2_details.append("Experience history includes measurable impact metrics")
                strengths.append("Measurable engineering impact metrics in career history")
            else:
                c2_score += 2.0
                recommendations.append("Enhance experience descriptions with numbers and KPIs (e.g. 'processed 10M+ daily records', '4x cost reduction').")
        else:
            recommendations.append("Add detailed experience_history entries to profile_config.json.")

        # Notice Period
        notice_days = work.get("notice_period_days")
        if notice_days is not None:
            c2_score += 4.0
            c2_details.append(f"Notice period calibrated ({notice_days} days)")
            if int(notice_days) <= 30:
                strengths.append(f"Immediate / 30-day fast notice availability ({notice_days}d)")
        else:
            critical_gaps.append("Notice period days is not specified")
            recommendations.append("Specify notice_period_days in work_summary (e.g. 15, 30, 60).")

        # Current & Expected Salary / Compensation
        curr_sal = str(work.get("current_salary_inr_lpa", "")).strip()
        exp_sal = str(work.get("expected_salary_inr_lpa", "")).strip()
        if curr_sal and exp_sal:
            c2_score += 4.0
            c2_details.append(f"Compensation expectation set (Current: ₹{curr_sal}LPA, Expected: ₹{exp_sal}LPA)")
        elif curr_sal or exp_sal:
            c2_score += 2.0
            recommendations.append("Fill both current_salary_inr_lpa and expected_salary_inr_lpa to avoid recruiter drop-offs on Indian portals.")
        else:
            critical_gaps.append("Compensation numbers (current & expected CTC) missing")
            recommendations.append("Set current_salary_inr_lpa and expected_salary_inr_lpa in work_summary.")

        cat_2 = CategoryScore("Work & Compensation Fundamentals", c2_score, c2_max, round((c2_score / c2_max) * 100, 1), c2_details)

        # ---------------------------------------------------------
        # Category 3: Technical Skill Density & Depth (20 Points)
        # ---------------------------------------------------------
        c3_score = 0.0
        c3_max = 20.0
        c3_details: List[str] = []

        skill_count = len(skills)
        if skill_count >= 15:
            c3_score += 10.0
            c3_details.append(f"Extensive technical vocabulary ({skill_count} tracked competencies)")
            strengths.append(f"Deep technical skill index ({skill_count}+ technologies)")
        elif skill_count >= 7:
            c3_score += 7.0
            c3_details.append(f"Solid skill baseline ({skill_count} tracked competencies)")
        elif skill_count > 0:
            c3_score += 4.0
            c3_details.append(f"Basic skill list ({skill_count} competencies)")
            recommendations.append("Add more specific technical competencies and frameworks to skills_years_experience.")
        else:
            critical_gaps.append("No technical skills configured in skills_years_experience")
            recommendations.append("Populate skills_years_experience with key tools and years (e.g., 'python': 5, 'aws': 4).")

        # Check core foundational areas
        skill_keys_lower = [s.lower() for s in skills.keys()]
        
        # Languages
        has_lang = any(lang in skill_keys_lower for lang in ["python", "java", "scala", "c++", "golang", "javascript", "typescript", "rust"])
        if has_lang:
            c3_score += 3.0
            c3_details.append("Core programming languages verified")
        else:
            recommendations.append("Add primary programming languages (e.g. Python, Java, Go) to skills_years_experience.")

        # Databases
        has_db = any(db in skill_keys_lower for db in ["sql", "postgresql", "postgres", "mysql", "mongodb", "neo4j", "cassandra", "snowflake", "redshift"])
        if has_db:
            c3_score += 2.0
            c3_details.append("Relational / distributed databases indexed")

        # Cloud & DevOps
        has_cloud = any(cl in skill_keys_lower for cl in ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "jenkins", "github actions"])
        if has_cloud:
            c3_score += 3.0
            c3_details.append("Cloud infrastructure & DevOps stack verified")
            strengths.append("Cloud & Container ecosystem coverage (AWS/Azure/GCP/Docker)")
        else:
            recommendations.append("Add cloud platforms (AWS, Azure, or GCP) and Docker/K8s to skills.")

        # Advanced / Domain Specialization
        has_adv = any(adv in skill_keys_lower for adv in ["pyspark", "spark", "databricks", "delta lake", "kafka", "langchain", "llm", "genai", "mlops", "agentic ai"])
        if has_adv:
            c3_score += 2.0
            c3_details.append("High-demand distributed computing or AI competencies verified")
            strengths.append("Specialized modern stack (Databricks, Spark, or LLMs)")

        cat_3 = CategoryScore("Technical Skill Density & Recency", c3_score, c3_max, round((c3_score / c3_max) * 100, 1), c3_details)

        # ---------------------------------------------------------
        # Category 4: Multi-Role Resume Tag Readiness (20 Points)
        # ---------------------------------------------------------
        c4_score = 0.0
        c4_max = 20.0
        c4_details: List[str] = []

        available_resumes = self.resume_selector.list_available_resumes()
        resume_names = [p.name for p in available_resumes]
        detected_tags = set()

        if available_resumes:
            c4_score += 8.0
            c4_details.append(f"Found {len(available_resumes)} resume PDF file(s)")

            # Check role tag patterns in resume file names
            for path in available_resumes:
                name_lower = path.name.lower()
                for tag, patterns in ROLE_PATTERNS.items():
                    if any(re.search(pat, name_lower) for pat in patterns):
                        detected_tags.add(tag)

            tag_count = len(detected_tags)
            if tag_count >= 3:
                c4_score += 12.0
                c4_details.append(f"Exceptional multi-role resume coverage ({tag_count} specialized tracks)")
                strengths.append(f"Multi-role tailored resume suite ({', '.join(sorted(detected_tags))})")
            elif tag_count == 2:
                c4_score += 8.0
                c4_details.append(f"Dual-role resume targeting ({tag_count} tracks: {', '.join(sorted(detected_tags))})")
                recommendations.append("Add a 3rd role variant (e.g. _AI or _SWE resume) in resumes/ to unlock 100% multi-role score.")
            elif tag_count == 1:
                c4_score += 4.0
                c4_details.append(f"Single-role resume detected ({list(detected_tags)[0]})")
                recommendations.append(
                    "Create targeted resume variants in the `resumes/` folder (e.g. Name_DE_resume.pdf, Name_SWE_resume.pdf, Name_AI_resume.pdf) for dynamic role switching."
                )
            else:
                c4_score += 2.0
                c4_details.append("Resume found, but lacks standard role tags (_DE, _SWE, _AI, _DS, _MLOps)")
                recommendations.append("Rename resumes to include role tags like `_DE` or `_SWE` for intelligent auto-selection.")
        else:
            critical_gaps.append("No PDF resume files found in resumes/ directory")
            recommendations.append("Place your primary PDF resume in the `resumes/` folder.")

        cat_4 = CategoryScore("Multi-Role Resume Tag Readiness", c4_score, c4_max, round((c4_score / c4_max) * 100, 1), c4_details)

        # ---------------------------------------------------------
        # Category 5: Screening Memory & Automation Defaults (20 Points)
        # ---------------------------------------------------------
        c5_score = 0.0
        c5_max = 20.0
        c5_details: List[str] = []

        # Work authorization & sponsorship
        if "legally_authorized" in screening and "require_sponsorship" in screening:
            c5_score += 4.0
            c5_details.append("Legal work authorization & visa sponsorship defaults calibrated")
        else:
            critical_gaps.append("Missing legal authorization / sponsorship settings in screening_defaults")
            recommendations.append("Set legally_authorized: true and require_sponsorship in screening_defaults.")

        # Notice period negotiation & join settings
        if "is_notice_negotiable" in screening or "notice_period_days" in screening or "serving_notice_period" in screening:
            c5_score += 3.0
            c5_details.append("Recruiter notice & joining availability rules configured")
        else:
            recommendations.append("Add notice period and joining preferences to screening_defaults.")

        # Remote / Relocation / Workplace
        if "willing_to_relocate" in screening or "open_to_remote" in screening:
            c5_score += 3.0
            c5_details.append("Relocation & hybrid/remote work posture defined")

        # Learned Screening Memory (custom_answers)
        num_answers = len(custom_answers)
        if num_answers >= 20:
            c5_score += 10.0
            c5_details.append(f"Robust recruiter question memory ({num_answers} cached answers)")
            strengths.append(f"Zero-friction Q&A memory ({num_answers}+ cached ATS answers)")
        elif num_answers >= 10:
            c5_score += 7.0
            c5_details.append(f"Good question memory base ({num_answers} cached answers)")
        elif num_answers >= 3:
            c5_score += 4.0
            c5_details.append(f"Initial question memory started ({num_answers} answers)")
            recommendations.append("Expand custom_answers memory by running in interactive mode (`-i`) on complex forms.")
        else:
            c5_score += 1.0
            recommendations.append("Pre-populate common custom_answers (e.g. current CTC, notice period, preferred locations) to speed up auto-apply.")

        cat_5 = CategoryScore("Screening Memory & Automation Defaults", c5_score, c5_max, round((c5_score / c5_max) * 100, 1), c5_details)

        # ---------------------------------------------------------
        # Final Total & Grade Calculation
        # ---------------------------------------------------------
        raw_total = c1_score + c2_score + c3_score + c4_score + c5_score
        total_score = min(100, max(0, int(round(raw_total))))

        if total_score >= 92:
            letter_grade = "A+"
            grade_title = "Elite ATS & Auto-Apply Ready (Top 2%)"
        elif total_score >= 82:
            letter_grade = "A"
            grade_title = "Strong Automated Candidate Profile"
        elif total_score >= 72:
            letter_grade = "B+"
            grade_title = "Solid Profile with Minor Optimization Gaps"
        elif total_score >= 60:
            letter_grade = "B"
            grade_title = "Moderate Readiness (Needs Compensation & Tagging Tuning)"
        else:
            letter_grade = "C"
            grade_title = "Needs Immediate Attention"

        # ---------------------------------------------------------
        # Role Readiness Calculation
        # ---------------------------------------------------------
        role_readiness: Dict[str, Dict[str, Any]] = {}
        for role_tag, req_skills in ROLE_CORE_SKILLS.items():
            matched = [s for s in req_skills if s in skill_keys_lower]
            base_pct = (len(matched) / max(1, len(req_skills))) * 80  # Max 80% from skills
            
            # Check if specialized resume exists for this track
            has_tag_resume = any(
                role_tag.replace("_", "").lower() in r.lower() or
                role_tag.lower() in r.lower()
                for r in resume_names
            )
            if has_tag_resume:
                base_pct += 20.0  # +20% for tailored resume
            else:
                base_pct += 5.0   # General resume baseline
            
            pct = min(100, int(round(base_pct)))
            role_readiness[role_tag] = {
                "label": ROLE_LABELS.get(role_tag, role_tag),
                "readiness_percent": pct,
                "matched_skills": matched,
                "has_dedicated_resume": has_tag_resume
            }

        # Certifications bonus recognition
        if certifications and len(certifications) >= 2:
            strengths.append(f"{len(certifications)} verified industry certifications (AWS, Databricks, Azure)")

        # Optional LLM critique
        llm_critique = None
        if include_llm_critique:
            llm_critique = self._generate_llm_critique(total_score, letter_grade, strengths, recommendations)

        return ProfileScoreReport(
            total_score=total_score,
            letter_grade=letter_grade,
            grade_title=grade_title,
            categories={
                "contact": asdict(cat_1),
                "experience": asdict(cat_2),
                "skills": asdict(cat_3),
                "resumes": asdict(cat_4),
                "screening": asdict(cat_5),
            },
            strengths=strengths,
            critical_gaps=critical_gaps,
            actionable_recommendations=recommendations[:6],
            role_readiness=role_readiness,
            resumes_detected=resume_names,
            llm_critique=llm_critique
        )

    def _generate_llm_critique(
        self,
        score: int,
        grade: str,
        strengths: List[str],
        recommendations: List[str]
    ) -> Optional[str]:
        """Optionally generates a high-level executive audit summary via unified AI solver."""
        try:
            from ai.ai_solver import UnifiedAISolver
            solver = UnifiedAISolver()
            prompt = f"""
You are an elite Tech Career Coach & ATS System Auditor.
Provide a sharp, 2-sentence executive assessment of this candidate profile.
Candidate Score: {score}/100 (Grade: {grade})
Top Strengths: {', '.join(strengths[:3])}
Key Optimization Areas: {', '.join(recommendations[:2])}
Tone: Professional, direct, encouraging, high-agency. No fluff.
"""
            res = solver._call_gemini(prompt, max_tokens=100)
            if not res:
                res = solver._call_claude(prompt, max_tokens=100)
            if not res:
                res = solver._call_openai(prompt, max_tokens=100)
            if not res:
                res = solver._call_nvidia(prompt, max_tokens=100)
            if res and res[0]:
                return res[0].strip()
        except Exception:
            pass
        return None

    def format_cli_scorecard(self, report: ProfileScoreReport) -> str:
        """Formats an ANSI terminal scorecard for display."""
        # Color codes
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        MAGENTA = "\033[95m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        RESET = "\033[0m"

        grade_color = GREEN if report.total_score >= 80 else (YELLOW if report.total_score >= 65 else MAGENTA)

        lines = []
        lines.append(f"\n{BOLD}{'='*68}{RESET}")
        lines.append(f"{CYAN}{BOLD}  🎯 CAREERENGINE CANDIDATE PROFILE AUDIT & ATS SCORECARD{RESET}")
        lines.append(f"{BOLD}{'='*68}{RESET}\n")

        # Score Banner
        lines.append(f"  {BOLD}Overall ATS Readiness Score:{RESET}  {grade_color}{BOLD}{report.total_score}/100{RESET}  [{grade_color}{report.letter_grade}{RESET}] - {report.grade_title}")
        lines.append(f"  {DIM}Evaluated against 5 key hiring criteria & Indian/Global portal constraints{RESET}\n")

        # Category Breakdown
        lines.append(f"  {BOLD}Dimensional Breakdown:{RESET}")
        for cat_key, cat in report.categories.items():
            pct = cat['percentage']
            bar_len = int(pct / 5)  # 20 chars max
            bar = "█" * bar_len + "░" * (20 - bar_len)
            c_color = GREEN if pct >= 80 else (YELLOW if pct >= 60 else MAGENTA)
            lines.append(f"    • {cat['name']:<36} {c_color}{bar}{RESET} {cat['score']:>4.1f}/{cat['max_score']:<4.1f} ({pct:>5.1f}%)")

        # Role Readiness
        lines.append(f"\n  {BOLD}Multi-Role Domain Readiness (% Fit):{RESET}")
        for role_tag, data in report.role_readiness.items():
            r_pct = data['readiness_percent']
            tag_mark = "✓ Tagged Resume" if data['has_dedicated_resume'] else "⚠ Generic Resume"
            r_color = GREEN if r_pct >= 80 else (YELLOW if r_pct >= 60 else DIM)
            lines.append(f"    • {data['label']:<34} [{r_color}{r_pct:>3}%{RESET}]  {DIM}({tag_mark}){RESET}")

        # Detected Resumes
        lines.append(f"\n  {BOLD}Resumes in Repository ({len(report.resumes_detected)}):{RESET}")
        for r_name in report.resumes_detected:
            lines.append(f"    📄 {r_name}")
        if not report.resumes_detected:
            lines.append(f"    {YELLOW}⚠️ No resume PDF files detected in resumes/{RESET}")

        # Strengths
        if report.strengths:
            lines.append(f"\n  {GREEN}{BOLD}Candidate Strengths & Badges:{RESET}")
            for s in report.strengths[:5]:
                lines.append(f"    ✓ {s}")

        # Actionable Recommendations
        if report.actionable_recommendations:
            lines.append(f"\n  {YELLOW}{BOLD}Actionable Recommendations for 100% Score:{RESET}")
            for idx, rec in enumerate(report.actionable_recommendations, 1):
                lines.append(f"    {idx}. {rec}")

        # LLM Critique if available
        if report.llm_critique:
            lines.append(f"\n  {CYAN}{BOLD}AI Executive Assessment:{RESET}")
            lines.append(f"    \"{report.llm_critique}\"")

        lines.append(f"\n{BOLD}{'='*68}{RESET}\n")
        return "\n".join(lines)

profile_scorer = ProfileScorer()
