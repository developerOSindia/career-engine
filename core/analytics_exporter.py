"""
CareerEngine Application Analytics & Multi-Format Exporter.
Computes deep pipeline metrics (conversion rate, platform distribution, top companies)
and exports application records to CSV, JSON, and Markdown formats.
"""

import os
import csv
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from core.config_loader import get_config

ROOT_DIR = Path(__file__).resolve().parent.parent

class AnalyticsExporter:
    """Computes pipeline intelligence and exports tracking data."""

    def __init__(self, db_path: Optional[str] = None):
        config = get_config()
        self.db_path = db_path or config.database_path

    def get_all_applications(self) -> List[Dict[str, Any]]:
        """Queries all application records from SQLite jobs.db."""
        if not os.path.exists(self.db_path):
            return []
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, job_id, title, company, location, platform,
                       workplace_type, hiring_manager_name, hiring_manager_url,
                       key_skills, job_url, status, notes, screenshot_path, created_at
                FROM applications
                ORDER BY id DESC
            """)
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            print(f"⚠️ Error reading SQLite DB: {e}")
            return []

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Calculates conversion rates, platform counts, and velocity metrics."""
        records = self.get_all_applications()
        total = len(records)

        status_counts: Dict[str, int] = {}
        platform_counts: Dict[str, int] = {}
        workplace_counts: Dict[str, int] = {}
        company_counts: Dict[str, int] = {}
        daily_counts: Dict[str, int] = {}
        screenshots_count = 0

        for r in records:
            # Status
            st = r.get("status") or "unknown"
            status_counts[st] = status_counts.get(st, 0) + 1

            # Platform
            plat = (r.get("platform") or "linkedin").lower()
            platform_counts[plat] = platform_counts.get(plat, 0) + 1

            # Workplace
            wp = r.get("workplace_type") or "Not Specified"
            workplace_counts[wp] = workplace_counts.get(wp, 0) + 1

            # Company
            comp = r.get("company") or "Unknown"
            company_counts[comp] = company_counts.get(comp, 0) + 1

            # Screenshot
            if r.get("screenshot_path") and os.path.exists(r.get("screenshot_path")):
                screenshots_count += 1

            # Daily timeline
            created = r.get("created_at") or ""
            day = created[:10] if len(created) >= 10 else "Unknown"
            if day != "Unknown":
                daily_counts[day] = daily_counts.get(day, 0) + 1

        applied_count = status_counts.get("applied", 0)
        dry_run_count = status_counts.get("dry_run_completed", 0)
        success_applications = applied_count + dry_run_count
        conversion_rate = round((success_applications / max(1, total)) * 100, 1)

        # Top 10 companies
        sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_companies = [{"company": c, "count": cnt} for c, cnt in sorted_companies]

        return {
            "total_applications": total,
            "applied_count": applied_count,
            "dry_run_count": dry_run_count,
            "conversion_rate_percent": conversion_rate,
            "status_breakdown": status_counts,
            "platform_breakdown": platform_counts,
            "workplace_breakdown": workplace_counts,
            "top_companies": top_companies,
            "screenshots_stored": screenshots_count,
            "daily_velocity": dict(sorted(daily_counts.items(), reverse=True)[:7])
        }

    def export_csv(self, output_path: Optional[str] = None) -> str:
        """Exports all applications to a standardized CSV file."""
        records = self.get_all_applications()
        target_path = output_path or str(ROOT_DIR / "applications_export.csv")

        fieldnames = [
            "id", "job_id", "title", "company", "location", "platform",
            "workplace_type", "hiring_manager_name", "status", "job_url",
            "notes", "screenshot_path", "created_at"
        ]

        with open(target_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in records:
                writer.writerow(r)

        return target_path

    def export_to_csv(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        path = self.export_csv(output_path)
        records = self.get_all_applications()
        return {"file_path": path, "total_exported": len(records)}

    def export_json(self, output_path: Optional[str] = None) -> str:
        """Exports all applications to an indented JSON file."""
        records = self.get_all_applications()
        target_path = output_path or str(ROOT_DIR / "applications_export.json")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

        return target_path

    def export_to_json(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        path = self.export_json(output_path)
        records = self.get_all_applications()
        return {"file_path": path, "total_exported": len(records)}

    def export_markdown(self, output_path: Optional[str] = None) -> str:
        """Generates an executive Markdown audit report."""
        summary = self.get_analytics_summary()
        records = self.get_all_applications()
        target_path = output_path or str(ROOT_DIR / "applications_report.md")

        lines = []
        lines.append("# 📊 CareerEngine Job Applications Pipeline Report")
        lines.append(f"Generated on: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n")

        lines.append("## 📈 Pipeline Summary")
        lines.append(f"- **Total Tracked Opportunities**: {summary['total_applications']}")
        lines.append(f"- **Live Applied**: {summary['applied_count']}")
        lines.append(f"- **Dry-Run Previews**: {summary['dry_run_count']}")
        lines.append(f"- **Successful Pipeline Conversion Rate**: {summary['conversion_rate_percent']}%")
        lines.append(f"- **Verified Screenshots Captured**: {summary['screenshots_stored']}\n")

        lines.append("## 🌐 Applications by Platform")
        lines.append("| Platform | Applications | Share |")
        lines.append("|---|---|---|")
        for plat, cnt in sorted(summary['platform_breakdown'].items(), key=lambda x: x[1], reverse=True):
            pct = round((cnt / max(1, summary['total_applications'])) * 100, 1)
            lines.append(f"| **{plat.upper()}** | {cnt} | {pct}% |")

        lines.append("\n## 🏢 Top Targeted Companies")
        lines.append("| Company | Applications Count |")
        lines.append("|---|---|")
        for tc in summary['top_companies']:
            lines.append(f"| {tc['company']} | {tc['count']} |")

        lines.append("\n## 📋 Recent Applications (Last 20)")
        lines.append("| ID | Role | Company | Platform | Status | Date |")
        lines.append("|---|---|---|---|---|---|")
        for r in records[:20]:
            lines.append(f"| {r.get('id')} | {r.get('title')[:30]} | {r.get('company')[:20]} | {r.get('platform', '').upper()} | `{r.get('status')}` | {r.get('created_at', '')[:10]} |")

        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return target_path

    def export_to_markdown(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        path = self.export_markdown(output_path)
        records = self.get_all_applications()
        return {"file_path": path, "total_exported": len(records)}

    def format_cli_summary(self) -> str:
        """Helper to get summary and format it as CLI text."""
        summary = self.get_analytics_summary()
        return self.format_cli_analytics(summary)

    def format_cli_analytics(self, summary: Dict[str, Any]) -> str:
        """Renders rich terminal report for the CLI."""
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        RESET = "\033[0m"

        lines = []
        lines.append(f"\n{BOLD}{'='*68}{RESET}")
        lines.append(f"{CYAN}{BOLD}  📊 CAREERENGINE PIPELINE ANALYTICS & INSIGHTS{RESET}")
        lines.append(f"{BOLD}{'='*68}{RESET}\n")

        lines.append(f"  {BOLD}Total Applications Tracked:{RESET}  {GREEN}{BOLD}{summary['total_applications']}{RESET}")
        lines.append(f"  {BOLD}Pipeline Conversion Rate:{RESET}    {CYAN}{BOLD}{summary['conversion_rate_percent']}%{RESET} (Live applied + verified preview)\n")

        # Status breakdown
        lines.append(f"  {BOLD}Status Breakdown:{RESET}")
        for st, count in summary['status_breakdown'].items():
            icon = "✅" if st == "applied" else ("🎯" if st == "dry_run_completed" else "⏭️")
            lines.append(f"    {icon} {st:<22}: {BOLD}{count}{RESET}")

        # Platform breakdown
        lines.append(f"\n  {BOLD}Platform Distribution:{RESET}")
        for plat, count in summary['platform_breakdown'].items():
            bar_len = int((count / max(1, summary['total_applications'])) * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"    • {plat.upper():<14} {CYAN}{bar}{RESET} {count:>3} apps")

        # Top Companies
        if summary['top_companies']:
            lines.append(f"\n  {BOLD}Top Targeted Companies:{RESET}")
            for tc in summary['top_companies'][:5]:
                lines.append(f"    🏢 {tc['company']:<26}: {tc['count']} applications")

        lines.append(f"\n{BOLD}{'='*68}{RESET}\n")
        return "\n".join(lines)

analytics_exporter = AnalyticsExporter()
