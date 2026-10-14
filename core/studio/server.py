"""
CareerEngine Local Web Studio Server.
Zero-dependency HTTP server built on Python standard library.
Provides REST APIs and serves the developerOS-styled Web Studio frontend.
"""

import os
import sys
import json
import sqlite3
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
DB_PATH = ROOT_DIR / "jobs.db"
PROFILE_PATH = ROOT_DIR / "profile_config.json"
SCREENSHOTS_DIR = ROOT_DIR / "screenshots"

# Global state for process runner
class RunnerManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.process: Optional[subprocess.Popen] = None
        self.logs: List[str] = []
        self.is_running: bool = False
        self.current_task: str = ""

    def start_run(self, command_args: List[str], task_name: str) -> bool:
        with self.lock:
            if self.is_running and self.process and self.process.poll() is None:
                return False  # Already running
            
            self.logs = [f"🚀 Starting task: {task_name}", f"Command: {' '.join(command_args)}\n"]
            self.is_running = True
            self.current_task = task_name

            def worker():
                try:
                    self.process = subprocess.Popen(
                        command_args,
                        cwd=str(ROOT_DIR),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    for line in iter(self.process.stdout.readline, ''):
                        if not line and self.process.poll() is not None:
                            break
                        with self.lock:
                            self.logs.append(line.rstrip())
                            if len(self.logs) > 1000:
                                self.logs.pop(0)
                    self.process.stdout.close()
                    self.process.wait()
                    with self.lock:
                        self.logs.append(f"\n✅ Task finished with exit code {self.process.returncode}")
                except Exception as e:
                    with self.lock:
                        self.logs.append(f"\n❌ Error during execution: {e}")
                finally:
                    with self.lock:
                        self.is_running = False

            t = threading.Thread(target=worker, daemon=True)
            t.start()
            return True

    def stop_run(self) -> bool:
        with self.lock:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.logs.append("⚠️ Process terminated by user request.")
                self.is_running = False
                return True
            return False

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "is_running": self.is_running,
                "current_task": self.current_task,
                "logs": self.logs[-200:]
            }

runner_manager = RunnerManager()

class StudioRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Mute standard noisy HTTP access logs, output only errors
        if args and str(args[1])[0] in ['4', '5']:
            sys.stderr.write(f"[Studio HTTP Error] {args[0]} - {args[1]}\n")

    def send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Static file: Home SPA
        if path == "/" or path == "/index.html":
            index_file = STATIC_DIR / "index.html"
            if index_file.exists():
                content = index_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_json({"error": "Studio static UI not found"}, 404)
            return

        # API: Stats Overview
        if path == "/api/stats":
            self.handle_api_stats()
            return

        # API: Applications List
        if path == "/api/jobs":
            self.handle_api_jobs(query)
            return

        # API: Screenshots List
        if path == "/api/screenshots":
            self.handle_api_screenshots()
            return

        # API: Serve a specific Screenshot Image
        if path.startswith("/api/screenshot/"):
            filename = os.path.basename(path.replace("/api/screenshot/", ""))
            self.handle_serve_screenshot(filename)
            return

        # API: Profile score & ATS audit report
        if path == "/api/profile/score":
            self.handle_get_profile_score()
            return

        # API: Profile config
        if path == "/api/profile":
            self.handle_get_profile()
            return

        # API: Run status & logs
        if path == "/api/run/status":
            self.send_json(runner_manager.get_status())
            return

        # API: Auto-Pilot Status
        if path == "/api/autopilot/status":
            from core.autopilot import autopilot
            self.send_json(autopilot.get_status())
            return

        # API: Pipeline Analytics & Insights
        if path == "/api/analytics":
            from core.analytics_exporter import analytics_exporter
            self.send_json(analytics_exporter.get_analytics_summary())
            return

        # API: Export Applications (CSV / JSON / Markdown download)
        if path == "/api/export":
            from core.analytics_exporter import analytics_exporter
            fmt = query.get("format", ["csv"])[0].lower()
            if fmt == "json":
                out_path = analytics_exporter.export_json()
                content = Path(out_path).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="applications_export.json"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            elif fmt in ("markdown", "md"):
                out_path = analytics_exporter.export_markdown()
                content = Path(out_path).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="applications_report.md"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                out_path = analytics_exporter.export_csv()
                content = Path(out_path).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="applications_export.csv"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # API: Cross-Platform Duplicate Audit
        if path == "/api/dedup/audit":
            from core.smart_dedup import smart_deduplicator
            dups = smart_deduplicator.audit_database_duplicates(str(DB_PATH))
            self.send_json({
                "total_duplicate_groups": len(dups),
                "groups": dups
            })
            return

        self.send_json({"error": "Not Found", "path": path}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body_data = {}
        if content_length > 0:
            try:
                body_bytes = self.rfile.read(content_length)
                body_data = json.loads(body_bytes.decode("utf-8"))
            except Exception as e:
                self.send_json({"error": f"Invalid JSON payload: {e}"}, 400)
                return

        # API: ATS Resume Tailoring
        if path == "/api/resume/tailor":
            from core.resume_tailor import resume_tailor
            job_title = body_data.get("job_title", "Software Engineer")
            company = body_data.get("company", "Tech Company")
            job_description = body_data.get("job_description", "")
            target_role = body_data.get("target_role")
            job_id = body_data.get("job_id")
            if job_id and not job_description:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT title, company, job_description FROM applications WHERE job_id = ? LIMIT 1", (job_id,))
                    row = c.fetchone()
                    conn.close()
                    if row:
                        job_title = job_title or row[0]
                        company = company or row[1]
                        job_description = row[2] or ""
                except Exception:
                    pass
            report = resume_tailor.tailor_for_job(
                job_title=job_title,
                job_description=job_description,
                company=company,
                target_role=target_role
            )
            self.send_json(report.to_dict())
            return

        # API: Auto-Pilot Start
        if path == "/api/autopilot/start":
            from core.autopilot import autopilot
            daily_limit = int(body_data.get("daily_limit", autopilot.daily_limit))
            interval_minutes = int(body_data.get("interval_minutes", autopilot.interval_minutes))
            dry_run = bool(body_data.get("dry_run", True))
            platforms = body_data.get("platforms", autopilot.platforms)

            autopilot.daily_limit = daily_limit
            autopilot.interval_minutes = interval_minutes
            autopilot.dry_run = dry_run
            autopilot.platforms = platforms
            started = autopilot.start(in_background=True)
            self.send_json({"success": started, "status": autopilot.get_status()})
            return

        # API: Auto-Pilot Stop
        if path == "/api/autopilot/stop":
            from core.autopilot import autopilot
            stopped = autopilot.stop()
            self.send_json({"success": stopped, "status": autopilot.get_status()})
            return

        # API: Trigger CLI Run
        if path == "/api/run":
            platform = body_data.get("platform", "linkedin")
            mode = body_data.get("mode", "preview")
            limit = int(body_data.get("limit", 5))
            keyword = body_data.get("keyword", "")

            cmd = [sys.executable, str(ROOT_DIR / "main.py"), "apply", "--platform", platform, "--limit", str(limit)]
            if mode == "live":
                cmd.append("--live")
            else:
                cmd.append("--dry-run")
            if keyword:
                cmd.extend(["--keyword", keyword])

            task_name = f"Apply ({platform.upper()} - {mode.upper()} - limit: {limit})"
            success = runner_manager.start_run(cmd, task_name)
            if success:
                self.send_json({"status": "started", "task": task_name, "command": cmd})
            else:
                self.send_json({"error": "Another process is already running. Please stop it first."}, 409)
            return

        # API: Stop Running Process
        if path == "/api/run/stop":
            stopped = runner_manager.stop_run()
            self.send_json({"stopped": stopped})
            return

        # API: Recruiter Outreach Synthesis
        if path == "/api/outreach/generate":
            from core.cold_outreach import cold_outreach_synthesizer
            company = body_data.get("company", "")
            job_title = body_data.get("job_title", "Senior Software Engineer")
            target_name = body_data.get("target_name")
            job_id = body_data.get("job_id")
            if job_id and (not company or not target_name):
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT title, company, hiring_manager_name FROM applications WHERE job_id = ? LIMIT 1", (job_id,))
                    row = c.fetchone()
                    conn.close()
                    if row:
                        job_title = job_title or row[0]
                        company = company or row[1]
                        target_name = target_name or row[2]
                except Exception:
                    pass
            if not company:
                self.send_json({"error": "Company name is required"}, 400)
                return
            kit = cold_outreach_synthesizer.generate_outreach_kit(
                company=company,
                job_title=job_title,
                target_name=target_name
            )
            self.send_json(kit.to_dict())
            return

        # API: Interview Preparation & STAR Simulator
        if path == "/api/interview/prep":
            from core.interview_prep import interview_prep_simulator
            job_title = body_data.get("job_title", "Senior Software Engineer")
            company = body_data.get("company", "Tech Company")
            job_description = body_data.get("job_description", "")
            job_id = body_data.get("job_id")
            if job_id and not job_description:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT title, company, job_description FROM applications WHERE job_id = ? LIMIT 1", (job_id,))
                    row = c.fetchone()
                    conn.close()
                    if row:
                        job_title = job_title or row[0]
                        company = company or row[1]
                        job_description = row[2] or ""
                except Exception:
                    pass
            kit = interview_prep_simulator.generate_prep_kit(
                job_title=job_title,
                company=company,
                job_description=job_description
            )
            self.send_json(kit.to_dict())
            return

        # API: Update Job Status (Kanban pipeline stage change)
        if path == "/api/jobs/update-status":
            job_id = body_data.get("job_id")
            new_status = body_data.get("status")
            if not job_id or not new_status:
                self.send_json({"error": "job_id and status are required"}, 400)
                return
            valid_statuses = {"applied", "reviewing", "interview_scheduled", "offer", "archived", "rejected", "dry_run_completed", "failed", "skipped"}
            if new_status not in valid_statuses:
                self.send_json({"error": f"Invalid status: {new_status}"}, 400)
                return
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE applications SET status = ? WHERE job_id = ?", (new_status, job_id))
                rows_updated = c.rowcount
                conn.commit()
                conn.close()
                self.send_json({"success": True, "job_id": job_id, "status": new_status, "rows_updated": rows_updated})
            except Exception as e:
                self.send_json({"error": f"Failed to update status: {e}"}, 500)
            return

        # API: Update Profile Config
        if path == "/api/profile":
            try:
                if not PROFILE_PATH.exists():
                    self.send_json({"error": "profile_config.json not found"}, 404)
                    return
                with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(body_data, f, indent=2)
                self.send_json({"status": "success", "message": "Profile updated successfully"})
            except Exception as e:
                self.send_json({"error": f"Failed to save profile: {e}"}, 500)
            return

        self.send_json({"error": "Endpoint not found"}, 404)

    def handle_api_stats(self):
        """Returns aggregated database statistics."""
        if not DB_PATH.exists():
            self.send_json({
                "total_applications": 0,
                "status_breakdown": {},
                "platform_breakdown": {},
                "recent_jobs": []
            })
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Status breakdown
            cursor.execute("SELECT status, count(*) as count FROM applications GROUP BY status")
            status_breakdown = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Platform breakdown
            cursor.execute("SELECT platform, count(*) as count FROM applications GROUP BY platform")
            platform_breakdown = {row["platform"]: row["count"] for row in cursor.fetchall()}

            # Total
            cursor.execute("SELECT count(*) as total FROM applications")
            total = cursor.fetchone()["total"]

            # Recent 10
            cursor.execute("""
                SELECT id, job_id, title, company, location, platform, status, created_at, notes as salary_notes, screenshot_path as screenshot
                FROM applications
                ORDER BY id DESC
                LIMIT 10
            """)
            recent_jobs = [dict(row) for row in cursor.fetchall()]

            conn.close()
            self.send_json({
                "total_applications": total,
                "status_breakdown": status_breakdown,
                "platform_breakdown": platform_breakdown,
                "recent_jobs": recent_jobs
            })
        except Exception as e:
            self.send_json({"error": f"Database error: {e}"}, 500)

    def handle_api_jobs(self, query: Dict[str, List[str]]):
        """Returns filterable and paginated application records."""
        if not DB_PATH.exists():
            self.send_json({"jobs": [], "total": 0, "page": 1, "pages": 0})
            return

        platform = query.get("platform", [None])[0]
        status = query.get("status", [None])[0]
        search = query.get("q", [None])[0]
        page = max(1, int(query.get("page", [1])[0]))
        limit = min(100, max(5, int(query.get("limit", [20])[0])))
        offset = (page - 1) * limit

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            where_clauses = []
            params = []

            if platform and platform != "all":
                where_clauses.append("platform = ?")
                params.append(platform)
            if status and status != "all":
                where_clauses.append("status = ?")
                params.append(status)
            if search:
                where_clauses.append("(title LIKE ? OR company LIKE ? OR location LIKE ?)")
                p = f"%{search}%"
                params.extend([p, p, p])

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # Count total
            cursor.execute(f"SELECT count(*) as cnt FROM applications {where_sql}", params)
            total = cursor.fetchone()["cnt"]

            # Fetch items
            cursor.execute(f"""
                SELECT id, job_id, title, company, location, platform, status, created_at, notes as salary_notes, key_skills, screenshot_path as screenshot, job_url
                FROM applications
                {where_sql}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, params + [limit, offset])

            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()

            pages = (total + limit - 1) // limit if total > 0 else 1

            self.send_json({
                "jobs": rows,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages
            })
        except Exception as e:
            self.send_json({"error": f"Database error: {e}"}, 500)

    def handle_api_screenshots(self):
        """Lists screenshots available on disk."""
        if not SCREENSHOTS_DIR.exists():
            self.send_json({"screenshots": []})
            return

        try:
            files = []
            for p in sorted(SCREENSHOTS_DIR.glob("*.png"), key=lambda f: f.stat().st_mtime, reverse=True)[:50]:
                files.append({
                    "filename": p.name,
                    "size_bytes": p.stat().st_size,
                    "modified": p.stat().st_mtime
                })
            self.send_json({"screenshots": files})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_serve_screenshot(self, filename: str):
        """Safely streams screenshot file from screenshots directory."""
        if not filename or ".." in filename or "/" in filename or "\\" in filename:
            self.send_json({"error": "Invalid filename"}, 400)
            return

        file_path = SCREENSHOTS_DIR / filename
        if not file_path.exists() or not file_path.is_file():
            self.send_json({"error": "Screenshot not found"}, 404)
            return

        try:
            content = file_path.read_bytes()
            mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_json({"error": f"Could not read file: {e}"}, 500)

    def handle_get_profile(self):
        """Reads candidate profile facts."""
        if not PROFILE_PATH.exists():
            self.send_json({"error": "profile_config.json not found"}, 404)
            return
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.send_json(data)
        except Exception as e:
            self.send_json({"error": f"Failed to load profile: {e}"}, 500)

    def handle_get_profile_score(self):
        """Computes candidate ATS profile score and audit recommendations."""
        try:
            from core.profile_scorer import profile_scorer
            report = profile_scorer.evaluate()
            self.send_json(report.to_dict())
        except Exception as e:
            self.send_json({"error": f"Failed to compute profile score: {e}"}, 500)

def start_studio_server(host: str = "127.0.0.1", port: int = 8501):
    """Starts the CareerEngine Local Web Studio HTTP server."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, StudioRequestHandler)
    print(f"\n{'='*64}")
    print(f"🚀 CareerEngine Web Studio is running locally!")
    print(f"🌐 Access Dashboard: http://{host}:{port}/")
    print(f"🔒 Data Privacy: 100% on-device (Zero external telemetry)")
    print(f"⚡ Press Ctrl+C in terminal to stop.")
    print(f"{'='*64}\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping CareerEngine Web Studio...")
        runner_manager.stop_run()
        httpd.server_close()
        print("✓ Studio stopped cleanly.")
