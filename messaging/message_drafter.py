"""
Message Drafter module.
Synthesizes professional, highly tailored replies to recruiter InMails and messages.
"""
from typing import Optional
from core.models import InMailMessage
from ai.ai_solver import UnifiedAISolver

class MessageDrafter:
    def __init__(self, ai_solver: Optional[UnifiedAISolver] = None):
        self.ai = ai_solver or UnifiedAISolver()

    def draft_reply_for_message(self, message: InMailMessage) -> str:
        """Generates contextual reply to recruiter message."""
        print(f"✍️ Drafting tailored response for {message.sender_name} ({message.sender_headline})...")
        
        reply = self.ai.draft_inmail_reply(
            sender_name=message.sender_name,
            sender_headline=message.sender_headline,
            message_text=message.last_message_text
        )

        if not reply:
            # Context-aware fallback using profile configuration
            prof = self.ai.profile.get("personal_info", {})
            work = self.ai.profile.get("work_summary", {})
            cand_name = prof.get("full_name", "Candidate")
            cand_title = work.get("current_title", "Senior Engineer")
            cand_company = work.get("current_company", "current company")
            cand_exp = work.get("total_years_experience", 5)
            cand_np = work.get("notice_period_days", 30)
            cand_ectc = work.get("expected_salary_inr_lpa", "Competitive")
            cand_phone = prof.get("full_phone", "")

            reply = (
                f"Hi {message.sender_name.split()[0] if message.sender_name else 'there'},\n\n"
                f"Thank you for reaching out! I am currently a {cand_title} at {cand_company} with {cand_exp} years "
                f"of experience.\n\n"
                f"I would love to learn more about the role. Could you please share the detailed Job Description "
                f"and the budgeted compensation range? (My expected CTC is {cand_ectc} LPA, with a notice period of {cand_np} days).\n\n"
                f"Best regards,\n{cand_name}"
                + (f"\n{cand_phone}" if cand_phone else "")
            )

        message.draft_reply = reply
        message.status = "draft_ready"
        return reply
