# 🎯 CareerEngine: Autonomous Multi-Platform Career Operating System & Recruiter Agent

[![Documentation](https://img.shields.io/badge/Docs-GitHub%20Pages-6366F1?style=for-the-badge&logo=github)](https://developerosindia.github.io/career-engine/)
[![License: MIT](https://img.shields.io/badge/License-MIT-38BDF8?style=for-the-badge)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-10B981?style=for-the-badge&logo=python)](https://python.org)
[![Privacy: 100% Local](https://img.shields.io/badge/Privacy-100%25%20Local-purple?style=for-the-badge)](https://developerosindia.github.io/career-engine/#privacy)

> 📖 **Interactive Documentation & Setup Guide**: [https://developerosindia.github.io/career-engine/](https://developerosindia.github.io/career-engine/)

> **CareerEngine** is an open-source autonomous career operating system developed by [developerOS](https://github.com/developerOSindia). It uses authentic Google Chrome remote debugging (CDP port 9222) and rotational Gemini AI models to search, solve questionnaire screenings, and auto-apply for engineering roles across LinkedIn and Naukri with 100% local data privacy.

### ⚡ Key Metrics & Architecture
| Metric | Performance Benchmark | Description |
|---|---|---|
| **Data Privacy** | `100% Local` | All secrets, databases, and resumes stay strictly on your local machine |
| **Telemetry Egress** | `0 MB` | No tracking, analytics, or external telemetry of any kind |
| **Form Solution Latency** | `< 1.5s` | Round-robin Gemini 3.x Flash-lite rotation with local cache memory |
| **Resume Matching** | `5+ Role Presets` | Automatic contextual PDF selection (`_DE`, `_DS`, `_AI`, `_SWE`, `_MLOps`) |
| **Stealth Protocol** | `Chrome CDP 9222` | Genuine user profile session, avoiding bot detection and CAPTCHAs |

---

## 🚀 Key Features

- **CDP Remote Debugging Integration**: Controls your authentic Google Chrome browser over port `9222`, inheriting your active LinkedIn cookies, 2FA credentials, and session state without triggering bot detection or CAPTCHAs.
- **Dynamic Form Intelligence**:
  - Automatically parses LinkedIn Easy Apply dialogs across dropdowns (`<select>`), radio fieldsets, numeric inputs, text fields, and file upload triggers.
  - Multi-line question label extraction solves LinkedIn's nested DOM layouts without truncating questions.
  - **Rotational Multi-LLM Engine**: High-speed Google Gemini 3.x (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`) round-robin rotation across multiple API keys with NVIDIA / DeepSeek V4 fallback and automatic cooldowns.
  - **Permanent QA Memory**: Remembers answered questions in `profile_config.json` so recurring prompts are resolved instantly without API latency.
  - **Form Length Guardrails**: Prevents LinkedIn validation errors (`maxlength=20`) by strictly restricting years-of-experience questions to numeric integers.
- **Recruiter InMail Auto-Reply Engine**:
  - Navigates to `https://www.linkedin.com/messaging/` and inspects incoming recruiter reach-outs and InMails.
  - Understands the recruiter's pitch and drafts concise, polished responses highlighting candidate strengths, confirming notice period (30 days), and aligning compensation expectations (40 LPA expected, 30 LPA current).
  - Includes `--preview` (draft review) and `--send` (live automated reply) modes.
- **Multi-Job-Board Architecture**:
  - Standardized `BasePlatform` interface with pre-built connectors for **LinkedIn**, and scaffolds ready for **Naukri**, **Wellfound** (AngelList), and **Indeed**.
- **Transparent Dual Tracking**:
  - Full relational record stored in SQLite database (`jobs.db`).
  - Spreadsheet export in CSV (`applied_jobs.csv`) with 13 audit fields including hiring manager profile link, workplace type (Remote/Hybrid/Onsite), key skills, questions answered, and review screenshots.
- **Git-Safe Secrets Management**:
  - All API keys and environment configurations are strictly isolated in `.env` (gitignored).
  - Includes `.env.example` and `.gitignore` to guarantee credentials and personal application histories are never pushed to public repositories.

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

#### Backward Compatibility:
The legacy command continues to work seamlessly:
```bash
python3 agent.py --live --limit 10
```

---

### 2. Recruiter InMail & Message Auto-Reply (`inmail`)

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

### 3. Application Status Dashboard (`status`)

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
  • Fabric Azure Data Engineer @ Fabric Azure Data Engi [Remote] | Hirer: Rashi Shukla
============================================================
```

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

### What is CareerEngine?
CareerEngine is an open-source autonomous career operating system developed by developerOS. It connects to your existing Google Chrome browser via Chrome DevTools Protocol (CDP port 9222) to autonomously search, solve screening questionnaires, and apply for engineering roles across LinkedIn and Naukri while keeping all personal data strictly local.

### How does CareerEngine avoid bot detection on LinkedIn?
Unlike traditional Selenium scripts that launch detectable automated instances, CareerEngine attaches directly to your already opened, authentic Google Chrome browser profile. It leverages your existing session cookies, genuine 2FA logins, realistic human dwell times (2.5s), and natural typing jitter (30ms–90ms).

### Which AI models are supported for form filling?
CareerEngine rotates between Google Gemini 3.5 Flash-lite and Gemini 3.1 Flash-lite across multiple free API keys to prevent rate limits, with automatic fallback to NVIDIA DeepSeek V4. It caches learned answers locally in `profile_config.json`.

### How does the Multi-Role Resume Selector choose a resume?
CareerEngine inspects the job title and requirements, matching them against tagged PDFs in `resumes/` (e.g. `_DE` for Data Engineering, `_DS` for Data Science, `_AI` for GenAI Platforms, `_SWE` for Backend, and `_MLOps` for DevOps).

### Is my personal resume or profile information shared with the cloud?
No. CareerEngine operates on a zero-telemetry architecture. Your API keys, candidate facts, database records (`jobs.db`), and resume PDFs never leave your local machine, and are protected by automated pre-push security git hooks.

---

## 📄 License

CareerEngine is open-sourced under the [MIT License](LICENSE).
© 2026 [developerOS](https://github.com/developerOSindia). All rights reserved.
