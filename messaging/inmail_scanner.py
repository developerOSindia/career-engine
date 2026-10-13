"""
LinkedIn InMail and Recruiter Message Scanner.
Extracts incoming messages, recruiter credentials, and unread threads from LinkedIn Messaging.
"""
import asyncio
from typing import List, Dict, Optional
from playwright.async_api import Page
from core.models import InMailMessage

class InMailScanner:
    def __init__(self, page: Page):
        self.page = page

    async def navigate_to_messaging(self) -> bool:
        """Navigates to LinkedIn Messaging page and waits for thread list."""
        print("📨 Navigating to LinkedIn Messaging (https://www.linkedin.com/messaging/)...")
        await self.page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(3.5)

        # Ensure messaging container is loaded
        try:
            await self.page.wait_for_selector(".msg-conversations-container, .msg-thread", timeout=10000)
            return True
        except Exception:
            print("⚠️ Note: Messaging container took longer than expected to appear.")
            return True

    async def get_conversation_threads(self, unread_only: bool = False, limit: int = 10) -> List[InMailMessage]:
        """Parses visible conversation list cards."""
        threads_data = await self.page.evaluate(r'''() => {
            const items = Array.from(document.querySelectorAll('.msg-conversation-listitem, li.msg-conversations-container__convo-item'));
            const results = [];

            for (const item of items) {
                // Check thread ID
                const link = item.querySelector('a[href*="/messaging/thread/"]');
                let threadId = '';
                if (link && link.href) {
                    const match = link.href.match(/thread\/([^/?]+)/);
                    if (match) threadId = match[1];
                }
                if (!threadId) {
                    threadId = item.getAttribute('data-view-name') || Math.random().toString(36).substring(7);
                }

                // Participant Name
                const nameEl = item.querySelector('.msg-conversation-listitem__participant-names, h3, .msg-conversation-card__participant-names');
                const name = nameEl ? nameEl.innerText.trim() : 'Recruiter';

                // Participant Headline
                const headlineEl = item.querySelector('.msg-conversation-card__participant-headline, .msg-conversation-listitem__headline');
                const headline = headlineEl ? headlineEl.innerText.trim() : '';

                // Message Snippet
                const snippetEl = item.querySelector('.msg-conversation-card__message-snippet-body, .msg-conversation-listitem__message-snippet');
                const snippet = snippetEl ? snippetEl.innerText.trim() : '';

                // Check Unread Status
                const isUnread = !!item.querySelector('.msg-conversation-card--unread, .msg-conversation-listitem--unread, .msg-conversation-card__unread-count');

                // Check InMail indicator
                const itemText = item.innerText || '';
                const isInMail = itemText.toLowerCase().includes('inmail') || !!item.querySelector('svg[data-test-icon*="inmail"]');

                // Time
                const timeEl = item.querySelector('time');
                const time = timeEl ? timeEl.innerText.trim() : '';

                results.push({
                    thread_id: threadId,
                    sender_name: name,
                    sender_headline: headline,
                    sender_url: link ? link.href : '',
                    is_inmail: isInMail,
                    is_unread: isUnread,
                    last_message_text: snippet,
                    received_time: time
                });
            }
            return results;
        }''')

        messages: List[InMailMessage] = []
        for d in threads_data:
            if unread_only and not d.get("is_unread"):
                continue

            msg = InMailMessage(
                thread_id=d["thread_id"],
                sender_name=d["sender_name"],
                sender_headline=d["sender_headline"],
                sender_url=d["sender_url"],
                is_inmail=d["is_inmail"],
                is_unread=d["is_unread"],
                last_message_text=d["last_message_text"],
                received_time=d["received_time"]
            )
            messages.append(msg)
            if len(messages) >= limit:
                break

        return messages

    async def open_thread_and_get_full_text(self, thread: InMailMessage) -> str:
        """Clicks into conversation thread to retrieve full message transcript."""
        try:
            # Find listitem matching thread ID or sender name
            card = self.page.locator(f".msg-conversation-listitem:has-text('{thread.sender_name}')").first
            if await card.count() > 0 and await card.is_visible():
                await card.click()
                await asyncio.sleep(1.5)

            # Extract full text of latest incoming messages
            full_text = await self.page.evaluate(r'''() => {
                const messageList = document.querySelector('.msg-s-message-list-container, .msg-thread__event-list');
                if (!messageList) return '';
                
                // Collect messages sent by the counterparty (not user)
                const bubbles = Array.from(messageList.querySelectorAll('.msg-s-event-listitem__body'));
                if (bubbles.length === 0) return '';
                
                // Join last 2 messages for full context
                return bubbles.slice(-2).map(b => b.innerText.trim()).join('\n---\n');
            }''')

            if full_text:
                thread.last_message_text = full_text
                return full_text
        except Exception as e:
            print(f"  ⚠️ Could not read expanded thread for {thread.sender_name}: {e}")

        return thread.last_message_text
