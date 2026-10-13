"""
Configuration loader module.
Loads environment variables from .env and settings from config.yaml and profile_config.json.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Find workspace root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

# Explicitly load .env from root directory
env_path = ROOT_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Config:
    """Centralized configuration manager."""
    def __init__(
        self,
        yaml_path: Optional[str] = None,
        profile_path: Optional[str] = None
    ):
        self.root_dir = ROOT_DIR
        self.yaml_path = Path(yaml_path) if yaml_path else self.root_dir / "config.yaml"
        self.profile_path = Path(profile_path) if profile_path else self.root_dir / "profile_config.json"
        
        # Load YAML configuration
        self.yaml_config: Dict[str, Any] = {}
        if self.yaml_path.exists():
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                self.yaml_config = yaml.safe_load(f) or {}

        # Load candidate profile configuration
        self.profile: Dict[str, Any] = {}
        if self.profile_path.exists():
            with open(self.profile_path, "r", encoding="utf-8") as f:
                self.profile = json.load(f) or {}

    # --- API Keys & Credentials ---
    @property
    def gemini_api_keys(self) -> List[str]:
        """Returns all available Gemini API keys in rotation order."""
        keys = []
        for env_var in ["GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
            val = os.getenv(env_var, "").strip()
            if val and val not in keys and not val.startswith("your_"):
                keys.append(val)
        return keys

    @property
    def nvidia_api_key(self) -> str:
        """Returns the NVIDIA / DeepSeek API key."""
        return os.getenv("NVIDIA_API_KEY", "").strip()

    @property
    def nvidia_base_url(self) -> str:
        return os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").strip()

    @property
    def nvidia_model(self) -> str:
        return os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-pro-0813").strip()

    # --- Browser & Connection ---
    @property
    def cdp_url(self) -> str:
        return os.getenv("CHROME_CDP_URL", self.yaml_config.get("settings", {}).get("cdp_url", "http://localhost:9222"))

    @property
    def chrome_user_data_dir(self) -> str:
        return os.path.expanduser(os.getenv("CHROME_USER_DATA_DIR", "~/.chrome-job-agent"))

    # --- Safety & Delays ---
    @property
    def min_delay(self) -> float:
        return float(os.getenv("MIN_ACTION_DELAY", self.yaml_config.get("settings", {}).get("min_delay", 1.5)))

    @property
    def max_delay(self) -> float:
        return float(os.getenv("MAX_ACTION_DELAY", self.yaml_config.get("settings", {}).get("max_delay", 2.8)))

    @property
    def default_max_applications(self) -> int:
        return int(os.getenv("MAX_APPLICATIONS_PER_RUN", self.yaml_config.get("settings", {}).get("max_applications", 10)))

    # --- File Paths ---
    @property
    def database_path(self) -> str:
        db_file = self.yaml_config.get("job_search", {}).get("database_file", "jobs.db")
        return str(self.root_dir / db_file)

    @property
    def csv_path(self) -> str:
        csv_file = self.yaml_config.get("job_search", {}).get("csv_file", "applied_jobs.csv")
        return str(self.root_dir / csv_file)

    @property
    def screenshots_dir(self) -> str:
        ss_dir = self.yaml_config.get("paths", {}).get("screenshots_dir", "screenshots")
        p = self.root_dir / ss_dir
        p.mkdir(parents=True, exist_ok=True)
        return str(p)

    @property
    def resume_path(self) -> str:
        # Check personal info first, then YAML path
        resume_personal = self.profile.get("personal_info", {}).get("resume_path", "")
        if resume_personal and os.path.exists(resume_personal):
            return resume_personal
        yaml_resume = self.yaml_config.get("paths", {}).get("resume_pdf", "resume.pdf")
        return str(self.root_dir / yaml_resume)

    def get_resume_for_job(self, job_title: str = "") -> str:
        """Dynamically selects the best matching resume based on job role and keywords."""
        from core.resume_selector import get_resume_selector
        selector = get_resume_selector()
        return selector.select_resume_for_job(job_title=job_title, default_path=self.resume_path)

    # --- Search Settings ---
    @property
    def search_keywords(self) -> List[str]:
        return self.yaml_config.get("job_search", {}).get("keywords", ["Senior Data Engineer"])

    @property
    def search_location(self) -> str:
        return os.getenv("DEFAULT_LOCATION", self.yaml_config.get("job_search", {}).get("location", "Bengaluru, Karnataka, India"))

    @property
    def search_preference(self) -> str:
        return os.getenv("DEFAULT_WORK_MODE", self.yaml_config.get("job_search", {}).get("preference", "remote_first"))

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Singleton getter for configuration."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
