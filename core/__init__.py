"""
Core package for Career Automator.
Provides configuration loading, Chrome CDP browser management, application persistence, and data models.
"""

from .config_loader import Config, get_config
from .models import JobPosting, ApplicationRecord, InMailMessage
from .browser_engine import BrowserEngine
from .tracker import ApplicationTracker

__all__ = [
    "Config",
    "get_config",
    "JobPosting",
    "ApplicationRecord",
    "InMailMessage",
    "BrowserEngine",
    "ApplicationTracker"
]
