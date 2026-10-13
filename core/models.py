"""
Data models for Career Automator.
Standardizes data exchange across browser scanners, form fillers, message responders, and trackers.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime

@dataclass
class JobPosting:
    """Represents a job discovered on a platform."""
    job_id: str
    title: str
    company: str
    location: str
    url: str
    platform: str = "linkedin"
    workplace_type: str = "On-site"
    hiring_manager_name: str = ""
    hiring_manager_url: str = ""
    key_skills: str = ""
    job_description: str = ""
    easy_apply: bool = True

@dataclass
class ApplicationRecord:
    """Represents a tracked job application event."""
    job_id: str
    title: str
    company: str
    location: str
    job_url: str
    platform: str = "linkedin"
    workplace_type: str = "On-site"
    hiring_manager_name: str = ""
    hiring_manager_url: str = ""
    key_skills: str = ""
    job_description: str = ""
    status: str = "applied"  # applied, dry_run_completed, skipped, failed, needs_review
    notes: str = ""
    answers_filled: Dict[str, str] = field(default_factory=dict)
    screenshot_path: str = ""
    applied_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class InMailMessage:
    """Represents a recruiter message or InMail received."""
    thread_id: str
    sender_name: str
    sender_headline: str
    sender_url: str
    is_inmail: bool
    is_unread: bool
    last_message_text: str
    role_mentioned: Optional[str] = None
    company_mentioned: Optional[str] = None
    received_time: Optional[str] = None
    draft_reply: Optional[str] = None
    status: str = "pending"  # pending, draft_ready, sent, ignored
