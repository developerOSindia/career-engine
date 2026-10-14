"""
CareerEngine ATS Resume Keyword Gap Optimizer & Tailoring Engine.
Analyzes job postings against candidate profile facts and resumes, identifies critical
keyword and competency gaps, and synthesizes high-converting, ATS-tailored achievement
bullets and recruiter pitch notes using multi-provider AI reasoning.
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

from core.config_loader import get_config
from core.resume_selector import get_resume_selector, ROLE_PATTERNS
from core.semantic_matcher import semantic_matcher, ROLE_KEYWORDS
from ai.ai_solver import UnifiedAISolver

ROOT_DIR = Path(__file__).resolve().parent.parent

# Tech keyword extraction vocabulary
COMMON_TECH_KEYWORDS = [
    "python", "pyspark", "spark", "apache spark", "sql", "scala", "java", "golang", "c++", "rust",
    "databricks", "delta lake", "delta live tables", "trino", "presto", "hive", "hadoop",
    "aws", "s3", "ec2", "emr", "glue", "lambda", "redshift", "athena", "dms", "kinesis",
    "azure", "azure data factory", "synapse", "azure databricks", "blob storage",
    "gcp", "bigquery", "dataflow", "cloud storage", "dataproc", "composer",
    "airflow", "prefect", "dagster", "dbt", "kafka", "flink", "rabbitmq", "pulsar",
    "docker", "kubernetes", "k8s", "terraform", "helm", "ci/cd", "jenkins", "github actions",
    "snowflake", "postgresql", "postgres", "mysql", "mongodb", "cassandra", "neo4j", "cockroachdb",
    "redis", "elasticsearch", "opensearch", "clickhouse",
    "machine learning", "ml", "deep learning", "nlp", "llm", "genai", "generative ai",
    "langchain", "llamaindex", "rag", "vector database", "pinecone", "weaviate", "qdrant",
    "fastapi", "flask", "django", "rest apis", "graphql", "grpc", "microservices",
    "data modeling", "star schema", "dimensional modeling", "etl", "elt", "data pipeline"
]

@dataclass
class ResumeTailorReport:
    job_title: str
    company: str
    target_role_tag: str
    recommended_resume_file: str
    baseline_ats_score: int
    optimized_ats_score: int
    matched_skills: List[str]
    missing_critical_keywords: List[str]
    missing_nice_to_haves: List[str]
    tailored_achievement_bullets: List[str]
    bespoke_pitch_note: str
    actionable_ats_tips: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ResumeTailor:
    """Intelligently audits JD keyword gaps and synthesizes tailored resume bullets."""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.profile = self.config.profile
        self.resume_selector = get_resume_selector()
        self.ai = UnifiedAISolver()

    def tailor_for_job(
        self,
        job_title: str,
        job_description: str = "",
        company: str = "Target Company",
        target_role: Optional[str] = None
    ) -> ResumeTailorReport:
        """Generates tailored ATS keyword audit and custom resume bullets for a job description."""
        combined_text = f"{job_title} {job_description}".lower()

        # 1. Identify Target Role Tag & Best Matching Resume PDF
        detected_role = target_role or self.resume_selector.detect_job_category(job_title)
        role_tag_map = {
            "data_engineering": "_DE",
            "data_science": "_DS",
            "ai_engineer": "_AI",
            "software_engineering": "_SWE",
            "mlops": "_MLOps"
        }
        target_role_tag = role_tag_map.get(detected_role, "_DE")
        selected_resume = self.resume_selector.select_resume_for_job(job_title, job_description)
        resume_filename = Path(selected_resume).name if selected_resume else "Kalash_Jindal_DE_resume.pdf"

        # 2. Extract Required Tech Keywords from JD
        required_keywords = []
        for kw in COMMON_TECH_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', combined_text):
                required_keywords.append(kw)

        # Candidate skills
        candidate_skills = {k.lower(): v for k, v in self.profile.get("skills_years_experience", {}).items()}
        matched_skills = []
        missing_skills = []

        for kw in required_keywords:
            if kw in candidate_skills:
                matched_skills.append(f"{kw.title()} ({candidate_skills[kw]}y)")
            else:
                missing_skills.append(kw.title())

        # Split into critical vs nice-to-haves
        missing_critical = missing_skills[:4]
        missing_nice_to_have = missing_skills[4:8]

        # Calculate Scores
        total_req = max(1, len(required_keywords))
        matched_count = len(matched_skills)
        baseline_score = min(98, max(45, int((matched_count / total_req) * 85) + (15 if target_role_tag == "_DE" else 5)))
        optimized_score = min(99, baseline_score + min(25, len(missing_critical) * 5 + 8))

        # 3. Generate Tailored Achievement Bullets using Multi-Provider LLM
        bullets = self._generate_tailored_bullets(job_title, company, required_keywords, matched_skills, missing_critical)

        # 4. Generate Pitch Note
        pitch_note = semantic_matcher.generate_pitch_note(
            job_title=job_title,
            company=company,
            job_description=job_description
        )

        # 5. Actionable ATS Tips
        action_tips = [
            f"Embed missing keywords like {', '.join(missing_critical[:3])} into your experience bullet points.",
            f"Use the recommended resume variant `{resume_filename}` which matches the `{target_role_tag}` role track.",
            f"Emphasize distributed scalability metrics (e.g., records/sec, latency reduction, cost savings) to satisfy ATS screening filters."
        ]

        return ResumeTailorReport(
            job_title=job_title,
            company=company,
            target_role_tag=target_role_tag,
            recommended_resume_file=resume_filename,
            baseline_ats_score=baseline_score,
            optimized_ats_score=optimized_score,
            matched_skills=matched_skills[:10],
            missing_critical_keywords=missing_critical,
            missing_nice_to_haves=missing_nice_to_have,
            tailored_achievement_bullets=bullets,
            bespoke_pitch_note=pitch_note,
            actionable_ats_tips=action_tips
        )

    def tailor_for_job_id(self, job_id: str) -> Optional[ResumeTailorReport]:
        """Looks up job from jobs.db and generates tailored resume recommendations."""
        try:
            conn = sqlite3.connect(self.config.database_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, company, job_description, key_skills
                FROM applications
                WHERE job_id = ? OR id = ?
                LIMIT 1
            """, (str(job_id), str(job_id)))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            title, company, jd, skills = row
            full_jd = f"{jd or ''} {skills or ''}"
            return self.tailor_for_job(job_title=title, job_description=full_jd, company=company)
        except Exception:
            return None

    def _generate_tailored_bullets(
        self,
        job_title: str,
        company: str,
        req_keywords: List[str],
        matched_skills: List[str],
        missing_critical: List[str]
    ) -> List[str]:
        """Synthesizes high-impact XYZ resume bullets using multi-provider AI reasoning."""
        work = self.profile.get("work_summary", {})
        years = work.get("total_years_experience", 5)
        top_tech = ", ".join(req_keywords[:6]) if req_keywords else "PySpark, AWS, Databricks, SQL"

        prompt = f"""
You are a Staff Technical Recruiter and ATS Optimization Expert.
Write 3 punchy, high-impact resume achievement bullet points for a Senior Engineer applying to {company} for '{job_title}'.
Target Tech Stack / Keywords: {top_tech}
Missing Keywords to strategically bridge: {', '.join(missing_critical)}

Requirements:
- Follow Google/Amazon XYZ formula: "Accomplished [X], as measured by [Y], by doing [Z]"
- Include concrete metrics (e.g. 50M+ records/day, 4x latency reduction, 99.9% uptime, 40% cost reduction).
- Tone: high-agency, authoritative senior engineer.
- Output ONLY the 3 bullet points, each starting with "• ".
"""
        try:
            res = self.ai._call_gemini(prompt, max_tokens=220)
            if not res:
                res = self.ai._call_claude(prompt, max_tokens=220)
            if not res:
                res = self.ai._call_openai(prompt, max_tokens=220)
            if not res:
                res = self.ai._call_nvidia(prompt, max_tokens=220)

            if res and res[0]:
                lines = [line.strip() for line in res[0].split("\n") if line.strip().startswith("•") or line.strip().startswith("-")]
                if len(lines) >= 2:
                    return [re.sub(r'^[•\-\*]\s*', '', l) for l in lines[:3]]
        except Exception:
            pass

        # Robust deterministic fallback bullets
        return [
            f"Architected distributed ETL and streaming pipelines using {top_tech}, scaling daily throughput to 50M+ events while reducing compute costs by 35%.",
            f"Automated mission-critical data workflows and CI/CD validation gates, cutting deployment rollbacks by 4x and guaranteeing 99.9% SLA uptime.",
            f"Modernized legacy batch processing pipelines into scalable architectures, accelerating analytical query execution by 60% across cross-functional teams."
        ]

    def format_cli_report(self, report: ResumeTailorReport) -> str:
        """Formats the tailoring report into an ANSI terminal card."""
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        RESET = "\033[0m"

        lines = []
        lines.append(f"\n{BOLD}{'='*68}{RESET}")
        lines.append(f"{CYAN}{BOLD}  🎯 CAREERENGINE ATS RESUME TAILOR & KEYWORD OPTIMIZER{RESET}")
        lines.append(f"{BOLD}{'='*68}{RESET}\n")

        lines.append(f"  {BOLD}Target Position:{RESET}  {report.job_title} @ {report.company}")
        lines.append(f"  {BOLD}Selected Resume:{RESET}  📄 {report.recommended_resume_file} [{GREEN}{report.target_role_tag}{RESET}]")
        lines.append(f"  {BOLD}ATS Match Score:{RESET}  {YELLOW}{report.baseline_ats_score}% Baseline{RESET} ➔ {GREEN}{BOLD}{report.optimized_ats_score}% Optimized{RESET}\n")

        # Matched Skills
        if report.matched_skills:
            lines.append(f"  {GREEN}{BOLD}Verified Matching Skills ({len(report.matched_skills)}):{RESET}")
            lines.append(f"    {', '.join(report.matched_skills[:8])}")

        # Missing Keywords
        if report.missing_critical_keywords:
            lines.append(f"\n  {YELLOW}{BOLD}Missing Critical Keywords (High ATS Priority):{RESET}")
            for kw in report.missing_critical_keywords:
                lines.append(f"    ⚠️ {kw}")

        # Tailored Bullet Points
        lines.append(f"\n  {CYAN}{BOLD}AI-Tailored Resume Achievement Bullets (XYZ Format):{RESET}")
        for idx, bullet in enumerate(report.tailored_achievement_bullets, 1):
            lines.append(f"    {idx}. {bullet}")

        # Recruiter Pitch
        lines.append(f"\n  {BOLD}Personalized Recruiter Pitch Note:{RESET}")
        lines.append(f"    \"{report.bespoke_pitch_note}\"")

        # Actionable Tips
        lines.append(f"\n  {DIM}Optimization Advice:{RESET}")
        for tip in report.actionable_ats_tips:
            lines.append(f"    • {tip}")

        lines.append(f"\n{BOLD}{'='*68}{RESET}\n")
        return "\n".join(lines)

resume_tailor = ResumeTailor()
