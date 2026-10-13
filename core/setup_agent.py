"""
CareerOS Onboarding & Profile Setup Agent.
Interactive CLI agent that prompts the user for their profile, resume,
search criteria, and API keys, automatically creating all local configuration files.
"""

import os
import sys
import json
import yaml
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent

class SetupAgent:
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or ROOT_DIR
        self.env_path = self.root_dir / ".env"
        self.profile_path = self.root_dir / "profile_config.json"
        self.yaml_path = self.root_dir / "config.yaml"
        self.db_path = self.root_dir / "jobs.db"

    def prompt_input(self, prompt: str, default: str = "") -> str:
        """Helper to get user input with an optional default value."""
        suffix = f" [{default}]: " if default else ": "
        try:
            val = input(f"👉 {prompt}{suffix}").strip()
            return val if val else default
        except (KeyboardInterrupt, EOFError):
            print("\n⚠️ Setup cancelled by user.")
            sys.exit(0)

    def prompt_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Helper to get boolean confirmation from user."""
        def_str = "Y/n" if default else "y/N"
        try:
            val = input(f"👉 {prompt} ({def_str}): ").strip().lower()
            if not val:
                return default
            return val in ["y", "yes", "true", "1"]
        except (KeyboardInterrupt, EOFError):
            print("\n⚠️ Setup cancelled by user.")
            sys.exit(0)

    def run(self, defaults_only: bool = False):
        """Runs the interactive onboarding agent."""
        print("\n" + "=" * 70)
        print("🤖 CareerOS - Automated Onboarding & Profile Setup Agent")
        print("=" * 70)
        print("Welcome to CareerOS! This agent will configure your profile, resume,")
        print("job search keywords, and AI keys securely on your local system.")
        print("🔒 Privacy Notice: All your credentials and profile data remain strictly local.")
        print("=" * 70 + "\n")

        # Check existing config
        if self.profile_path.exists() and not defaults_only:
            overwrite = self.prompt_yes_no("Existing profile_config.json detected. Overwrite/update?", default=True)
            if not overwrite:
                print("Skipping setup. Existing configuration preserved.")
                return

        # --- STEP 1: Personal Information ---
        print("\n📝 [Step 1/5] Personal Information")
        print("-" * 50)
        full_name = "Alex Mercer" if defaults_only else self.prompt_input("Full Name", "Alex Mercer")
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else "Alex"
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        email = "alex.mercer@example.com" if defaults_only else self.prompt_input("Email Address", "alex.mercer@example.com")
        phone_code = "+1" if defaults_only else self.prompt_input("Country Code (e.g. +1, +91)", "+1")
        phone_num = "5550199283" if defaults_only else self.prompt_input("Phone Number", "5550199283")
        full_phone = f"{phone_code}{phone_num}" if not phone_num.startswith("+") else phone_num

        location = "San Francisco, CA, USA" if defaults_only else self.prompt_input("Current City, State, Country", "San Francisco, CA, USA")
        linkedin_url = "" if defaults_only else self.prompt_input("LinkedIn Profile URL (optional)", "")
        github_url = "" if defaults_only else self.prompt_input("GitHub or Portfolio URL (optional)", "")

        # --- STEP 2: Resume Files & Role-Based Selector ---
        print("\n📄 [Step 2/5] Resumes & Multi-Role Setup")
        print("-" * 50)
        print("💡 CareerOS includes an Intelligent Resume Selector!")
        print("   Drop your specialized resume PDFs into the 'resumes/' directory:")
        print("   • Data Engineering:     resumes/*_DE*.pdf or resumes/*_data_engineer*.pdf")
        print("   • Data Science / ML:    resumes/*_DS*.pdf or resumes/*_data_science*.pdf")
        print("   • AI / GenAI Platforms: resumes/*_AI*.pdf or resumes/*_genai*.pdf")
        print("   • Software Engineering: resumes/*_SWE*.pdf or resumes/*_software*.pdf")
        print("   • MLOps / DevOps:       resumes/*_MLOps*.pdf or resumes/*_devops*.pdf")
        print("-" * 50)
        
        from core.resume_selector import get_resume_selector
        selector = get_resume_selector()
        found_resumes = selector.list_available_resumes()
        if found_resumes:
            print(f"  🔍 Detected {len(found_resumes)} resume(s) in resumes/ folder:")
            for r in found_resumes:
                print(f"     • {r.name}")
            resume_input = str(found_resumes[0])
        else:
            resume_input = "resumes/resume.pdf" if defaults_only else self.prompt_input("Default Resume PDF path", "resumes/resume.pdf")

        resume_path = os.path.abspath(os.path.expanduser(resume_input))

        # --- STEP 3: Career & Compensation ---
        print("\n💼 [Step 3/5] Career & Compensation Facts")
        print("-" * 50)
        title = "Senior Software Engineer" if defaults_only else self.prompt_input("Current / Most Recent Job Title", "Senior Software Engineer")
        company = "Tech Innovations Inc" if defaults_only else self.prompt_input("Current / Most Recent Company", "Tech Innovations Inc")
        years_exp = 5 if defaults_only else int(self.prompt_input("Total Years of Professional Experience", "5") or "5")
        notice_days = 30 if defaults_only else int(self.prompt_input("Notice Period in Days", "30") or "30")
        current_ctc = "30" if defaults_only else self.prompt_input("Current Annual Compensation / CTC (e.g. 30 LPA or 150000)", "30")
        expected_ctc = "40" if defaults_only else self.prompt_input("Expected Annual Compensation / CTC (e.g. 40 LPA or 180000)", "40")

        raw_skills = "Python, SQL, AWS, Docker, Kubernetes, CI/CD" if defaults_only else self.prompt_input(
            "Core Technical Skills (comma separated)", "Python, SQL, AWS, Docker, Kubernetes, CI/CD"
        )
        skills_list = [s.strip() for s in raw_skills.split(",") if s.strip()]
        skills_dict = {skill.lower(): years_exp for skill in skills_list}

        # --- STEP 4: Job Search Parameters ---
        print("\n🔍 [Step 4/5] Job Search Preferences")
        print("-" * 50)
        raw_keywords = f"{title}, Software Engineer" if defaults_only else self.prompt_input(
            "Target Search Keywords (comma separated)", f"{title}, Software Engineer"
        )
        keywords_list = [k.strip() for k in raw_keywords.split(",") if k.strip()]
        work_pref = "remote_first" if defaults_only else self.prompt_input(
            "Work Preference (remote_first, hybrid, onsite)", "remote_first"
        )
        max_apps = 10 if defaults_only else int(self.prompt_input("Default Max Applications Per Run", "10") or "10")

        # --- STEP 5: AI & Browser Keys ---
        print("\n🔑 [Step 5/5] AI Reasoning Keys & Browser Port")
        print("-" * 50)
        print("CareerOS uses Google Gemini for ultra-fast, intelligent form filling.")
        print("💡 Free Gemini API keys can be generated at: https://aistudio.google.com/")
        gemini_key_1 = "" if defaults_only else self.prompt_input("Gemini API Key 1", "")
        gemini_key_2 = "" if defaults_only else self.prompt_input("Gemini API Key 2 (Optional backup)", "")
        nvidia_key = "" if defaults_only else self.prompt_input("NVIDIA / DeepSeek API Key (Optional)", "")
        cdp_port = "9222" if defaults_only else self.prompt_input("Chrome Remote Debugging Port", "9222")

        # --- GENERATE FILES ---
        print("\n⚙️ Generating local configuration files...")

        # 1. Generate .env
        env_content = f"""# CareerOS Environment Configuration
