"""
Sanity test script to verify modular imports, .env loading, and AI solver.
"""
import os
import sys

# Ensure root directory in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config_loader import get_config
from core.models import JobPosting, ApplicationRecord, InMailMessage
from core.tracker import ApplicationTracker
from ai.ai_solver import UnifiedAISolver
from platforms.linkedin.scanner import LinkedInJobScanner
from platforms.linkedin.form_filler import LinkedInFormFiller
from messaging.inmail_scanner import InMailScanner
from messaging.message_drafter import MessageDrafter

def run_tests():
    print("🧪 Running Career Automator Sanity Checks...\n")

    # 1. Config & .env
    config = get_config()
    print(f"✅ Config loaded. Root dir: {config.root_dir}")
    print(f"✅ Gemini keys configured: {len(config.gemini_api_keys)}")
    print(f"✅ NVIDIA key configured: {'Yes' if config.nvidia_api_key else 'No'}")
    assert len(config.gemini_api_keys) > 0, "At least one Gemini key must be present"

    # 2. Database Tracker
    tracker = ApplicationTracker()
    summary = tracker.get_summary()
    print(f"✅ Tracker loaded. Total records: {summary['total_records']}, Applied: {summary['applied']}")
    assert 'applied' in summary, "Database must provide applied count"

    # 3. AI Solver & InMail Drafter Test
    ai = UnifiedAISolver()
    
    # Test Question Solving
    exp_years = str(config.profile.get("work_summary", {}).get("total_years_experience", 5))
    q_ans = ai.solve_question("How many years of work experience do you have with Databricks?")
    print(f"✅ AI QA Test: 'Databricks experience' -> '{q_ans}'")
    assert q_ans.isdigit(), f"Expected numeric experience, got '{q_ans}'"

    # Test InMail Drafting
    test_inmail = InMailMessage(
        thread_id="test-123",
        sender_name="Sarah Jenkins",
        sender_headline="Senior Talent Partner at Tier-1 FinTech",
        sender_url="",
        is_inmail=True,
        is_unread=True,
        last_message_text="Hi! We loved your engineering background and would love to connect about new opportunities."
    )
    drafter = MessageDrafter(ai)
    draft = drafter.draft_reply_for_message(test_inmail)
    print(f"\n✅ AI InMail Draft Test Generated:\n{'-'*50}\n{draft}\n{'-'*50}")
    assert len(draft) > 30, "Draft reply should be generated"

    print("\n🎉 ALL ARCHITECTURAL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
