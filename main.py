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
from platforms.foundit.connector import FounditPlatform
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
        elif "foundit" in u or "monsterindia" in u:
            platform = "foundit"

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
        elif platform == "indeed":
            from core.models import JobPosting
            agent = IndeedPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
            dummy_job = JobPosting(job_id=str(abs(hash(args.url)))[:10], title="Target Role", company="Target Company", location="India", url=args.url)
            asyncio.run(agent.apply_to_job(dummy_job))
            return
        elif platform == "glassdoor":
            from core.models import JobPosting
            agent = GlassdoorPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
            dummy_job = JobPosting(job_id=str(abs(hash(args.url)))[:10], title="Target Role", company="Target Company", location="India", url=args.url)
            asyncio.run(agent.apply_to_job(dummy_job))
            return
        elif platform == "foundit":
            from core.models import JobPosting
            agent = FounditPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
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
        elif p_name == "foundit":
            return FounditPlatform(dry_run=dry_run, limit=limit, interactive=interactive)
        return None

    kw = [args.keyword] if args.keyword else None

    if platform == "all":
        platforms_to_run = ["naukri", "linkedin", "hirist", "instahyre", "wellfound", "indeed", "glassdoor", "foundit"]
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

def handle_score(args):
    """Audits and scores candidate profile completeness, market readiness, and ATS fit."""
    from core.profile_scorer import profile_scorer
    llm = getattr(args, "llm", False)
    if llm:
        print("\n⏳ Running comprehensive ATS evaluation with AI executive assessment...")
    report = profile_scorer.evaluate(include_llm_critique=llm)
    print(profile_scorer.format_cli_scorecard(report))

def handle_tailor(args):
    """Generates ATS resume keywords, quantified achievement bullets, and recruiter pitch for a job description."""
    from core.resume_tailor import resume_tailor
    jd_text = ""
    if getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                jd_text = f.read()
        except Exception as e:
            print(f"❌ Error reading JD file {args.file}: {e}")
            return
    elif getattr(args, "jd", None):
        jd_text = args.jd

    if getattr(args, "job_id", None):
        import sqlite3
        from core.config_loader import get_config
        conn = sqlite3.connect(get_config().database_path)
        c = conn.cursor()
        c.execute("SELECT title, company, job_description FROM applications WHERE job_id = ? LIMIT 1", (args.job_id,))
        row = c.fetchone()
        conn.close()
        if row:
            if not getattr(args, "title", None) and row[0]:
                args.title = row[0]
            if not getattr(args, "company", None) and row[1]:
                args.company = row[1]
            if not jd_text and row[2]:
                jd_text = row[2]

    if not jd_text and not getattr(args, "title", None):
        print("❌ Please provide a job description with --jd '...' or --file path/to/jd.txt or job title with --title '...'")
        return

    title = getattr(args, "title", None) or "Software Engineer"
    company = getattr(args, "company", None) or "Tech Company"
    role = getattr(args, "role", None)

    print(f"\n🎯 Tailoring Resume for: {title} @ {company}...")
    report = resume_tailor.tailor_for_job(
        job_title=title,
        company=company,
        job_description=jd_text,
        target_role=role
    )
    print(resume_tailor.format_cli_report(report))

def handle_export(args):
    """Exports application history and status from jobs.db to CSV, JSON, or Markdown."""
    from core.analytics_exporter import analytics_exporter
    fmt = args.format.lower()
    out_path = args.output
    if fmt == "csv":
        res = analytics_exporter.export_to_csv(out_path)
    elif fmt == "json":
        res = analytics_exporter.export_to_json(out_path)
    elif fmt in ("markdown", "md"):
        res = analytics_exporter.export_to_markdown(out_path)
    else:
        print(f"❌ Unsupported format: {fmt}. Use csv, json, or markdown.")
        return
    print(f"✅ Exported {res.get('total_exported', 0)} application records to {res.get('file_path')}")

def handle_analytics(args):
    """Displays comprehensive pipeline analytics, velocity, and conversion metrics."""
    from core.analytics_exporter import analytics_exporter
    print(analytics_exporter.format_cli_summary())