# Generated automatically by Setup Agent

# Google Gemini API Keys (Free keys from https://aistudio.google.com/)
GEMINI_API_KEY_1={gemini_key_1}
GEMINI_API_KEY_2={gemini_key_2}
GEMINI_API_KEY_3=

# Optional NVIDIA / DeepSeek Fallback API Key
NVIDIA_API_KEY={nvidia_key}
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=deepseek-ai/deepseek-v4-pro-0813

# Chrome Remote Debugging
CHROME_CDP_URL=http://localhost:{cdp_port}
CHROME_USER_DATA_DIR=~/.chrome-job-agent

# Automation Parameters
MAX_APPLICATIONS_PER_RUN={max_apps}
MIN_ACTION_DELAY=1.5
MAX_ACTION_DELAY=2.8
DEFAULT_LOCATION="{location}"
DEFAULT_WORK_MODE={work_pref}
"""
        with open(self.env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"  ✅ Created: {self.env_path.name}")

        # 2. Generate profile_config.json
        profile_data = {
            "personal_info": {
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "email": email,
                "phone_country_code": phone_code,
                "phone_number": phone_num,
                "full_phone": full_phone,
                "location": location,
                "linkedin_url": linkedin_url,
                "github_url": github_url,
                "portfolio_url": github_url or linkedin_url,
                "resume_path": resume_path
            },
            "work_summary": {
                "current_title": title,
                "current_company": company,
                "total_years_experience": years_exp,
                "notice_period_days": notice_days,
                "notice_period_text": f"{notice_days} days",
                "current_salary_inr_lpa": str(current_ctc),
                "expected_salary_inr_lpa": str(expected_ctc)
            },
            "education": {
                "degree": "Bachelor of Technology",
                "field_of_study": "Computer Science and Engineering",
                "institution": "University / Institute",
                "graduation_year": "2021"
            },
            "skills_years_experience": skills_dict,
            "screening_defaults": {
                "legally_authorized": True,
                "require_sponsorship": False,
                "willing_to_relocate": True,
                "remote_friendly": True,
                "preferred_work_model": work_pref,
                "open_to_remote": True,
                "open_to_contract": True,
                "notice_period_days": str(notice_days),
                "gender": "Decline to specify",
                "veteran_status": "No",
                "disability_status": "No",
                "english_proficiency": "Professional"
            },
            "custom_answers": {
                "notice period": str(notice_days),
                "notice period in days": str(notice_days),
                "current ctc": str(current_ctc),
                "expected ctc": str(expected_ctc),
                "current salary": str(current_ctc),
                "expected salary": str(expected_ctc),
                "authorized to work": "Yes",
                "require sponsorship": "No",
                "willing to relocate": "Yes",
                "comfortable working remotely": "Yes"
            }
        }
        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)
        print(f"  ✅ Created: {self.profile_path.name}")

        # 3. Generate config.yaml
        yaml_data = {
            "settings": {
                "dry_run": True,
                "max_applications": max_apps,
                "min_delay": 1.5,
                "max_delay": 2.8,
                "connection_mode": "cdp",
                "cdp_url": f"http://localhost:{cdp_port}",
                "interactive_unknowns": True
            },
            "job_search": {
                "preference": work_pref,
                "keywords": keywords_list,
                "location": location,
                "date_posted": "past-week",
                "easy_apply_only": True,
                "database_file": "jobs.db",
                "csv_file": "applied_jobs.csv"
            },
            "paths": {
                "profile_config": "profile_config.json",
                "resume_pdf": os.path.basename(resume_path),
                "resumes_dir": "resumes",
                "history_file": "applied_jobs.json",
                "screenshots_dir": "screenshots"
            }
        }
        with open(self.yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f, sort_keys=False, default_flow_style=False)
        print(f"  ✅ Created: {self.yaml_path.name}")

        # 4. Initialize Database
        self._init_db()

        print("\n" + "=" * 70)
        print("🎉 CareerOS Setup Completed Successfully!")
        print("=" * 70)
        print("🚀 NEXT STEPS:")
        print(f"  1. Start Chrome with remote debugging: ./scripts/launch_chrome.sh")
        print(f"  2. Preview applications in Dry-Run mode: python3 main.py apply --dry-run")
        print(f"  3. Run live applications: python3 main.py apply --live --limit 5")
        print("=" * 70 + "\n")

    def _init_db(self):
        """Initializes jobs.db SQLite database schema if not present."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                title TEXT,
                company TEXT,
                location TEXT,
                workplace_type TEXT,
                hiring_manager_name TEXT,
                hiring_manager_url TEXT,
                key_skills TEXT,
                job_url TEXT,
                job_description TEXT,
                status TEXT,
                notes TEXT,
                answers_filled TEXT,
                screenshot_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                platform TEXT DEFAULT 'linkedin'
            )
        ''')
        conn.commit()
        conn.close()
        print(f"  ✅ Initialized Database: {self.db_path.name}")

if __name__ == "__main__":
    agent = SetupAgent()
    defaults = "--defaults" in sys.argv or "--non-interactive" in sys.argv
    agent.run(defaults_only=defaults)
