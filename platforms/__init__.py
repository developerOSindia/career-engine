"""
Platforms package for Career Automator.
Supports multi-job-board expansion (LinkedIn, Naukri, Wellfound, Indeed) via a unified interface.
"""

from .base import BasePlatform
from .naukri.connector import NaukriPlatform
from .linkedin.agent import LinkedInApplicationAgent
from .hirist.connector import HiristPlatform
from .instahyre.connector import InstahyrePlatform
from .wellfound.connector import WellfoundPlatform
from .indeed.connector import IndeedPlatform
from .glassdoor.connector import GlassdoorPlatform
from .foundit.connector import FounditPlatform

__all__ = [
    "BasePlatform",
    "NaukriPlatform",
    "LinkedInApplicationAgent",
    "HiristPlatform",
    "InstahyrePlatform",
    "WellfoundPlatform",
    "IndeedPlatform",
    "GlassdoorPlatform",
    "FounditPlatform"
]
