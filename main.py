#!/usr/bin/env python3
"""
Career Automator - Autonomous Job Application & Recruiter Outreach CLI.
Unified entrypoint for automated multi-platform applications, InMail replies, and status auditing.
"""
import sys
import asyncio
import argparse
import sqlite3
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from core.config_loader import get_config
from core.browser_engine import BrowserEngine
from core.tracker import ApplicationTracker
from platforms.linkedin.agent import LinkedInApplicationAgent
from platforms.naukri.connector import NaukriPlatform
from platforms.hirist.connector import HiristPlatform
from platforms.instahyre.connector import InstahyrePlatform
from platforms.indeed.connector import IndeedPlatform
from platforms.glassdoor.connector import GlassdoorPlatform
from platforms.wellfound.connector import WellfoundPlatform
from messaging.auto_responder import RecruiterAutoResponder

def handle_apply(args):
    """Executes the job application workflow on the selected platform."""
    platform = args.platform.lower() if args.platform else "linkedin"
    is_live = getattr(args, "live", False)
    dry_run = not is_live
    limit = args.limit
    interactive = getattr(args, "interactive", False)

    # Auto-detect platform from URL if provided
    if args.url:
        u = args.url.lower()
        if "naukri.com" in u:
            platform = "naukri"
        elif "linkedin.com" in u:
            platform = "linkedin"
        elif "hirist" in u:
            platform = "hirist"
        elif "instahyre" in u:
            platform = "instahyre"
        elif "wellfound" in u or "angel.co" in u:
            platform = "wellfound"
        elif "indeed" in u:
            platform = "indeed"
        elif "glassdoor" in u:
            platform = "glassdoor"

    print(f"\n{'='*60}")
    print(f"⚡ Target Platform: {platform.upper()}")
    print(f"🎯 Execution Mode: {'LIVE AUTO-SUBMIT' if not dry_run else 'DRY RUN (Preview)'}")
    print(f"💬 Interactive Q&A: {'ON (Will ask in terminal for new questions)' if interactive else 'OFF (Uses memory & AI)'}")
    print(f"📊 Application Limit: {limit}")
    print(f"{'='*60}\n")

    if args.url:
        print(f"🔗 Direct Job URL: {args.url}")
        if platform == "naukri":
            agent = NaukriPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
            asyncio.run(agent.apply_to_job_url(args.url))
            return
        elif platform == "linkedin":
            from core.models import JobPosting
            agent = LinkedInApplicationAgent(dry_run=dry_run, limit=limit, interactive=interactive)
            dummy_job = JobPosting(job_id=str(abs(hash(args.url)))[:10], title="Target Role", company="Target Company", location="India", url=args.url)
            asyncio.run(agent.apply_to_job(dummy_job))
            return
        elif platform == "hirist":
            from core.models import JobPosting
            agent = HiristPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
            dummy_job = JobPosting(job_id=str(abs(hash(args.url)))[:10], title="Target Role", company="Target Company", location="India", url=args.url)
            asyncio.run(agent.apply_to_job(dummy_job))
            return
        elif platform == "instahyre":
            from core.models import JobPosting
            agent = InstahyrePlatform(dry_run=dry_run, limit=limit, interactive=interactive)
            dummy_job = JobPosting(job_id=str(abs(hash(args.url)))[:10], title="Target Role", company="Target Company", location="India", url=args.url)
            asyncio.run(agent.apply_to_job(dummy_job))
            return
        elif platform == "wellfound":
            from core.models import JobPosting
            agent = WellfoundPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
            dummy_job = JobPosting(job_id=str(abs(hash(args.url)))[:10], title="Target Role", company="Target Company", location="India", url=args.url)
            asyncio.run(agent.apply_to_job(dummy_job))
            return

    def get_agent(p_name):
        if p_name == "naukri":
            return NaukriPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
        elif p_name == "linkedin":
            return LinkedInApplicationAgent(dry_run=dry_run, limit=limit, interactive=interactive)
        elif p_name == "hirist":
            return HiristPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
        elif p_name == "instahyre":
            return InstahyrePlatform(dry_run=dry_run, limit=limit, interactive=interactive)
        elif p_name == "indeed":
            return IndeedPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
        elif p_name == "glassdoor":
            return GlassdoorPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
        elif p_name == "wellfound":
            return WellfoundPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
        return None

    kw = [args.keyword] if args.keyword else None

    if platform == "all":
        platforms_to_run = ["naukri", "linkedin", "hirist", "instahyre", "wellfound", "indeed", "glassdoor"]
        for p in platforms_to_run:
            print(f"\n🚀 Starting Platform Batch: {p.upper()}")
            agent = get_agent(p)
            if agent:
                try:
                    asyncio.run(agent.run(keywords=kw, location=args.location))
                except Exception as e:
                    print(f"⚠️ Platform {p.upper()} finished with notice: {e}")
    else:
        agent = get_agent(platform)
        if agent:
            asyncio.run(agent.run(keywords=kw, location=args.location))
        else:
            print(f"❌ Unknown platform '{platform}'. Choose from: linkedin, naukri, hirist, instahyre, wellfound, indeed, glassdoor, all")

