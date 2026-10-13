"""
CareerEngine Semantic AI Matcher & Dynamic Pitch Generator.
Evaluates job descriptions against candidate profiles to score alignment,
filter out poor fits, recommend the best resume tag, and generate tailored pitch notes.
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from core.config_loader import get_config
from ai.ai_solver import UnifiedAISolver

ROLE_TAG_MAPPING = {
    "data_engineering": "_DE",
    "data_science": "_DS",
    "ai_engineer": "_AI",
    "software_engineering": "_SWE",
    "mlops": "_MLOps"
}

ROLE_KEYWORDS = {
    "_DE": ["spark", "pyspark", "airflow", "kafka", "dbt", "databricks", "snowflake", "bigquery", "etl", "data warehouse", "data lake", "sql"],
    "_DS": ["machine learning", "pandas", "numpy", "scikit-learn", "statistics", "a/b testing", "predictive", "tableau", "deep learning", "modeling"],
    "_AI": ["llm", "generative ai", "rag", "langchain", "prompt", "vector database", "fine-tuning", "gemini", "openai", "embeddings"],
    "_SWE": ["python", "typescript", "react", "node.js", "backend", "api", "fastapi", "django", "postgresql", "microservices", "system design"],
    "_MLOps": ["mlflow", "kubeflow", "docker", "kubernetes", "model deployment", "ci/cd", "triton", "monitoring", "sagemaker", "drift"]
}

@dataclass
class JobMatchResult:
    match_score: int                   # 0 to 100
    recommended_role_tag: str          # _DE, _DS, _AI, _SWE, _MLOps
    key_matching_skills: List[str]
    missing_prerequisites: List[str]
    meets_threshold: bool
    reasoning_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SemanticMatcher:
    """Semantic Matcher and Pitch Note Generator using rotational AI models and local heuristics."""

    def __init__(self, profile_data: Optional[Dict[str, Any]] = None):
        config = get_config()
        self.profile = profile_data or config.profile
        self.ai = UnifiedAISolver(self.profile)

    def evaluate_job_fit(
        self,
        job_title: str,
        job_description: str = "",
        min_threshold: int = 50
    ) -> JobMatchResult:
        """
        Evaluates the alignment between candidate profile and job requirements.
        Uses AI reasoning if available, with deterministic heuristic fallback.
        """
        if not job_description or len(job_description.strip()) < 50:
            return self.heuristic_match(job_title, job_description, min_threshold)

        # Attempt AI evaluation via Gemini / DeepSeek
        prompt = f"""
You are an expert technical hiring advisor evaluating candidate alignment for an engineering job.

{self.ai.candidate_summary}

Target Job Title: {job_title}
Job Description Excerpt:
{job_description[:2500]}

Evaluate this job posting for the candidate. Return ONLY a valid JSON object matching this schema:
{{
  "match_score": <integer from 0 to 100>,
  "recommended_role_tag": <one of "_DE", "_DS", "_AI", "_SWE", "_MLOps">,
  "key_matching_skills": [<list of up to 5 overlapping skills>],
  "missing_prerequisites": [<list of up to 3 missing required skills if any>],
  "reasoning_summary": "<one sentence summarizing fit>"
}}
"""
        try:
            raw_res = self.ai._call_gemini(prompt, max_tokens=220)
            if not raw_res:
                raw_res = self.ai._call_claude(prompt, max_tokens=220)
            if not raw_res:
                raw_res = self.ai._call_openai(prompt, max_tokens=220)
            if not raw_res:
                raw_res = self.ai._call_nvidia(prompt)

            if raw_res and raw_res[0]:
                cleaned = raw_res[0].strip()
                # Clean potential markdown fences
                if "```json" in cleaned:
                    cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned:
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()

                parsed = json.loads(cleaned)
                score = max(0, min(100, int(parsed.get("match_score", 60))))
                tag = parsed.get("recommended_role_tag", "_SWE")
                if tag not in ROLE_KEYWORDS:
                    tag = "_SWE"

                return JobMatchResult(
                    match_score=score,
                    recommended_role_tag=tag,
                    key_matching_skills=parsed.get("key_matching_skills", []),
                    missing_prerequisites=parsed.get("missing_prerequisites", []),
                    meets_threshold=score >= min_threshold,
                    reasoning_summary=parsed.get("reasoning_summary", "Evaluated via AI model.")
                )
        except Exception:
            pass  # Fallback to local heuristic

        return self.heuristic_match(job_title, job_description, min_threshold)

    def heuristic_match(
        self,
        job_title: str,
        job_description: str = "",
        min_threshold: int = 50
    ) -> JobMatchResult:
        """Fast, zero-latency local heuristic alignment."""
        text = f"{job_title} {job_description}".lower()

        scores = {}
        for tag, keywords in ROLE_KEYWORDS.items():
            matches = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text)]
            scores[tag] = matches

        # Pick role tag with most keyword overlaps
        best_tag = max(scores.keys(), key=lambda t: len(scores[t]))
        matched_skills = scores[best_tag][:5]

        # Calculate a baseline match score
        base_score = 40
        if best_tag in ["_DE", "_SWE"]:
            base_score = 75
        base_score += min(25, len(matched_skills) * 5)

        return JobMatchResult(
            match_score=base_score,
            recommended_role_tag=best_tag,
            key_matching_skills=matched_skills or ["General Software Engineering"],
            missing_prerequisites=[],
            meets_threshold=base_score >= min_threshold,
            reasoning_summary=f"Matched {len(matched_skills)} key competencies for {best_tag} profile."
        )

    def generate_pitch_note(
        self,
        job_title: str,
        company: str,
        job_description: str = ""
    ) -> str:
        """
        Generates a concise 2-3 sentence high-converting pitch note for startup applications
        (Wellfound notes, Instahyre cover note, or recruiter InMail outreach).
        """
        work = self.profile.get("work_summary", {})
        personal = self.profile.get("personal_info", {})
        years = work.get("total_years_experience", 5)
        notice = work.get("notice_period_days", 30)

        prompt = f"""
You are a top-tier software engineer applying to {company} for the role '{job_title}'.
Write a crisp, confident, 2-to-3 sentence note directly to the hiring manager or founder.
Requirements:
- NO generic pleasantries ("I hope this message finds you well", "I am excited to apply").
- Directly highlight {years}+ years of relevant technical experience and concrete capability.
- Mention readiness to join on {notice} days notice.
- Tone: high-agency, professional, concise engineer.

Candidate Profile:
{self.ai.candidate_summary}

Job Description Context:
{job_description[:1200] if job_description else job_title}
"""
        try:
            res = self.ai._call_gemini(prompt, max_tokens=150)
            if not res:
                res = self.ai._call_claude(prompt, max_tokens=150)
            if not res:
                res = self.ai._call_openai(prompt, max_tokens=150)
            if not res:
                res = self.ai._call_nvidia(prompt)
            if res and res[0]:
                note = res[0].strip().replace('"', '').strip()
                if len(note) > 40:
                    return note
        except Exception:
            pass

        # Robust heuristic fallback pitch note
        return (
            f"Hi team, I bring {years}+ years of engineering experience delivering distributed data pipelines "
            f"and robust systems aligned with {company}'s tech stack. I'm based in Bengaluru, legally authorized to work, "
            f"and actively available to join on {notice} days notice."
        )

semantic_matcher = SemanticMatcher()
