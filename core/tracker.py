"""
Job application tracking with SQLite, CSV, and JSON storage.
Maintains relational database (jobs.db), CSV spreadsheet (applied_jobs.csv),
and JSON cache for full transparency and multi-platform deduplication.
"""
import csv
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from core.config_loader import get_config

class ApplicationTracker:
    def __init__(
        self,
        history_file_path: Optional[str] = None,
        db_path: Optional[str] = None,
        csv_path: Optional[str] = None
    ):
        config = get_config()
        self.history_file_path = history_file_path or str(config.root_dir / "applied_jobs.json")
        self.db_path = db_path or config.database_path
        self.csv_path = csv_path or config.csv_path
        self.applied_cache: Dict[str, dict] = {}
        
        self._init_sqlite()
        self._load_json()
        self._sync_existing_to_sqlite_and_csv()

    def _init_sqlite(self):
        """Initializes SQLite database and tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    platform TEXT DEFAULT 'linkedin',
                    workplace_type TEXT,
                    hiring_manager_name TEXT,
                    hiring_manager_url TEXT,
                    key_skills TEXT,
                    job_url TEXT,
                    job_description TEXT,
                    status TEXT,
                    notes TEXT,
                    answers_filled TEXT,
                    screenshot_path TEXT,
                    created_at TEXT
                )
            """)
            # Ensure platform column exists in case table was created previously
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN platform TEXT DEFAULT 'linkedin'")
            except Exception:
                pass
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize SQLite DB ({e})")

    def _load_json(self):
        if os.path.exists(self.history_file_path):
            try:
                with open(self.history_file_path, "r", encoding="utf-8") as f:
                    self.applied_cache = json.load(f)
            except Exception as e:
                print(f"⚠️ Warning: Could not read {self.history_file_path} ({e}). Starting with empty history.")
                self.applied_cache = {}
        else:
            self.applied_cache = {}

    def _save_json(self):
        try:
            with open(self.history_file_path, "w", encoding="utf-8") as f:
                json.dump(self.applied_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Warning: Could not save {self.history_file_path} ({e})")

    def _save_sqlite(self, data: dict):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO applications (
                    job_id, title, company, location, platform, workplace_type,
                    hiring_manager_name, hiring_manager_url, key_skills,
                    job_url, job_description, status, notes,
                    answers_filled, screenshot_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    title=excluded.title,
                    company=excluded.company,
                    location=excluded.location,
                    platform=coalesce(nullif(excluded.platform, ''), applications.platform),
                    workplace_type=coalesce(nullif(excluded.workplace_type, ''), applications.workplace_type),
                    hiring_manager_name=coalesce(nullif(excluded.hiring_manager_name, ''), applications.hiring_manager_name),
                    hiring_manager_url=coalesce(nullif(excluded.hiring_manager_url, ''), applications.hiring_manager_url),
                    key_skills=coalesce(nullif(excluded.key_skills, ''), applications.key_skills),
                    job_url=excluded.job_url,
                    job_description=coalesce(nullif(excluded.job_description, ''), applications.job_description),
                    status=excluded.status,
                    notes=excluded.notes,
                    answers_filled=excluded.answers_filled,
                    screenshot_path=excluded.screenshot_path,
                    created_at=excluded.created_at
            """, (
                data.get("job_id"),
                data.get("title"),
                data.get("company"),
                data.get("location"),
                data.get("platform", "linkedin"),
                data.get("workplace_type", ""),
                data.get("hiring_manager_name", ""),
                data.get("hiring_manager_url", ""),
                data.get("key_skills", ""),
                data.get("job_url"),
                data.get("job_description", ""),
                data.get("status"),
                data.get("notes", ""),
                json.dumps(data.get("answers_filled", {}), ensure_ascii=False) if isinstance(data.get("answers_filled"), dict) else data.get("answers_filled", "{}"),
                data.get("screenshot", "") or data.get("screenshot_path", ""),
                data.get("timestamp") or data.get("created_at") or datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Warning: Could not save to SQLite DB ({e})")

    def _export_csv(self):
        """Exports all applications to CSV."""
        fieldnames = [
            "Job ID",
            "Title",
            "Company",
            "Platform",
            "Location",
            "Workplace Type",
            "Hiring Manager",
            "Hiring Manager Link",
            "Key Skills",
            "Status",
            "Applied At",
            "Job URL",
            "Screenshot"
        ]
        try:
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for entry in self.applied_cache.values():
                    writer.writerow({
                        "Job ID": entry.get("job_id", ""),
                        "Title": entry.get("title", ""),
                        "Company": entry.get("company", ""),
                        "Platform": entry.get("platform", "linkedin"),
                        "Location": entry.get("location", ""),
                        "Workplace Type": entry.get("workplace_type", ""),
                        "Hiring Manager": entry.get("hiring_manager_name", ""),
                        "Hiring Manager Link": entry.get("hiring_manager_url", ""),
                        "Key Skills": entry.get("key_skills", ""),
                        "Status": entry.get("status", ""),
                        "Applied At": entry.get("timestamp") or entry.get("created_at", ""),
                        "Job URL": entry.get("job_url", ""),
                        "Screenshot": entry.get("screenshot") or entry.get("screenshot_path", "")
                    })
        except Exception as e:
            print(f"⚠️ Warning: Could not export CSV ({e})")

    def _sync_existing_to_sqlite_and_csv(self):
        """Backfills existing cached JSON records into SQLite and CSV on launch."""
        for entry in self.applied_cache.values():
            self._save_sqlite(entry)
        self._export_csv()

    def is_already_applied(self, job_id: str, job_title: str = "", company: str = "") -> bool:
        if str(job_id) in self.applied_cache:
            status = self.applied_cache[str(job_id)].get("status")
            if status in ("applied", "dry_run_completed"):
                return True
        key = f"{job_title.strip().lower()}@@@{company.strip().lower()}"
        for entry in self.applied_cache.values():
            entry_key = f"{entry.get('title', '').strip().lower()}@@@{entry.get('company', '').strip().lower()}"
            if key == entry_key and entry.get("status") in ("applied", "dry_run_completed"):
                return True
        return False

    def record_application(
        self,
        job_id: str,
        title: str,
        company: str,
        location: str,
        job_url: str,
        platform: str = "linkedin",
        workplace_type: str = "",
        hiring_manager_name: str = "",
        hiring_manager_url: str = "",
        key_skills: str = "",
        job_description: str = "",
        status: str = "applied",
        notes: str = "",
        answers_filled: Optional[dict] = None,
        screenshot: Optional[str] = None
    ):
        data = {
            "job_id": str(job_id),
            "title": title,
            "company": company,
            "location": location,
            "platform": platform,
            "workplace_type": workplace_type,
            "hiring_manager_name": hiring_manager_name,
            "hiring_manager_url": hiring_manager_url,
            "key_skills": key_skills,
            "job_description": job_description,
            "job_url": job_url,
            "status": status,
            "notes": notes,
            "answers_filled": answers_filled or {},
            "screenshot": screenshot or "",
            "timestamp": datetime.now().isoformat()
        }
        self.applied_cache[str(job_id)] = data
        self._save_json()
        self._save_sqlite(data)
        self._export_csv()

    def get_summary(self) -> dict:
        total = len(self.applied_cache)
        applied = sum(1 for v in self.applied_cache.values() if v.get("status") == "applied")
        dry_run = sum(1 for v in self.applied_cache.values() if v.get("status") == "dry_run_completed")
        skipped = sum(1 for v in self.applied_cache.values() if v.get("status") == "skipped")
        failed = sum(1 for v in self.applied_cache.values() if v.get("status") in ("failed", "needs_review"))
        needs_review = sum(1 for v in self.applied_cache.values() if v.get("status") == "needs_review")
        return {
            "total_records": total,
            "applied": applied,
            "dry_run": dry_run,
            "skipped": skipped,
            "failed": failed,
            "needs_review": needs_review
        }

    def get_today_application_count(self) -> int:
        """Returns the total number of applications processed today (applied or dry_run_completed)."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        count = 0
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count(*) FROM applications WHERE status IN ('applied', 'dry_run_completed') AND created_at LIKE ?",
                (f"{today_str}%",)
            )
            row = cursor.fetchone()
            if row:
                count = row[0]
            conn.close()
        except Exception:
            # Fallback to cache counting
            count = sum(
                1 for v in self.applied_cache.values()
                if (v.get("timestamp", "").startswith(today_str) or v.get("created_at", "").startswith(today_str))
                and v.get("status") in ("applied", "dry_run_completed")
            )
        return count

    def get_today_by_platform(self) -> Dict[str, int]:
        """Returns breakdown of today's applications by platform."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        breakdown: Dict[str, int] = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT platform, count(*) FROM applications WHERE status IN ('applied', 'dry_run_completed') AND created_at LIKE ? GROUP BY platform",
                (f"{today_str}%",)
            )
            for plat, cnt in cursor.fetchall():
                breakdown[plat or "unknown"] = cnt
            conn.close()
        except Exception:
            pass
        return breakdown