def handle_inmail(args):
    """Executes the Recruiter InMail Auto-Reply workflow."""
    is_send = args.send or args.live
    dry_run = not is_send
    limit = args.limit
    unread_only = not args.all

    responder = RecruiterAutoResponder(dry_run=dry_run, limit=limit)
    asyncio.run(responder.run(unread_only=unread_only))

def handle_status(args):
    """Displays tracking database statistics and recent applications."""
    config = get_config()
    db_path = config.database_path

    print(f"\n{'='*60}")
    print("📊 Career Automator - Application Status Dashboard")
    print(f"📁 Database: {db_path}")
    print(f"{'='*60}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT status, count(*) FROM applications GROUP BY status")
        rows = cursor.fetchall()
        print("\n📈 Applications Breakdown by Status:")
        for status, count in rows:
            icon = "✅" if status == "applied" else ("🎯" if status == "dry_run_completed" else ("⚠️" if status == "needs_review" else "⏭️"))
            print(f"  {icon} {status.replace('_', ' ').title():<20}: {count}")

        cursor.execute("""
            SELECT title, company, workplace_type, hiring_manager_name, status, created_at
            FROM applications
            WHERE status = 'applied'
            ORDER BY id DESC
            LIMIT 10
        """)
        recent = cursor.fetchall()
        if recent:
            print("\n🕒 Last 10 Submitted Applications:")
            for title, comp, wp, hirer, st, ts in recent:
                hirer_str = f" | Hirer: {hirer}" if hirer else ""
                print(f"  • {title[:32]} @ {comp[:22]} [{wp}]{hirer_str}")

        conn.close()
    except Exception as e:
        print(f"⚠️ Error reading status database: {e}")

    print("\n" + "="*60 + "\n")

def handle_studio(args):
    """Launches the CareerEngine Local Web Studio GUI server."""
    from core.studio import start_studio_server
    start_studio_server(host=args.host, port=args.port)

def main():
    parser = argparse.ArgumentParser(
        description="Career Automator - Autonomous Job Application & Recruiter Outreach CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply to 10 LinkedIn jobs in Live mode:
  python3 main.py apply --platform linkedin --live --limit 10

  # Preview application answers in Dry-Run mode:
  python3 main.py apply --platform linkedin --dry-run --limit 5

  # Launch the local Web Studio GUI:
  python3 main.py studio --port 8501

  # Preview AI-generated replies to unread recruiter InMails:
  python3 main.py inmail --preview

  # Auto-send replies to incoming recruiter InMails:
  python3 main.py inmail --send --limit 5

  # Check total application statistics:
  python3 main.py status
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: apply
    parser_apply = subparsers.add_parser("apply", help="Apply to jobs automatically on job boards")
    parser_apply.add_argument("--platform", type=str, default="linkedin", choices=["linkedin", "naukri", "hirist", "instahyre", "indeed", "glassdoor", "wellfound", "all"], help="Target job platform (default: linkedin)")
    parser_apply.add_argument("--live", action="store_true", help="Submit applications directly")
    parser_apply.add_argument("--dry-run", action="store_true", help="Preview without submitting")
    parser_apply.add_argument("--interactive", "-i", action="store_true", help="Prompt interactively in terminal for any unknown question and remember answers")
    parser_apply.add_argument("--limit", type=int, default=10, help="Maximum number of applications to process (default: 10)")
    parser_apply.add_argument("--keyword", type=str, default=None, help="Filter by specific job title keyword")
    parser_apply.add_argument("--location", type=str, default=None, help="Filter by specific location")
    parser_apply.add_argument("--url", type=str, default=None, help="Direct job posting URL to apply to immediately")

    # Command: inmail
    parser_inmail = subparsers.add_parser("inmail", help="Scan and auto-reply to LinkedIn InMails / recruiter inquiries")
    parser_inmail.add_argument("--preview", action="store_true", default=True, help="Generate and preview draft replies without sending (default)")
    parser_inmail.add_argument("--send", action="store_true", help="Send AI-crafted replies directly to recruiters")
    parser_inmail.add_argument("--live", action="store_true", help="Alias for --send")
    parser_inmail.add_argument("--limit", type=int, default=5, help="Number of message threads to process (default: 5)")
    parser_inmail.add_argument("--all", action="store_true", help="Scan all conversations (not just unread)")

    # Command: status
    subparsers.add_parser("status", help="View current application metrics and history")

    # Command: studio
    parser_studio = subparsers.add_parser("studio", help="Launch the local Web Studio dashboard GUI")
    parser_studio.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind to (default: 127.0.0.1)")
    parser_studio.add_argument("--port", type=int, default=8501, help="Port to listen on (default: 8501)")

    # Command: setup
    parser_setup = subparsers.add_parser("setup", help="Interactive onboarding agent to configure personal profile and API keys")
    parser_setup.add_argument("--defaults", action="store_true", help="Quick setup with default configuration placeholders")

    args = parser.parse_args()

    if args.command == "setup":
        from core.setup_agent import SetupAgent
        agent = SetupAgent()
        agent.run(defaults_only=args.defaults)
    elif args.command == "apply":
        handle_apply(args)
    elif args.command == "inmail":
        handle_inmail(args)
    elif args.command == "status":
        handle_status(args)
    elif args.command == "studio":
        handle_studio(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
