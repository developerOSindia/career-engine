"""
Recruiter messaging and InMail automation package.
Scans LinkedIn InMails/messages, drafts personalized AI responses, and auto-replies.
"""

from .inmail_scanner import InMailScanner
from .message_drafter import MessageDrafter
from .auto_responder import RecruiterAutoResponder

__all__ = ["InMailScanner", "MessageDrafter", "RecruiterAutoResponder"]
