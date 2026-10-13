"""
CareerEngine Intelligent Resume Selector.
Dynamically selects the most relevant resume PDF based on the target job title,
role keywords, and domain.

Naming conventions supported in the `resumes/` (or `resume/`) directory:
  - Data Engineering:      *_DE*.pdf, *_data_engineer*.pdf, *_pyspark*.pdf, *_etl*.pdf
  - Data Science / ML:     *_DS*.pdf, *_data_science*.pdf, *_ml*.pdf, *_machine_learning*.pdf
  - Software Engineering:   *_SWE*.pdf, *_sde*.pdf, *_software*.pdf, *_backend*.pdf, *_fullstack*.pdf
  - AI / GenAI Platforms:  *_AI*.pdf, *_genai*.pdf, *_llm*.pdf, *_agent*.pdf
  - MLOps / DevOps:        *_MLOps*.pdf, *_devops*.pdf, *_cloud*.pdf, *_platform*.pdf
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent

# Role classification mapping to search patterns in filename
ROLE_PATTERNS: Dict[str, List[str]] = {
    "data_engineering": [
        r"(?:^|[\W_])de(?:[\W_]|$)",
        r"data[_\s-]?engineer",
        r"pyspark",
        r"databricks",
        r"big[_\s-]?data",
        r"etl"
    ],
    "data_science": [
        r"(?:^|[\W_])ds(?:[\W_]|$)",
        r"data[_\s-]?scien(?:ce|tist)",
        r"machine[_\s-]?learning",
        r"(?:^|[\W_])ml(?:[\W_]|$)",
        r"analytics"
    ],
    "ai_engineer": [
        r"(?:^|[\W_])ai(?:[\W_]|$)",
        r"gen[_\s-]?ai",
        r"llm",
        r"artificial[_\s-]?intelligence",
        r"agent"
    ],
    "mlops": [
        r"mlops",
        r"devops",
        r"cloud",
        r"platform[_\s-]?engineer",
        r"sre"
    ],
    "software_engineering": [
        r"swe",
        r"sde",
        r"software[_\s-]?engineer",
        r"backend",
        r"full[_\s-]?stack",
        r"frontend",
        r"developer"
    ]
}

class ResumeSelector:
    """Intelligently matches candidate resumes from the resumes/ folder to job postings."""
    
    def __init__(self, resumes_dir: Optional[str] = None):
        self.resumes_dir = Path(resumes_dir) if resumes_dir else ROOT_DIR / "resumes"
            
        self.resumes_dir.mkdir(parents=True, exist_ok=True)

    def list_available_resumes(self) -> List[Path]:
        """Returns all PDF resume files found in resumes directory."""
        if not self.resumes_dir.exists():
            return []
        files = list(self.resumes_dir.glob("*.pdf"))
        # Also check root for backward compatibility
        root_pdfs = list(ROOT_DIR.glob("*.pdf"))
        all_pdfs = files + [p for p in root_pdfs if p not in files]
        return sorted(all_pdfs, key=lambda p: p.stat().st_mtime, reverse=True)

    def detect_job_category(self, job_title: str) -> Optional[str]:
        """Detects the role domain from the job title."""
        title_lower = job_title.lower()

        # Check explicit roles in priority order
        if any(re.search(pat, title_lower) for pat in ROLE_PATTERNS["data_engineering"]):
            return "data_engineering"
        if any(re.search(pat, title_lower) for pat in ROLE_PATTERNS["data_science"]):
            return "data_science"
        if any(re.search(pat, title_lower) for pat in ROLE_PATTERNS["ai_engineer"]):
            return "ai_engineer"
        if any(re.search(pat, title_lower) for pat in ROLE_PATTERNS["mlops"]):
            return "mlops"
        if any(re.search(pat, title_lower) for pat in ROLE_PATTERNS["software_engineering"]):
            return "software_engineering"
        return None

    def select_resume_for_job(self, job_title: str = "", default_path: str = "") -> str:
        """
        Selects the best matching resume file for the given job title.
        Returns the absolute filepath to the chosen resume PDF.
        """
        available = self.list_available_resumes()
        if not available:
            # Fall back to default path if supplied
            if default_path and os.path.exists(default_path):
                return default_path
            # Check default resume.pdf in root
            root_default = ROOT_DIR / "resume.pdf"
            return str(root_default)

        # If only 1 resume exists in folder, return it directly
        if len(available) == 1:
            chosen = available[0]
            print(f"  📄 [Resume Selector] Using available resume: {chosen.name}")
            return str(chosen)

        # Detect category from job title
        category = self.detect_job_category(job_title)
        if category and category in ROLE_PATTERNS:
            patterns = ROLE_PATTERNS[category]
            for resume in available:
                fname_lower = resume.name.lower()
                for pat in patterns:
                    if re.search(pat, fname_lower):
                        print(f"  🎯 [Resume Selector] Matched '{category}' resume for '{job_title}': {resume.name}")
                        return str(resume)

        # If default_path is specified and exists in available, use it
        if default_path:
            abs_def = os.path.abspath(default_path)
            if any(os.path.abspath(r) == abs_def for r in available):
                return abs_def

        # Fallback to the first/most recently modified resume
        fallback = available[0]
        print(f"  📄 [Resume Selector] Using primary resume: {fallback.name}")
        return str(fallback)

# Global singleton
_selector_instance: Optional[ResumeSelector] = None

def get_resume_selector() -> ResumeSelector:
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = ResumeSelector()
    return _selector_instance