def handle_outreach(args):
    """Synthesizes cold email frameworks, recruiter discovery queries, and mailto links."""
    from core.cold_outreach import cold_outreach_synthesizer
    company = getattr(args, "company", None)
    title = getattr(args, "title", None) or "Senior Software Engineer"
    target_name = getattr(args, "name", None)

    if getattr(args, "job_id", None):
        import sqlite3
        from core.config_loader import get_config
        conn = sqlite3.connect(get_config().database_path)
        c = conn.cursor()
        c.execute("SELECT title, company, hiring_manager_name FROM applications WHERE job_id = ? LIMIT 1", (args.job_id,))
        row = c.fetchone()
        conn.close()
        if row:
            title = title or row[0]
            company = company or row[1]
            target_name = target_name or row[2]

    if not company:
        print("❌ Please specify a company name with --company 'CompanyName' or provide a --job-id.")
        return

    kit = cold_outreach_synthesizer.generate_outreach_kit(
        company=company,
        job_title=title,
        target_name=target_name
    )
    print(cold_outreach_synthesizer.format_cli_outreach(kit))

def handle_prep(args):
    """Generates tailored System Design challenges, technical drills, and STAR stories for interview prep."""
    from core.interview_prep import interview_prep_simulator
    company = getattr(args, "company", None)
    title = getattr(args, "title", None) or "Senior Software Engineer"
    jd_text = ""

    if getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                jd_text = f.read()
        except Exception as e:
            print(f"❌ Error reading JD file {args.file}: {e}")
            return
    elif getattr(args, "jd", None):
        jd_text = args.jd

    if getattr(args, "job_id", None):
        import sqlite3
        from core.config_loader import get_config
        conn = sqlite3.connect(get_config().database_path)
        c = conn.cursor()
        c.execute("SELECT title, company, job_description FROM applications WHERE job_id = ? LIMIT 1", (args.job_id,))
        row = c.fetchone()
        conn.close()
        if row:
            title = title or row[0]
            company = company or row[1]
            if not jd_text and row[2]:
                jd_text = row[2]

    if not company:
        print("❌ Please specify a company name with --company 'CompanyName' or provide a --job-id.")
        return

    print(f"\n⏳ Synthesizing Interview Preparation Kit for {title} @ {company}...")
    kit = interview_prep_simulator.generate_prep_kit(
        job_title=title,
        company=company,
        job_description=jd_text
    )
    print(interview_prep_simulator.format_cli_prep(kit))

def handle_dedup_audit(args):
    """Audits local jobs.db database for potential cross-platform duplicate applications."""
    from core.smart_dedup import smart_deduplicator
    from core.config_loader import get_config
    db_path = get_config().database_path

    print(f"\n{'='*68}")
    print("  🔍 CAREERENGINE CROSS-PLATFORM DUPLICATE AUDIT")
    print(f"  Database: {db_path}")
    print(f"{'='*68}\n")

    dups = smart_deduplicator.audit_database_duplicates(db_path)
    if not dups:
        print("  ✅ Zero duplicate job postings detected! Database is clean.")
    else:
        print(f"  ⚠️ Detected {len(dups)} potential cross-platform duplicate groups:\n")
        for idx, d in enumerate(dups, 1):
            p = d["primary"]
            print(f"  {idx}. Primary: '{p['title']}' @ {p['company']} [{p.get('platform', '').upper()}] ({p['status']})")
            for m in d["matches"]:
                print(f"     ↳ Duplicate: '{m['title']}' @ {m['company']} [{m.get('platform', '').upper()}] ({m['status']})")
            print()
    print(f"{'='*68}\n")

def handle_cover_letter(args):
    """Generates an ATS-optimized, customized Cover Letter or Executive Memo."""
    from core.cover_letter import CoverLetterGenerator
    from core.config_loader import get_config
    import sqlite3

    company = args.company
    title = args.title or "Senior Engineer"
    jd_text = args.jd

    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            jd_text = f.read()

    if args.job_id:
        db_path = get_config().database_path
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT title, company, job_description FROM applications WHERE job_id = ? LIMIT 1", (args.job_id,))
        row = c.fetchone()
        conn.close()
        if row:
            title = title or row[0]
            company = company or row[1]
            if not jd_text and row[2]:
                jd_text = row[2]

    if not company:
        print("❌ Please specify a company name with --company 'CompanyName' or provide a --job-id.")
        return

    generator = CoverLetterGenerator()
    print(f"\n⏳ Synthesizing {args.style.upper()} Cover Letter for {title} @ {company}...")
    kit = generator.generate(
        company=company,
        title=title,
        job_description=jd_text,
        style=args.style,
        hiring_manager_name=args.manager
    )

    print("\n" + "="*68)
    print(f"  📄 COVER LETTER: {kit.target_title} @ {kit.target_company} ({kit.style.upper()})")
    print(f"  Matched Skills: {', '.join(kit.target_skills_matched)}")
    print("="*68 + "\n")
    print(kit.full_text)
    print("="*68)

    save_path = generator.save_to_file(kit, output_dir=args.output)
    print(f"  💾 Saved clean Markdown version to: {save_path}\n")

