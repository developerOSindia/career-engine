# 🎯 Career Automator: Autonomous Multi-Platform Job Application & Recruiter Agent

An intelligent, human-stealth career automation agent designed to autonomously search and apply for target engineering positions on LinkedIn (and expand to Naukri, Wellfound, and Indeed), solve screening questionnaires via rotational Gemini 3.x Flash-lite and DeepSeek AI models, and automatically scan and draft personalized, high-converting replies to recruiter InMails.

Built specifically for high-impact Data Engineering, Distributed Systems, MLOps, and AI platform roles.

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
resume/
├── .env                              # Private API keys and local configuration (GITIGNORED)
├── .env.example                      # Public template for environment variables
├── .gitignore                        # Git exclusion rules (protects credentials and databases)
├── config.yaml                       # Application settings, keywords, and search preferences
├── profile_config.json               # Candidate master profile facts & learned memory
├── main.py                           # Unified CLI entrypoint (apply, inmail, status)
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
│   ├── naukri/                       # Scaffolded connector for Naukri.com
│   ├── wellfound/                    # Scaffolded connector for Wellfound / AngelList
│   └── indeed/                       # Scaffolded connector for Indeed Apply
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
git clone <your-repo-url>
cd resume

# Install required Python packages
pip install -r requirements.txt
```

### 2. Interactive Profile & Secrets Setup Agent
Run the interactive CareerOS Setup Agent to automatically configure your profile, resume, search keywords, and API keys:
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
📊 CareerOS - Application Status Dashboard
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

## 👤 Candidate Profile & Customization

The candidate facts used to answer form questions and compose recruiter messages are defined in [`profile_config.json`](profile_config.json):

| Metric / Fact | Value | Rules Enforced |
|---|---|---|
| **Total Experience** | 5 years | Strictly 5 years (excluding internships) |
| **Current Role** | Senior Data Engineer @ Nasdaq | Verified Nasdaq experience |
| **Current CTC** | 30 LPA | 24 LPA Fixed + 6 LPA Variable/Benefits |
| **Expected CTC** | 40 LPA | Precedence given over fixed base |
| **Notice Period** | 30 days | Official 60 days, negotiable to 30 days |
| **Core Technical Skills** | Python, PySpark, Databricks, AWS, Delta Lake, SQL, MLOps, AI | 5 years each |
| **Location Authorization** | Bengaluru, India | Legally authorized to work, No visa sponsorship needed |

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

## 📄 License
Private & Confidential. Created for personal career management.
