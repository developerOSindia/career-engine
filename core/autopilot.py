"""
CareerEngine Autonomous Auto-Pilot Engine.
Provides background scheduling, circadian work-hour pacing, multi-platform round-robin cycling,
daily quota enforcement, and automated recruiter InMail scanning.
"""

import os
import sys
import time
import random
import asyncio
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from core.config_loader import get_config
from core.tracker import ApplicationTracker
from messaging.auto_responder import RecruiterAutoResponder

DEFAULT_PLATFORMS = ["linkedin", "naukri", "wellfound", "instahyre", "indeed", "glassdoor", "foundit", "hirist"]

class AutoPilotEngine:
    """
    Autonomous multi-platform runner that continuously applies to jobs and monitors
    recruiter InMails while strictly enforcing daily rate limits and human pacing.
    """

    def __init__(
        self,
        interval_minutes: int = 180,
        daily_limit: int = 20,
        session_limit: int = 5,
        platforms: Optional[List[str]] = None,
        inmail_check: bool = True,
        business_hours_only: bool = True,
        dry_run: bool = True
    ):
        self.config = get_config()
        self.tracker = ApplicationTracker()
        self.interval_minutes = interval_minutes
        self.daily_limit = daily_limit
        self.session_limit = session_limit
        self.platforms = platforms or DEFAULT_PLATFORMS
        self.inmail_check = inmail_check
        self.business_hours_only = business_hours_only
        self.dry_run = dry_run

        self.is_running = False
        self._stop_event = threading.Event()
        self.worker_thread: Optional[threading.Thread] = None

        self.state = "IDLE"  # IDLE, RUNNING_CYCLE, RESTING, DAILY_LIMIT_REACHED, OUTSIDE_HOURS, STOPPED
        self.platform_index = 0
        self.current_platform = ""
        self.last_run_time: Optional[str] = None
        self.next_run_time: Optional[str] = None
        self.cycle_logs: List[Dict[str, Any]] = []

    def is_within_business_hours(self) -> bool:
        """Returns True if current local time is between 09:00 and 19:00."""
        if not self.business_hours_only:
            return True
        now = datetime.now()
        # Monday is 0, Sunday is 6
        if now.weekday() >= 6:  # Sunday rest
            return False
        return 9 <= now.hour < 19

    def get_status(self) -> Dict[str, Any]:
        """Returns complete Auto-Pilot operational metrics for CLI and Web Studio."""
        today_count = self.tracker.get_today_application_count()
        today_platforms = self.tracker.get_today_by_platform()

        return {
            "is_running": self.is_running,
            "state": self.state,
            "dry_run": self.dry_run,
            "daily_limit": self.daily_limit,
            "today_count": today_count,
            "today_remaining": max(0, self.daily_limit - today_count),
            "today_by_platform": today_platforms,
            "interval_minutes": self.interval_minutes,
            "session_limit": self.session_limit,
            "configured_platforms": self.platforms,
            "current_platform": self.current_platform,
            "last_run_time": self.last_run_time,
            "next_run_time": self.next_run_time,
            "business_hours_only": self.business_hours_only,
            "inmail_check": self.inmail_check,
            "recent_cycles": self.cycle_logs[-10:]
        }

    def _execute_platform_batch(self, platform_name: str, limit: int) -> int:
        """Executes a single platform application batch synchronously inside the thread."""
        print(f"\n🤖 [Auto-Pilot] Executing cycle on platform: {platform_name.upper()} (Limit: {limit})")
        from main import get_agent  # Dynamically imported from main
        
        agent = None
        if platform_name == "linkedin":
            from platforms.linkedin.agent import LinkedInApplicationAgent
            agent = LinkedInApplicationAgent(dry_run=self.dry_run, limit=limit)
        elif platform_name == "naukri":
            from platforms.naukri.connector import NaukriPlatform
            agent = NaukriPlatform(dry_run=self.dry_run, limit=limit)
        elif platform_name == "wellfound":
            from platforms.wellfound.connector import WellfoundPlatform
            agent = WellfoundPlatform(dry_run=self.dry_run, limit=limit)
        elif platform_name == "instahyre":
            from platforms.instahyre.connector import InstahyrePlatform
            agent = InstahyrePlatform(dry_run=self.dry_run, limit=limit)
        elif platform_name == "indeed":
            from platforms.indeed.connector import IndeedPlatform
            agent = IndeedPlatform(dry_run=self.dry_run, limit=limit)
        elif platform_name == "glassdoor":
            from platforms.glassdoor.connector import GlassdoorPlatform
            agent = GlassdoorPlatform(dry_run=self.dry_run, limit=limit)
        elif platform_name == "foundit":
            from platforms.foundit.connector import FounditPlatform
            agent = FounditPlatform(dry_run=self.dry_run, limit=limit)
        elif platform_name == "hirist":
            from platforms.hirist.connector import HiristPlatform
            agent = HiristPlatform(dry_run=self.dry_run, limit=limit)

        if not agent:
            print(f"⚠️ [Auto-Pilot] Unknown platform {platform_name}")
            return 0

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(agent.run())
            loop.close()
            return limit
        except Exception as e:
            print(f"⚠️ [Auto-Pilot] Notice during {platform_name} execution: {e}")
            return 0

    def _execute_inmail_check(self) -> None:
        """Scans unread recruiter messages and answers them."""
        print("📬 [Auto-Pilot] Checking incoming recruiter messages...")
        try:
            responder = RecruiterAutoResponder(dry_run=self.dry_run, limit=3)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(responder.run(unread_only=True))
            loop.close()
        except Exception as e:
            print(f"⚠️ [Auto-Pilot] Notice during InMail check: {e}")

    def run_single_cycle(self) -> Dict[str, Any]:
        """Runs one full scheduled application cycle with safety validations."""
        now = datetime.now()
        today_applied = self.tracker.get_today_application_count()

        cycle_record = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "platform": "",
            "applied": 0,
            "status": "completed",
            "message": ""
        }

        # 1. Business Hours Check
        if not self.is_within_business_hours():
            self.state = "OUTSIDE_HOURS"
            cycle_record["status"] = "skipped"
            cycle_record["message"] = "Outside permitted business hours (09:00 - 19:00). Pausing."
            print(f"🌙 [Auto-Pilot] {cycle_record['message']}")
            self.cycle_logs.append(cycle_record)
            return cycle_record

        # 2. Daily Limit Check
        remaining_today = self.daily_limit - today_applied
        if remaining_today <= 0:
            self.state = "DAILY_LIMIT_REACHED"
            cycle_record["status"] = "limit_reached"
            cycle_record["message"] = f"Daily safety limit reached ({today_applied}/{self.daily_limit}). Resting until tomorrow."
            print(f"🛑 [Auto-Pilot] {cycle_record['message']}")
            self.cycle_logs.append(cycle_record)
            return cycle_record

        # 3. Pick Next Platform in Round-Robin Order
        self.state = "RUNNING_CYCLE"
        target_platform = self.platforms[self.platform_index % len(self.platforms)]
        self.platform_index += 1
        self.current_platform = target_platform
        cycle_record["platform"] = target_platform

        allowed_limit = min(self.session_limit, remaining_today)

        # 4. Run Job Application Batch
        try:
            applied = self._execute_platform_batch(target_platform, allowed_limit)
            cycle_record["applied"] = applied
            cycle_record["message"] = f"Successfully processed {target_platform} batch."
        except Exception as e:
            cycle_record["status"] = "error"
            cycle_record["message"] = str(e)

        # 5. Optional InMail Check
        if self.inmail_check:
            self._execute_inmail_check()

        self.last_run_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.cycle_logs.append(cycle_record)
        return cycle_record

    def _worker_loop(self) -> None:
        """Background daemon loop controlling timer intervals and circadian sleep."""
        print(f"🚀 [Auto-Pilot Engine] Background loop started. Daily Limit: {self.daily_limit}")
        self.is_running = True

        while not self._stop_event.is_set():
            # Run one cycle
            self.run_single_cycle()

            if self._stop_event.is_set():
                break

            # Calculate next run with +/- 10% human jitter
            jitter_sec = random.randint(-180, 180)
            sleep_sec = max(60, (self.interval_minutes * 60) + jitter_sec)
            next_dt = datetime.now() + timedelta(seconds=sleep_sec)
            self.next_run_time = next_dt.strftime("%Y-%m-%d %H:%M:%S")
            self.state = "RESTING"

            print(f"⏳ [Auto-Pilot] Resting for {sleep_sec // 60}m. Next cycle scheduled at {self.next_run_time}")

            # Sleep in small slices to allow responsive stop() signals
            waited = 0
            while waited < sleep_sec and not self._stop_event.is_set():
                time.sleep(1.0)
                waited += 1

        self.is_running = False
        self.state = "STOPPED"
        print("🛑 [Auto-Pilot Engine] Background loop stopped cleanly.")

    def start(self, in_background: bool = True) -> bool:
        """Starts the Auto-Pilot engine."""
        if self.is_running:
            return False

        self._stop_event.clear()
        if in_background:
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            self.is_running = True
            return True
        else:
            self._worker_loop()
            return True

    def stop(self) -> bool:
        """Gracefully halts the Auto-Pilot engine."""
        if not self.is_running:
            return False
        print("🛑 [Auto-Pilot] Received stop signal...")
        self._stop_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=3.0)
        self.is_running = False
        self.state = "STOPPED"
        return True

# Global Auto-Pilot Singleton
autopilot = AutoPilotEngine()