def handle_negotiate(args):
    """Generates compensation market benchmarks and negotiation battlecards."""
    from core.salary_negotiator import SalaryNegotiator

    negotiator = SalaryNegotiator()
    company = args.company or "Target Company"
    title = args.title or "Senior Engineer"

    print(f"\n⏳ Analyzing compensation & formulating negotiation playbook for {title} @ {company}...")
    report = negotiator.analyze_and_plan(
        company=company,
        title=title,
        offered_comp=args.offered,
        current_comp=args.current,
        market_region=args.region,
        competing_offer=args.competing
    )

    print("\n" + "="*68)
    print(f"  💰 COMPENSATION COPILOT: {report.target_title} @ {report.target_company}")
    print(f"  Seniority Bracket: {report.seniority_level} | Market: {args.region.upper()}")
    print("="*68)
    print(f"  Current Compensation:   {report.current_compensation}")
    print(f"  Initial Offered:        {report.offered_compensation}")
    print(f"  Recommended Anchor:     {report.target_recommendation}")
    print(f"  Market Distribution:    P25: {report.market_percentiles.get('p25')} | P50: {report.market_percentiles.get('p50')} | P75: {report.market_percentiles.get('p75')} | P90: {report.market_percentiles.get('p90')} ({report.currency})")
    print("="*68 + "\n")

    for idx, strat in enumerate(report.strategies, 1):
        print(f"  🎯 SCENARIO {idx}: {strat.scenario_title.upper()}")
        print(f"  Target Anchor: {strat.recommended_target}")
        print(f"  Rationale: {strat.rationale}\n")
        print("  📧 Ready-to-Send Email Script:")
        print(f"  Subject: {strat.email_subject}")
        for line in strat.email_body.splitlines():
            print(f"    {line}")
        print("\n  📞 Phone Call Talking Points:")
        for tp in strat.phone_talking_points:
            print(f"    • {tp}")
        print("\n" + "-"*68 + "\n")

def handle_stealth_audit(args):
    """Executes a diagnostic bot-detection and stealth safety audit."""
    from core.stealth_auditor import StealthAuditor

    auditor = StealthAuditor()
    print("\n⏳ Running CareerEngine Stealth & Bot-Detection Safety Audit...")
    report = auditor.run_audit()

    print("\n" + "="*68)
    print("  🛡️  CAREERENGINE STEALTH & BOT-DETECTION SAFETY AUDIT")
    print(f"  Safety Score: {report.safety_score}/100 [{report.risk_level}]")
    print(f"  Summary:      {report.summary}")
    print(f"  Velocity:     {report.daily_applications_today}/{report.daily_limit} applications sent today")
    print("="*68 + "\n")

    for c in report.checks:
        icon = "✅" if c.status == "PASS" else "⚠️" if c.status == "WARN" else "❌"
        print(f"  {icon} [{c.status}] {c.name} ({c.score_points}/{c.max_points} pts)")
        print(f"     ↳ {c.finding}")
        if c.remediation:
            print(f"     💡 Fix: {c.remediation}")
        print()

    print("="*68 + "\n")

def handle_studio(args):
    """Launches the CareerEngine Local Web Studio GUI server."""
    from core.studio import start_studio_server
    start_studio_server(host=args.host, port=args.port)

def handle_auto(args):
    """Launches the CareerEngine Autonomous Auto-Pilot runner."""
    from core.autopilot import AutoPilotEngine
    is_live = getattr(args, "live", False)
    dry_run = not is_live

    engine = AutoPilotEngine(
        interval_minutes=args.interval,
        daily_limit=args.daily_limit,
        session_limit=args.session_limit,
        business_hours_only=not args.all_hours,
        inmail_check=not args.no_inmail,
        dry_run=dry_run
    )

    print("\n" + "="*60)
    print("🤖 CareerEngine Autonomous Auto-Pilot")
    print(f"🎯 Execution Mode: {'LIVE AUTO-SUBMIT' if not dry_run else 'DRY RUN (Preview)'}")
    print(f"📊 Daily Safety Limit: {args.daily_limit} applications / day")
    print(f"⏱️ Cycle Interval: Every {args.interval} minutes")
    print(f"🕒 Schedule: {'24/7 Unrestricted' if args.all_hours else '09:00 - 19:00 Business Hours Only'}")
    print(f"📬 Recruiter InMail Check: {'ON' if not args.no_inmail else 'OFF'}")
    print("⚡ Press Ctrl+C in terminal to stop Auto-Pilot.")
    print("="*60 + "\n")

    try:
        engine.start(in_background=False)
    except KeyboardInterrupt:
        engine.stop()
        print("\n✓ Auto-Pilot stopped cleanly by user.")

