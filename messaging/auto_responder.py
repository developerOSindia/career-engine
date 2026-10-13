"""
Recruiter Auto-Responder Orchestrator.
Coordinates scanning InMails, generating AI responses, previewing, and sending replies.
"""
import asyncio
from typing import List, Optional
from core.browser_engine import BrowserEngine
from core.models import InMailMessage
from messaging.inmail_scanner import InMailScanner
from messaging.message_drafter import MessageDrafter

class RecruiterAutoResponder:
    def __init__(
        self,
        engine: Optional[BrowserEngine] = None,
        dry_run: bool = True,
        limit: int = 5
    ):
        self.engine = engine or BrowserEngine()
        self.dry_run = dry_run
        self.limit = limit
        self.scanner: Optional[InMailScanner] = None
        self.drafter = MessageDrafter()
        self.page = None

    async def run(self, unread_only: bool = True):
        """Executes the InMail discovery and reply pipeline."""
        print(f"\n{'='*60}")
        print("📬 LinkedIn InMail & Recruiter Auto-Reply Engine")
        print(f"  • Mode: {'DRY RUN (Preview Only)' if self.dry_run else 'LIVE AUTO-SEND'}")
        print(f"  • Unread Only: {unread_only}")
        print(f"  • Batch Limit: {self.limit} threads")
        print(f"{'='*60}\n")

        self.page = await self.engine.start()
        is_logged_in = await self.engine.check_linkedin_logged_in()
        if not is_logged_in:
            print("❌ Error: LinkedIn session not authenticated. Please log in on Chrome.")
            await self.engine.close()
            return

        self.scanner = InMailScanner(self.page)
        await self.scanner.navigate_to_messaging()

        threads = await self.scanner.get_conversation_threads(unread_only=unread_only, limit=self.limit)
        print(f"📋 Found {len(threads)} relevant conversation threads.\n")

        if not threads:
            print("ℹ️ No new unread messages or InMails found.")
            await self.engine.close()
            return

        for idx, thread in enumerate(threads, 1):
            print(f"\n[{idx}/{len(threads)}] From: {thread.sender_name} | {thread.sender_headline}")
            print(f"    🏷️ InMail: {'Yes' if thread.is_inmail else 'No'} | Unread: {'Yes' if thread.is_unread else 'No'}")
            
            # Read full transcript
            full_text = await self.scanner.open_thread_and_get_full_text(thread)
            snippet = full_text[:120].replace('\n', ' ')
            print(f"    💬 Message: \"{snippet}...\"")

            # Draft AI reply
            reply_text = self.drafter.draft_reply_for_message(thread)

            print(f"\n    📝 Proposed Reply:")
            print("    " + "-"*50)
            for line in reply_text.split("\n"):
                print(f"    | {line}")
            print("    " + "-"*50)

            if self.dry_run:
                print("    🎯 [PREVIEW] Not sending reply (use --send or --live to deliver).")
            else:
                print("    🚀 Sending reply...")
                sent = await self._send_reply_in_current_thread(reply_text)
                if sent:
                    print("    ✅ Reply successfully delivered!")
                    thread.status = "sent"
                else:
                    print("    ❌ Could not deliver reply.")

            await asyncio.sleep(2.0)

        print("\n" + "="*60)
        print(f"🎉 Processed {len(threads)} recruiter threads.")
        print("="*60 + "\n")

        await self.engine.close()

    async def _send_reply_in_current_thread(self, reply_text: str) -> bool:
        """Finds compose box in active thread, types response, and clicks send."""
        try:
            # Common LinkedIn messaging compose selectors
            compose_box = self.page.locator(
                "div.msg-form__contenteditable[contenteditable='true'], "
                "div[role='textbox'][aria-label*='Write a message']"
            ).first

            if await compose_box.count() == 0 or not await compose_box.is_visible():
                print("    ⚠️ Compose box not found in active thread.")
                return False

            await compose_box.click()
            await asyncio.sleep(0.5)

            # Human-like typing
            await self.engine.human_type(compose_box, reply_text, clear_first=False)
            await asyncio.sleep(1.0)

            # Send button
            send_btn = self.page.locator(
                "button.msg-form__send-button, "
                "button[type='submit']:has-text('Send')"
            ).first

            if await send_btn.count() > 0 and await send_btn.is_visible():
                await send_btn.click()
                await asyncio.sleep(1.5)
                return True
            else:
                # Alternative: press Enter if send button is absent
                await compose_box.press("Enter")
                await asyncio.sleep(1.5)
                return True

        except Exception as e:
            print(f"    ⚠️ Error typing/sending reply: {e}")
            return False
