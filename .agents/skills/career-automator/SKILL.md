---
name: career-automator
description: Autonomous career agent for multi-platform job applications (LinkedIn, Naukri, Wellfound, Indeed), AI questionnaire solving with rotational Gemini 3.x / DeepSeek, and automated recruiter InMail reply drafting and outreach.
risk: low
source: workspace
---

# Career Automator Skill

Autonomous, human-stealth agent for job applications, screening questionnaire solving, and inbound recruiter InMail communications across modern job boards.

## Overview & Core Capabilities

The Career Automator connects to a real Chrome user session over Chrome DevTools Protocol (CDP) on port `9222`, preserving existing cookies, login tokens, and 2FA states without triggering bot protections or login challenges.

### Primary Engines
1. **Multi-Platform Application Engine**:
   - Discovers jobs via keyword search and advanced filters (Remote, Location, Easy Apply, Date Posted).
   - Solves multi-step application modals (personal info, work authorization, dropdowns, numeric years, radio groups, and long-form architectural questions).
   - Uses rotational Gemini 3.x Flash-lite models (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`) and NVIDIA DeepSeek fallback.
   - Discards incomplete forms cleanly without saving drafts to avoid cluttering candidate profiles.
   - Dual-writes all outcomes to SQLite (`jobs.db`) and CSV (`applied_jobs.csv`).

2. **Inbound Recruiter & InMail Auto-Reply Engine**:
   - Scans LinkedIn Messaging (`https://www.linkedin.com/messaging/`) for incoming recruiter InMails and job pitches.
   - Extracts sender identity, title, company, and message body.
   - Synthesizes personalized, high-converting responses using candidate facts (5 years experience, 30L current CTC, 40L expected CTC, 30 days notice period).
   - Features `--preview` mode (inspect drafts before sending) and `--send` mode (types and sends).

3. **Multi-Job-Board Expansion**:
   - Unified `BasePlatform` interface for adding new platforms (`platforms/naukri/`, `platforms/wellfound/`, `platforms/indeed/`).

---

## Directory Layout

```
resume/
├── .env                              # API keys & configurations (gitignored)
├── .env.example                      # Template for version control
├── .gitignore                        # Git exclusion rules
├── config.yaml                       # Application targets & delays
├── profile_config.json               # Candidate master facts & learned QA memory
├── main.py                           # Unified CLI entrypoint
├── requirements.txt                  # Python dependencies
│
├── core/                             # Core framework infrastructure
│   ├── config_loader.py              # Loads .env & YAML with validation
│   ├── browser_engine.py             # Playwright CDP connection & stealth
│   ├── tracker.py                    # SQLite & CSV multi-platform tracker
│   └── models.py                     # Typed dataclasses (Job, Application, Message)
│
├── ai/                               # Multi-LLM reasoning engine
│   ├── ai_solver.py                  # Rotational Gemini 3.x + NVIDIA DeepSeek
│   └── prompts.py                    # Form QA & InMail reply system prompts
│
├── platforms/                        # Multi-board architecture
│   ├── base.py                       # BasePlatform abstract contract
│   ├── linkedin/                     # LinkedIn Easy Apply implementation
│   │   ├── scanner.py                # Job search & card parser
│   │   ├── form_filler.py            # Questionnaire & review solver
│   │   └── agent.py                  # LinkedIn job application coordinator
│   ├── naukri/                       # Naukri.com connector
│   ├── wellfound/                    # Wellfound / AngelList connector
│   └── indeed/                       # Indeed Apply connector
│
├── messaging/                        # Recruiter InMail auto-reply engine
│   ├── inmail_scanner.py             # Scans /messaging/ for recruiter threads
│   ├── message_drafter.py            # Synthesizes tailored recruiter replies
│   └── auto_responder.py             # Review & send coordinator
│
└── scripts/
    └── launch_chrome.sh              # Launches Chrome on port 9222 with isolated profile
```

---

## Prerequisites & Setup

### 1. Configure Environment Secrets
Copy `.env.example` to `.env` and configure your API keys:
```bash
cp .env.example .env
```
Ensure at least one `GEMINI_API_KEY_1` (or `2`/`3`) or `NVIDIA_API_KEY` is present.

### 2. Launch Debugging Chrome
Start the Chrome instance with remote debugging enabled:
```bash
./scripts/launch_chrome.sh
```
*Log into LinkedIn once in this browser window. Your login session persists in `~/.chrome-job-agent`.*

---

## CLI Command Reference

### Job Applications (`main.py apply`)
```bash
# Preview applications in Dry-Run mode (fills forms, takes review screenshots, does NOT submit):
python3 main.py apply --platform linkedin --dry-run --limit 5

# Live auto-apply on LinkedIn:
python3 main.py apply --platform linkedin --live --limit 10

# Autonomous batch applications on Naukri (No URLs needed - searches, extracts cards, auto-applies):
python3 main.py apply --platform naukri --live --limit 20

# Preview batch applications on Naukri in dry-run mode:
python3 main.py apply --platform naukri --dry-run --limit 20

# Apply directly to a specific URL (e.g. Aurus early-jobs or email alerts):
python3 main.py apply --platform naukri --url "<URL>" --live

# Search a specific job keyword and location:
python3 main.py apply --keyword "Databricks Engineer" --location "Bengaluru" --live --limit 5

# Backward compatibility wrapper:
python3 agent.py --live --limit 10
```

### Recruiter InMail Auto-Reply (`main.py inmail`)
```bash
# Preview AI-crafted responses for unread recruiter InMails without sending:
python3 main.py inmail --preview --limit 5

# Automatically send approved replies to incoming recruiter messages:
python3 main.py inmail --send --limit 5

# Process all conversations (including read messages):
python3 main.py inmail --preview --all
```

### Application Dashboard & Metrics (`main.py status`)
```bash
# Display summary of all applied jobs, success rates, and recent submissions:
python3 main.py status
```

---

## Candidate Profile Constraints

Always adhere to the verified candidate facts:
- **Total Experience**: 5 years (Full-time Senior Data Engineer).
- **Core Skills**: Python, PySpark, Databricks, AWS, Delta Lake, SQL, MLOps, AI/GenAI platforms.
- **Current CTC**: 30 LPA (Fixed: 24 LPA, Variable/Benefits: 6 LPA).
- **Expected CTC**: 40 LPA.
- **Notice Period**: 30 days (negotiable from official 60 days).
- **Location**: Bengaluru, Karnataka, India (Indian citizen, No visa sponsorship required, open to Remote, Hybrid, or 5-day WFO).

---

## Adding a New Job Platform

To add a new platform (e.g., Naukri, Wellfound, Instahyre):
1. Subclass `platforms.base.BasePlatform`.
2. Implement:
   - `authenticate_or_check_session()`
   - `search_jobs(keyword, location, remote, page_num)`
   - `apply_to_job(job)`
   - `run(keywords, location)`
3. Register the platform choice in `main.py`'s `handle_apply()`.
