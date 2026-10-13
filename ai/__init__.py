"""
AI package for Career Automator.
Unified router across Gemini 3.x Flash-lite rotation and NVIDIA DeepSeek models.
"""

from .ai_solver import UnifiedAISolver
from .prompts import SYSTEM_PROMPT_QA, SYSTEM_PROMPT_INMAIL

__all__ = ["UnifiedAISolver", "SYSTEM_PROMPT_QA", "SYSTEM_PROMPT_INMAIL"]
