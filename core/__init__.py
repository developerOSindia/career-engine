"""
Core package for Career Automator.
Provides configuration loading, Chrome CDP browser management, application persistence, and data models.
"""

from .config_loader import Config, get_config
from .models import JobPosting, ApplicationRecord, InMailMessage
from .browser_engine import BrowserEngine
from .tracker import ApplicationTracker
from .smart_dedup import smart_deduplicator, SmartDeduplicator
from .cold_outreach import cold_outreach_synthesizer, ColdOutreachSynthesizer
from .interview_prep import interview_prep_simulator, InterviewPrepSimulator

__all__ = [
    "Config",
    "get_config",
    "JobPosting",
    "ApplicationRecord",
    "InMailMessage",
    "BrowserEngine",
    "ApplicationTracker",
    "smart_deduplicator",
    "SmartDeduplicator",
    "cold_outreach_synthesizer",
    "ColdOutreachSynthesizer",
    "interview_prep_simulator",
    "InterviewPrepSimulator"
]
