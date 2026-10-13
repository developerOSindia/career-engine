# 🎯 CareerEngine: Open Source Autonomous Career Engine

[![Docs: GitHub Pages](https://img.shields.io/badge/Docs-GitHub%20Pages-06b6d4?style=for-the-badge&logo=github)](https://developerosindia.github.io/career-engine/)
[![License: MIT](https://img.shields.io/badge/License-MIT-f97316?style=for-the-badge)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-22c55e?style=for-the-badge&logo=python)](https://python.org)
[![Part of developerOS](https://img.shields.io/badge/Part%20of-developerOS-f97316?style=for-the-badge)](https://developeros.in/)

> 📖 **Setup & User Documentation**: [https://developerosindia.github.io/career-engine/](https://developerosindia.github.io/career-engine/)  
> 🌐 **CareerOS Web App (Application Tracker)**: [https://careeros.developeros.in/](https://careeros.developeros.in/)

---

### 🌐 The developerOS Career Suite

developerOS is a suite of free tools for engineers' careers, covering learning, tracking and applying:
- **[CloudPrep](https://developeros.in/)**: Teaches cloud certifications hands-on (AWS, GCP, Azure).
- **[ResumeOS](https://developeros.in/)**: Tailors your ATS resume with semantic AI matching.
- **[CareerOS](https://careeros.developeros.in/)**: Tracks applications, interviews, and offers in ₹ lakhs.
- **[DevTrack](https://developeros.in/)**: Analyses developer engineering activity and git metrics.
- **[Insights](https://developeros.in/)**: The engineering blog and industry salary benchmarks.
- **[Toolkit](https://developeros.in/)**: Browser-native utilities for everyday developer workflows.
- **CareerEngine (This Repository)**: The open-source automation layer: it applies to jobs through your own Chrome and runs on your machine. **CareerOS** is where you then track and compare what comes back.

> ℹ️ *Everything shares one developerOS sign-in, one design system and the same dark palette. CareerEngine is a standalone tool and does not sync with CareerOS yet.*

---

### ⚠️ Important Notice on Platform Terms & Account Risk

Automating job applications can breach the terms of service of platforms like LinkedIn and Naukri, and risks account restriction. CareerEngine uses authentic Google Chrome CDP remote debugging with human-like delays to minimize detection, but we strongly advise:
1. Always run with `--preview` or `--dry-run` first to inspect forms before submitting.
2. Keep application volume conservative (5–15 jobs per session).
3. Do not run continuous unattended high-frequency loops.

---

### 🔒 Local Privacy Architecture & Gemini API

- **What stays strictly local**: Your candidate master profile (`profile_config.json`), resume PDFs, API keys (`.env`), and SQLite database (`jobs.db`) remain entirely on your local machine and are protected by git pre-push security hooks.
- **What uses the cloud**: Only the raw text prompts of individual job screening questionnaires are evaluated via the Google Gemini API keys that you provide in `.env`.

---

## 🚀 Key Features

- **CDP Remote Debugging Integration**: Controls your authentic Google Chrome browser over port `9222`, inheriting your active LinkedIn and Naukri sessions, cookies, and 2FA credentials.
- **Dynamic Form Intelligence**:
  - Automatically parses screening questionnaires across dropdowns (`<select>`), radio buttons, text fields, and file upload modals.
  - **Rotational Multi-LLM Engine**: Round-robin rotation across multiple Google Gemini 3.x Flash-lite API keys (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`) with DeepSeek fallback to prevent rate limits.
  - **Permanent QA Memory**: Caches answered questions locally in `profile_config.json` to resolve recurring prompts instantly without redundant API calls.
  - **Form Validation Guardrails**: Restricts numeric experience inputs to prevent form validation length errors (`maxlength=20`).
- **Contextual Multi-Role Resume Selector**:
  - Analyzes the job title and description in real-time and attaches the best matching resume PDF from `resumes/` (`_DE`, `_DS`, `_AI`, `_SWE`, `_MLOps`).
- **Recruiter InMail Auto-Reply Engine**:
  - Inspects incoming LinkedIn messaging threads and drafts personalized responses highlighting candidate strengths, confirmed notice period (e.g. 30 days), and expected compensation.
- **Supported Platforms**:
  - Pre-built connectors for **LinkedIn** (Easy Apply & InMail fully operational) and **Naukri** (Batch Quick Apply & Chatbot questions scaffolds ready; test with `--preview`).
- **Relational Local History**:
  - Stored in SQLite database (`jobs.db`) and exported to spreadsheet format (`applied_jobs.csv`).

---

## 📁 Modular Directory Structure

```
career-engine/
├── docs/                             # GitHub Pages Documentation Website (developerosindia.github.io/career-engine)
│   ├── index.html                    # Responsive documentation & interactive playground
│   ├── styles.css                    # Glassmorphism dark mode aesthetic
│   ├── script.js                     # Tab switching, copy code, config generator
│   └── .nojekyll                     # Direct GitHub Pages asset serving
├── resumes/                          # Multi-Role Resumes Folder
│   ├── copy_your_resume_here.txt     # Placeholder & role tagging instructions
│   └── README.md                     # Documentation for _DE, _DS, _AI, _SWE tags
├── .env                              # Private API keys and local configuration (GITIGNORED)
├── .env.example                      # Public template for environment variables
├── .gitignore                        # Git exclusion rules (protects credentials and databases)
├── LICENSE                           # Open-source MIT License
├── config.yaml                       # Application settings, keywords, and search preferences
├── profile_config.json               # Candidate master profile facts & learned memory
├── main.py                           # Unified CLI entrypoint (apply, inmail, status, setup)
├── setup_agent.py                    # Interactive profile & secrets configuration wizard
├── agent.py                          # Backward-compatible wrapper for LinkedIn agent
├── requirements.txt                  # Python dependencies
│
├── core/                             # Core framework infrastructure
│   ├── __init__.py
│   ├── config_loader.py              # Loads .env & YAML with strict validation
│   ├── browser_engine.py             # Playwright CDP connection & stealth Chrome manager
│   ├── tracker.py                    # SQLite (jobs.db) & CSV (applied_jobs.csv) tracking
│   └── models.py                     # Typed dataclasses (JobPosting, ApplicationRecord, InMailMessage)
│
├── ai/                               # Multi-LLM reasoning engine
│   ├── __init__.py
│   ├── ai_solver.py                  # Rotational Gemini 3.x Flash-lite + NVIDIA DeepSeek V4
│   └── prompts.py                    # Structured system prompts (Form QA & InMail replies)
│
├── platforms/                        # Multi-platform job board architecture
│   ├── __init__.py
│   ├── base.py                       # BasePlatform abstract contract
│   ├── linkedin/                     # LinkedIn Easy Apply implementation
│   │   ├── __init__.py
│   │   ├── scanner.py                # Job search, card parsing, and URL generator
│   │   ├── form_filler.py            # Questionnaire solver, dropdowns, and radio handler
│   │   └── agent.py                  # LinkedIn job application coordinator
│   ├── naukri/                       # Naukri.com automated batch applicant & chatbot solver
│   ├── wellfound/                    # Connector for Wellfound / AngelList
│   └── indeed/                       # Connector for Indeed Apply
│
├── messaging/                        # Recruiter InMail auto-reply engine
│   ├── __init__.py
│   ├── inmail_scanner.py             # Scans /messaging/ for recruiter threads & InMails
│   ├── message_drafter.py            # Synthesizes personalized, professional replies
│   └── auto_responder.py             # Review & send coordinator (preview vs live send)
│
├── scripts/                          # Utility & launch scripts
│   └── launch_chrome.sh              # Launches Chrome on port 9222 with isolated profile
│
└── .agents/skills/career-automator/   # Agent Skill definition for Antigravity / Claude
    └── SKILL.md
```

---

## ⚙️ Installation & Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/developerOSindia/career-engine.git
cd career-engine

# Install required Python packages
pip install -r requirements.txt
```

### 2. Interactive Profile & Secrets Setup Agent
Run the interactive CareerEngine Setup Agent to automatically configure your profile, resume, search keywords, and API keys:
```bash
python3 main.py setup
# Or directly:
python3 setup_agent.py
```
The setup agent will walk you through setting up your:
- Full name, contact details, and location
- Resume PDF path
- Target job keywords and experience years
- Current and expected compensation (CTC)
- Free Gemini API keys (from [Google AI Studio](https://aistudio.google.com/))
- Local configuration (`.env`, `profile_config.json`, `config.yaml`, `jobs.db`)

*Note: All generated configuration files are strictly gitignored to keep your personal data local.*

### 3. Launch Google Chrome in Remote Debugging Mode
Run the launcher script in a separate terminal:
```bash
./scripts/launch_chrome.sh
```
> **Note**: If you are not already logged into LinkedIn in this Chrome window, log in once. Your session will remain safely cached in `~/.chrome-job-agent` across restarts.

---

## 💻 CLI Usage Guide

### 1. Live Job Applications (`apply`)

#### Preview Applications in Dry-Run Mode (Safe Test):
Navigates to matching jobs, fills every form step, attaches resume, captures review screenshots, and pauses without clicking submit:
```bash
python3 main.py apply --platform linkedin --dry-run --limit 5
```

#### Auto-Submit Live Applications:
Applies and submits applications directly:
```bash
python3 main.py apply --platform linkedin --live --limit 10
```

#### Search Specific Roles & Locations:
```bash
python3 main.py apply --keyword "Databricks Engineer" --location "Bengaluru" --live --limit 5
```

#### Autonomous Batch Applications on Naukri (No URLs Required):
Automatically queries Naukri across keywords (`Senior Data Engineer`, `Databricks Engineer`, `AWS Data Engineer`, etc.) in Bengaluru/Remote, scans 20 job cards per page, skips already applied jobs, fills applications via Quick Apply, and answers chatbot screening questions:
```bash
# Preview batch of 20 Naukri jobs in dry-run mode:
python3 main.py apply --platform naukri --dry-run --limit 20

# Live auto-submit 20 jobs on Naukri:
python3 main.py apply --platform naukri --live --limit 20

# Filter by custom keyword & location:
python3 main.py apply --platform naukri --keyword "Databricks Engineer" --location "Bengaluru" --live --limit 20
```

#### Apply to a Specific Direct URL (Naukri or LinkedIn):
Apply directly to any specific job link (such as top-tier email alerts or Aurus early-jobs):
```bash
# Preview application on a direct Naukri job link:
python3 main.py apply --platform naukri --url "https://www.naukri.com/aurus/early-jobs?jobId=290626926058..." --dry-run

# Live auto-apply on a direct Naukri job link:
python3 main.py apply --platform naukri --url "https://www.naukri.com/aurus/early-jobs?jobId=290626926058..." --live
```

#### Autonomous Applications on Wellfound & Instahyre:
```bash
# Preview Wellfound startup applications with dynamic pitch notes:
python3 main.py apply --platform wellfound --dry-run --limit 5

# Live auto-submit applications on Wellfound:
python3 main.py apply --platform wellfound --live --limit 5

# Preview curated applications on Instahyre with automated screening Q&A:
python3 main.py apply --platform instahyre --dry-run --limit 5
```

#### Apply to All Configured Platforms in Batch:
```bash
python3 main.py apply --platform all --dry-run --limit 10
```

---

### 2. Local Web Studio Dashboard GUI (`studio`)

Launch the zero-dependency developerOS Web Studio dashboard in your browser to inspect database metrics, preview form screenshots, manage candidate profile memory, and trigger CLI runs:

```bash
# Launch Studio on default port 8501:
python3 main.py studio

# Specify custom port or bind address:
python3 main.py studio --port 8599 --host 127.0.0.1
```

- **Dashboard**: Real-time KPI counters (`Applied`, `Dry Run Completed`, `Failed`), status breakdown, and recent applications.
- **Applications Explorer**: Searchable, filterable table of every job record with direct URLs, salary notes, and timestamps.
- **Run Orchestrator**: Select platform, mode (`Live` or `Dry Run`), and application limit with real-time terminal output streaming.
- **Screenshot Lightbox**: Visual gallery of review screenshots captured during `--preview` and live runs.
- **Profile JSON Editor**: Live viewer and editor for `profile_config.json` candidate facts and learned screening memory.
- **100% On-Device**: Built natively on Python's standard library `ThreadingHTTPServer` with zero cloud telemetry or data leaks.

---

### 3. Autonomous Auto-Pilot Mode (`auto`)

Run CareerEngine on autonomous background auto-pilot with human circadian pacing, daily safety quota limits, multi-platform round-robin cycling, and automatic recruiter InMail answering:

```bash
# Launch Auto-Pilot in preview mode with safe defaults (180 min interval, 20 daily apps cap):
python3 main.py auto --interval 180 --daily-limit 20 --dry-run

# Launch Auto-Pilot in live auto-submit mode:
python3 main.py auto --interval 120 --daily-limit 15 --live

# Custom cycle interval and 24/7 unrestricted hours:
python3 main.py auto --interval 60 --session-limit 3 --all-hours --dry-run
```

- **Circadian Pacing**: Only operates during business hours (09:00 - 19:00 local time) by default to avoid unnatural overnight bot activity.
- **Daily Safety Quotas**: Enforces hard caps (e.g. 20 applications/day total) in SQLite `jobs.db`. Once reached, rests until the next day.
- **Round-Robin Multi-Platform**: Cycles evenly across LinkedIn, Naukri, Wellfound, and Instahyre.
- **InMail Monitoring Loop**: Automatically inspects and answers unread recruiter inquiries after each batch.
- **Randomized Jitter**: Varies sleep intervals by ±10% to eliminate static cron fingerprints.
- **GUI Controls**: Can also be started, paused, and monitored visually from the Web Studio dashboard (`http://localhost:8501`).

---

### 4. Recruiter InMail & Message Auto-Reply (`inmail`)

#### Preview InMail Drafts (Dry-Run):
Scans your unread LinkedIn messages, analyzes recruiter inquiries, and displays proposed replies in the terminal without sending:
```bash
python3 main.py inmail --preview --limit 5
```

#### Live Auto-Send Replies:
Types and delivers AI-crafted responses directly into the message thread:
```bash
python3 main.py inmail --send --limit 5
```

#### Scan All Conversations (Including Read):
```bash
python3 main.py inmail --preview --all
```

---

### 5. Application Status Dashboard (`status`)

Inspect your complete application pipeline, status breakdown, and recent recruiter contacts:
```bash
python3 main.py status
```

Example Output:
```
============================================================
📊 CareerEngine - Application Status Dashboard
📁 Database: ./jobs.db
============================================================

📈 Applications Breakdown by Status:
  ✅ Applied             : 35
  🎯 Dry Run Completed   : 4
  ⏭️ Failed              : 7
  ⚠️ Needs Review        : 3
  ⏭️ Skipped             : 72

🕒 Last 10 Submitted Applications:
  • Full Stack Engineer with Mobile  @ Full Stack Engineer wi [Remote] | Hirer: Gayatri A
  • Software Engineer Intern (golang @ Software Engineer Inte [Remote]
  • Cloud Support Engineer @ Cloud Support Engineer [Remote]
  • Senior AI Compiler Engineer @ Senior AI Compiler Eng [Remote] | Hirer: Uday Bhaskar
  • Senior Statistical Programmer wi @ Senior Statistical Pro [Remote] | Hirer: Anchal Panchal
  • Linux Kernel Engineer @ Linux Kernel Engineer [Remote]
  • Software Engineer @ Software Engineer [Remote] | Hirer: Khursheed Ahmed
  • Remote Java Developer @ Remote Java Developer  [Remote]
  • (Senior) ServiceNow AI Engineer  @ (Senior) ServiceNow AI [Remote] | Hirer: Ravi prajapati
============================================================
```

---

### 6. Candidate Profile Scoring & ATS Audit (`score` / `audit`)

Audit and benchmark your candidate profile completeness, market readiness, and ATS fit before launching automated application campaigns:
```bash
# Run local deterministic ATS scoring and audit:
python3 main.py score

# Run scoring with AI executive critique from connected LLM (Claude, OpenAI, or Gemini):
python3 main.py score --llm
```

**Evaluated Criteria (100 Points Total):**
1. **Contact & Online Presence (15 pts)**: Full name, verified email, telephone with country code, location anchor, and active LinkedIn / GitHub / portfolio links.
2. **Work Experience & Compensation Fundamentals (25 pts)**: Current role, company, years of experience, metric-rich achievement descriptions, notice period calibration, and current vs. expected CTC in LPA.
3. **Technical Skill Density & Recency (20 pts)**: Skill catalog breadth, core programming languages, relational/NoSQL databases, cloud infrastructure, and modern specializations.
4. **Multi-Role Resume Tag Readiness (20 pts)**: Physical PDF resumes in `resumes/` folder tagged with `_DE`, `_DS`, `_AI`, `_SWE`, and `_MLOps` for automated dynamic role switching.
5. **Screening Memory & Automation Defaults (20 pts)**: Legal work authorization, visa sponsorship flags, joining availability, and cached `custom_answers` depth.

Produces an overall score, letter grade (`A+`, `A`, `B+`, `B`, `C`), multi-role fit % for 5 engineering tracks, and prioritized actionable recommendations to achieve 100%.

---

## 🧠 Semantic AI Matcher & Dynamic Pitch Generator

CareerEngine pairs candidate profiles with deep job description evaluation:
- **Semantic Scoring (0–100%)**: Uses Google Gemini to score role alignment against candidate experience before applying.
- **Resume Tag Alignment**: Recommends the optimal resume tag (`_DE`, `_DS`, `_AI`, `_SWE`, `_MLOps`) and pairs it with matching resume PDFs.
- **Dynamic Startup Pitch Generator**: Automatically synthesizes high-converting, personalized 2–3 sentence notes to founders and recruiters on platforms like Wellfound and LinkedIn InMail, emphasizing verified achievements and notice period without fluff.

---

## 📄 Multi-Role Intelligent Resume Selector

CareerEngine can automatically choose between multiple tailored resumes depending on the job you are applying to. Simply place your resume PDFs into the [`resumes/`](resumes/) folder using role tags:

| Target Role | Filename Pattern | Examples |
|---|---|---|
| **Data Engineering** | `*_DE*.pdf`, `*_data_engineer*.pdf` | `resumes/Alex_DE_resume.pdf` |
| **Data Science / ML** | `*_DS*.pdf`, `*_data_science*.pdf` | `resumes/Alex_DS_resume.pdf` |
| **AI / GenAI Platforms** | `*_AI*.pdf`, `*_genai*.pdf`, `*_llm*.pdf` | `resumes/Alex_AI_resume.pdf` |
| **Software Engineering** | `*_SWE*.pdf`, `*_software*.pdf`, `*_backend*.pdf` | `resumes/Alex_SWE_resume.pdf` |
| **MLOps / Cloud** | `*_MLOps*.pdf`, `*_devops*.pdf` | `resumes/Alex_MLOps_resume.pdf` |

*CareerEngine analyzes the job title and description in real-time and attaches the best matching resume automatically.*

---

## 👤 Candidate Profile & Customization

The candidate facts used to answer form questions and compose recruiter messages are defined locally in `profile_config.json`:

| Metric / Fact | Default Example | Rules Enforced |
|---|---|---|
| **Total Experience** | Configurable (e.g. 5 yrs) | Used for experience verification |
| **Current Role** | Configurable | Verified from profile summary |
| **Current CTC** | Configurable (e.g. 30 LPA) | Fixed base + variable split |
| **Expected CTC** | Configurable (e.g. 40 LPA) | Enforced on compensation fields |
| **Notice Period** | Configurable (e.g. 30 days) | Answered across dropdowns & numeric inputs |
| **Core Technical Skills** | Configurable | Filtered against role requirements |
| **Location Authorization** | Configurable | Work authorization & relocation preferences |

### Dynamic Questionnaire Memory:
Whenever a new unique question is encountered, the AI generates the appropriate response based on your profile and records it into `profile_config.json["custom_answers"]`. You can edit or fine-tune any saved response directly in that file.

---

## 🛡️ Anti-Bot Safety & Rate Limiting

- **Realistic Delays**:
  - Dwell time on job pages (2.5s) before interacting.
  - Delays between questionnaire steps (1.2s – 1.8s).
  - Human keystroke jitter (30ms – 90ms per character).
  - 3.5s cooldown between consecutive job applications.
- **Batch Processing**: Designed to run in batches of 5 to 15 applications per session to keep account activity completely organic.
- **Safe Form Discard**: Incomplete applications or unsupported multi-stage assessments are cleanly discarded using LinkedIn's `Discard` modal, preventing unwanted draft accumulations on your profile.

---

## 🌐 Multi-Platform Extension Guide

To implement a new job board (e.g. `naukri`, `wellfound`, `indeed`):
1. Navigate to `platforms/<platform_name>/connector.py`.
2. Inherit from `BasePlatform` and implement:
   - `authenticate_or_check_session()`: Validates session cookies.
   - `search_jobs()`: Extracts job listings and IDs.
   - `apply_to_job()`: Automates form filling on that platform.
3. The platform is immediately runnable via `python3 main.py apply --platform <name>`.

---

## ⚖️ CareerEngine vs Legacy Bots vs Chrome Extensions

| Feature / Architecture | CareerEngine (Open Source) | Legacy Python Bots (Selenium) | Browser Extensions |
|---|---|---|---|
| **Execution Architecture** | **Authentic Chrome CDP (9222)** | Headless / Selenium | In-page DOM Injection |
| **Detection Evasion** | **Genuine Session & 2FA Cookies** | Flagged / Triggers CAPTCHA | Detected by security scripts |
| **Questionnaire AI** | **Rotational Gemini 3.x Flash-lite** | Hardcoded regex lists | Single key / Paid cloud |
| **Multi-Role Resume Selector** | **Contextual Auto-Routing (`_DE`, `_DS`, `_AI`)** | Single static PDF | Static upload |
| **InMail Auto-Reply** | **Autonomous Recruiter Negotiator** | ❌ Not Supported | ❌ Not Supported |
| **Data Privacy** | **100% Local (Git-safe, zero egress)** | Plaintext credentials | Cloud-stored data |
| **Cost** | **Free & Open Source (MIT)** | Abandoned / Broken | $30–$80 / month |

---

## ❓ Frequently Asked Questions (FAQ)

### What is CareerEngine and how does it relate to CareerOS?
**CareerOS** ([careeros.developeros.in](https://careeros.developeros.in/)) is the web platform where engineers track and compare job applications, interviews, and offers in ₹ lakhs. **CareerEngine** is the open-source automation companion: it runs locally on your machine, attaches to your Google Chrome browser via CDP port 9222, and assists with filling job applications across LinkedIn and Naukri. *Note: CareerEngine is an independent open-source tool and does not sync automatically with CareerOS web yet.*

### Is there account risk when using automated tools?
Yes. Automated job applications can breach platform terms of service on LinkedIn and Naukri, and risk account restriction. CareerEngine controls your genuine Chrome browser with organic dwell times and typing jitter to minimize detection, but we strongly advise testing with `--dry-run` / `--preview` first, inspecting applications, and keeping application limits conservative (5–15 jobs per session).

### Which AI models are supported for form filling?
CareerEngine features a multi-provider fallback pipeline:
1. **Google Gemini** (Gemini 3.5 Flash-lite / 3.1 Flash-lite via `GEMINI_API_KEY_1..3`)
2. **Anthropic Claude** (Claude 3.5 Haiku / Sonnet via `ANTHROPIC_API_KEY` or `CLAUDE_API_KEY`)
3. **OpenAI** (GPT-4o / GPT-4o-mini via `OPENAI_API_KEY`)
4. **NVIDIA DeepSeek** (DeepSeek V4 via `NVIDIA_API_KEY`)
5. **Local Ollama** (Offline zero-cost model via `http://localhost:11434`)

Learned answers are cached locally in `profile_config.json["custom_answers"]` to eliminate repetitive API latency and costs.

### How does the Multi-Role Resume Selector choose a resume?
CareerEngine inspects the job title and requirements, matching them against tagged PDFs in `resumes/` (e.g. `_DE` for Data Engineering, `_DS` for Data Science, `_AI` for GenAI Platforms, `_SWE` for Backend, and `_MLOps` for DevOps).

### Is candidate data sent to the cloud?
Your candidate profile, resumes, API keys, and local SQLite database (`jobs.db`) stay strictly on your local machine. Only the raw questionnaire text prompts are sent to the LLM API keys that you configure in `.env` to evaluate answers.

---

## 📄 License

CareerEngine is open-sourced under the [MIT License](LICENSE).
© 2026 [developerOS](https://github.com/developerOSindia). All rights reserved.