def main():
    parser = argparse.ArgumentParser(
        description="Career Automator - Autonomous Job Application & Recruiter Outreach CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch Autonomous Auto-Pilot in preview mode:
  python3 main.py auto --interval 180 --daily-limit 20 --dry-run

  # Launch Auto-Pilot in live auto-submit mode:
  python3 main.py auto --interval 120 --daily-limit 15 --live

  # Apply to 10 LinkedIn jobs in Live mode:
  python3 main.py apply --platform linkedin --live --limit 10

  # Tailor resume for a job posting:
  python3 main.py tailor --title "Backend Engineer" --company "Acme" --file jd.txt

  # Export job applications to CSV:
  python3 main.py export --format csv

  # View application analytics and conversion funnel:
  python3 main.py analytics

  # Launch the local Web Studio GUI:
  python3 main.py studio --port 8501
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: apply
    parser_apply = subparsers.add_parser("apply", help="Apply to jobs automatically on job boards")
    parser_apply.add_argument("--platform", type=str, default="linkedin", choices=["linkedin", "naukri", "hirist", "instahyre", "indeed", "glassdoor", "wellfound", "foundit", "all"], help="Target job platform (default: linkedin)")
    parser_apply.add_argument("--live", action="store_true", help="Submit applications directly")
    parser_apply.add_argument("--dry-run", action="store_true", help="Preview without submitting")
    parser_apply.add_argument("--interactive", "-i", action="store_true", help="Prompt interactively in terminal for any unknown question and remember answers")
    parser_apply.add_argument("--limit", type=int, default=10, help="Maximum number of applications to process (default: 10)")
    parser_apply.add_argument("--keyword", type=str, default=None, help="Filter by specific job title keyword")
    parser_apply.add_argument("--location", type=str, default=None, help="Filter by specific location")
    parser_apply.add_argument("--url", type=str, default=None, help="Direct job posting URL to apply to immediately")

    # Command: tailor (ATS Resume Tailoring)
    parser_tailor = subparsers.add_parser("tailor", help="Synthesize JD keyword matches, XYZ achievement bullets, and recruiter pitch")
    parser_tailor.add_argument("--jd", type=str, default=None, help="Job description text")
    parser_tailor.add_argument("--file", type=str, default=None, help="Path to file containing Job Description")
    parser_tailor.add_argument("--job-id", type=str, default=None, help="Fetch job description from tracked jobs database")
    parser_tailor.add_argument("--title", type=str, default=None, help="Job role title (e.g., 'Senior Backend Engineer')")
    parser_tailor.add_argument("--company", type=str, default=None, help="Hiring company name")
    parser_tailor.add_argument("--role", type=str, default=None, help="Target profile role key (e.g., backend, fullstack, devops)")

    # Command: export
    parser_export = subparsers.add_parser("export", help="Export application tracking history to CSV, JSON, or Markdown")
    parser_export.add_argument("--format", type=str, default="csv", choices=["csv", "json", "markdown", "md"], help="Export format (default: csv)")
    parser_export.add_argument("--output", "-o", type=str, default=None, help="Custom output file path")

    # Command: analytics
    subparsers.add_parser("analytics", help="Display conversion rates, velocity, and platform breakdown")

    # Command: auto (Autonomous Auto-Pilot)
    parser_auto = subparsers.add_parser("auto", help="Launch autonomous background auto-pilot mode with circadian pacing")
    parser_auto.add_argument("--interval", type=int, default=180, help="Interval between cycles in minutes (default: 180)")
    parser_auto.add_argument("--daily-limit", type=int, default=20, help="Maximum applications per calendar day (default: 20)")
    parser_auto.add_argument("--session-limit", type=int, default=5, help="Maximum applications per batch cycle (default: 5)")
    parser_auto.add_argument("--live", action="store_true", help="Run in live auto-submit mode")
    parser_auto.add_argument("--dry-run", action="store_true", help="Run in preview mode (default)")
    parser_auto.add_argument("--all-hours", action="store_true", help="Disable business hours restriction (run 24/7)")
    parser_auto.add_argument("--no-inmail", action="store_true", help="Skip recruiter InMail auto-scanning")

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

    # Command: outreach (Recruiter Cold Outreach & Discovery)
    parser_outreach = subparsers.add_parser("outreach", help="Synthesize personalized cold outreach emails, Boolean search links, and mailto client launch")
    parser_outreach.add_argument("--company", type=str, default=None, help="Target company name (e.g. Stripe, Databricks)")
    parser_outreach.add_argument("--title", type=str, default=None, help="Job title / target role")
    parser_outreach.add_argument("--name", type=str, default=None, help="Recruiter or hiring manager name (optional)")
    parser_outreach.add_argument("--job-id", type=str, default=None, help="Target application job ID from jobs.db")

    # Command: prep (Technical Interview Prep & STAR Simulator)
    parser_prep = subparsers.add_parser("prep", help="Simulate domain-specific system design challenges, technical questions, and STAR stories")
    parser_prep.add_argument("--company", type=str, default=None, help="Target company name (e.g. Stripe, Databricks)")
    parser_prep.add_argument("--title", type=str, default=None, help="Target role title")
    parser_prep.add_argument("--jd", type=str, default=None, help="Pasted job description text")
    parser_prep.add_argument("--file", type=str, default=None, help="Path to job description text file")
    parser_prep.add_argument("--job-id", type=str, default=None, help="Target application job ID from jobs.db")

    # Command: dedup-audit (Cross-Platform Duplicate Detection)
    subparsers.add_parser("dedup-audit", help="Audit jobs.db for potential cross-platform duplicate applications across platforms")

    # Command: score (or audit)
    parser_score = subparsers.add_parser("score", help="Audit and score candidate profile completeness and ATS readiness")
    parser_score.add_argument("--llm", action="store_true", help="Include AI executive critique from connected LLM")

    parser_audit = subparsers.add_parser("audit", help="Alias for score command")
    parser_audit.add_argument("--llm", action="store_true", help="Include AI executive critique from connected LLM")

    # Command: cover-letter (AI Cover Letter & Executive Memo Generator)
    parser_cover = subparsers.add_parser("cover-letter", help="Generate customized, high-converting cover letters and executive memos")
    parser_cover.add_argument("--company", type=str, default=None, help="Target company name")
    parser_cover.add_argument("--title", type=str, default=None, help="Target role title")
    parser_cover.add_argument("--jd", type=str, default=None, help="Pasted job description text")
    parser_cover.add_argument("--file", type=str, default=None, help="Path to job description text file")
    parser_cover.add_argument("--job-id", type=str, default=None, help="Target application job ID from jobs.db")
    parser_cover.add_argument("--style", type=str, default="startup", choices=["startup", "enterprise", "concise"], help="Tone style: startup (default), enterprise, or concise")
    parser_cover.add_argument("--manager", type=str, default=None, help="Hiring manager or team lead name")
    parser_cover.add_argument("--output", "-o", type=str, default=None, help="Custom directory to save generated markdown file")

    # Command: negotiate (Salary & Offer Negotiation Copilot)
    parser_negotiate = subparsers.add_parser("negotiate", help="Compensation benchmarks, percentile distributions, and negotiation counter-offer playbooks")
    parser_negotiate.add_argument("--company", type=str, default=None, help="Hiring company name extending offer")
    parser_negotiate.add_argument("--title", type=str, default=None, help="Target position title")
    parser_negotiate.add_argument("--offered", type=float, default=None, help="Offered compensation number (e.g. 35 for 35 LPA or 180 for $180k)")
    parser_negotiate.add_argument("--current", type=float, default=None, help="Current compensation number")
    parser_negotiate.add_argument("--region", type=str, default="india_inr_lpa", choices=["india_inr_lpa", "us_remote_usd_k", "eu_remote_eur_k"], help="Market compensation benchmark region (default: india_inr_lpa)")
    parser_negotiate.add_argument("--competing", type=str, default=None, help="Details or context of any competing offer (e.g., 'another offer at 42 LPA')")

    # Command: audit-stealth (Safety & Bot Evasion Diagnostic Health Check)
    subparsers.add_parser("audit-stealth", help="Run anti-detection, browser fingerprint, and circadian safety health checks")

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
    elif args.command == "tailor":
        handle_tailor(args)
    elif args.command == "export":
        handle_export(args)
    elif args.command == "analytics":
        handle_analytics(args)
    elif args.command == "outreach":
        handle_outreach(args)
    elif args.command == "prep":
        handle_prep(args)
    elif args.command == "dedup-audit":
        handle_dedup_audit(args)
    elif args.command == "cover-letter":
        handle_cover_letter(args)
    elif args.command == "negotiate":
        handle_negotiate(args)
    elif args.command == "audit-stealth":
        handle_stealth_audit(args)
    elif args.command == "auto":
        handle_auto(args)
    elif args.command == "inmail":
        handle_inmail(args)
    elif args.command == "status":
        handle_status(args)
    elif args.command == "studio":
        handle_studio(args)
    elif args.command in ("score", "audit"):
        handle_score(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
