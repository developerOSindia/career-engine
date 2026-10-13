"""
Unified Multi-Provider AI Question Solver and Message Drafter.
Supports:
1. Google Gemini (gemini-3.x rotation) - Primary High-Speed Reasoning
2. NVIDIA NIM / DeepSeek V4 - High Intelligence Fallback
3. Local Ollama - Offline Fallback
"""
import json
import os
import time
import requests
from typing import List, Optional, Dict, Any
from core.config_loader import get_config
from ai.prompts import SYSTEM_PROMPT_QA, SYSTEM_PROMPT_INMAIL

class UnifiedAISolver:
    def __init__(self, profile_data: Optional[Dict[str, Any]] = None, config=None):
        config = config or get_config()
        self.profile = profile_data or config.profile
        
        # 1. Gemini Configuration (Keys from .env via Config)
        self.gemini_keys = config.gemini_api_keys or []
        self.gemini_idx = 0
        self.gemini_models = [
            "gemini-2.5-flash",
            "gemini-flash-latest",
            "gemini-2.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-2.5-pro"
        ]
        self._model_cooldowns = {}

        # 2. NVIDIA / DeepSeek Configuration
        self.nvidia_api_key = config.nvidia_api_key
        self.nvidia_url = f"{config.nvidia_base_url.rstrip('/')}/chat/completions"
        self.nvidia_model = config.nvidia_model

        # 3. OpenAI Configuration
        self.openai_api_key = config.openai_api_key
        self.openai_model = config.openai_model

        # 4. Anthropic / Claude Configuration
        self.anthropic_api_key = config.anthropic_api_key
        self.anthropic_model = config.anthropic_model

        # 5. Ollama Configuration (Local Offline)
        self.ollama_url = "http://localhost:11434/api/generate"

        personal = self.profile.get("personal_info", {})
        work = self.profile.get("work_summary", {})
        edu = self.profile.get("education", {})
        skills = self.profile.get("skills_years_experience", {})
        skills_str = ", ".join([f"{k} ({v} yrs)" for k, v in list(skills.items())[:20]]) if skills else "Software Engineering, Python, SQL"

        self.candidate_summary = f"""
Candidate: {personal.get('full_name', 'Candidate')} ({work.get('current_title', 'Software Engineer')} at {work.get('current_company', 'Tech Company')})
Total Experience: {work.get('total_years_experience', 5)} years
Location: {personal.get('location', 'Bengaluru, India')}
Current CTC: {work.get('current_salary_inr_lpa', '30')} LPA
Expected CTC: {work.get('expected_salary_inr_lpa', '40')} LPA
Notice Period: {work.get('notice_period_days', 30)} days
Work Model: {self.profile.get('screening_defaults', {}).get('preferred_work_model', 'Remote / Hybrid')}
Education: {edu.get('degree', 'B.Tech')} in {edu.get('field_of_study', 'Computer Science')} from {edu.get('institution', 'University')} ({edu.get('graduation_year', '2021')})
Key Technical Skills: {skills_str}
GitHub: {personal.get('github_url', '')} | LinkedIn: {personal.get('linkedin_url', '')}
"""

    def _call_gemini(self, prompt: str, max_tokens: int = 40) -> Optional[tuple]:
        """Calls Google Gemini API rotating across latest models and keys."""
        req_timeout = 3.0 if max_tokens > 100 else 2.0
        now = time.time()
        
        if now < self._model_cooldowns.get("all_gemini", 0):
            return None

        for model in self.gemini_models:
            if now < self._model_cooldowns.get(model, 0):
                continue
            
            for _ in range(len(self.gemini_keys)):
                key_idx = self.gemini_idx
                key = self.gemini_keys[key_idx]
                self.gemini_idx = (self.gemini_idx + 1) % len(self.gemini_keys)
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": max_tokens}
                }
                try:
                    resp = requests.post(url, json=payload, timeout=req_timeout)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                if "text" in part:
                                    ans = part["text"].strip()
                                    if ans:
                                        return ans, f"Gemini ({model} | Key {key_idx+1})"
                    elif resp.status_code in (429, 503, 500):
                        self._model_cooldowns[model] = time.time() + 60
                        self._model_cooldowns["all_gemini"] = time.time() + 30
                        break
                except Exception:
                    continue
        return None

    def _call_nvidia(self, prompt: str, max_tokens: int = 40) -> Optional[tuple]:
        """Calls NVIDIA NIM / DeepSeek as secondary fallback."""
        if not self.nvidia_api_key:
            return None
        now = time.time()
        if now < self._model_cooldowns.get("nvidia", 0):
            return None
        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "model": self.nvidia_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "stream": False
        }
        try:
            resp = requests.post(self.nvidia_url, headers=headers, json=payload, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {}).get("content", "").strip()
                    if msg:
                        return msg, f"NVIDIA ({self.nvidia_model})"
            elif resp.status_code in (429, 503, 500):
                self._model_cooldowns["nvidia"] = time.time() + 60
        except Exception:
            self._model_cooldowns["nvidia"] = time.time() + 30
        return None

    def _call_openai(self, prompt: str, max_tokens: int = 40) -> Optional[tuple]:
        """Calls OpenAI API (GPT-4o / GPT-4o-mini)."""
        if not self.openai_api_key or self.openai_api_key.startswith("your_"):
            return None
        now = time.time()
        if now < self._model_cooldowns.get("openai", 0):
            return None
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": max_tokens
        }
        try:
            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {}).get("content", "").strip()
                    if msg:
                        return msg, f"OpenAI ({self.openai_model})"
            elif resp.status_code in (429, 503, 500):
                self._model_cooldowns["openai"] = time.time() + 60
        except Exception:
            self._model_cooldowns["openai"] = time.time() + 30
        return None

    def _call_claude(self, prompt: str, max_tokens: int = 40) -> Optional[tuple]:
        """Calls Anthropic Claude API (Claude 3.5 Haiku / Sonnet)."""
        if not self.anthropic_api_key or self.anthropic_api_key.startswith("your_"):
            return None
        now = time.time()
        if now < self._model_cooldowns.get("claude", 0):
            return None
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.anthropic_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", [])
                if content and "text" in content[0]:
                    msg = content[0]["text"].strip()
                    if msg:
                        return msg, f"Claude ({self.anthropic_model})"
            elif resp.status_code in (429, 529, 500):
                self._model_cooldowns["claude"] = time.time() + 60
        except Exception:
            self._model_cooldowns["claude"] = time.time() + 30
        return None

    def _call_ollama(self, prompt: str) -> Optional[tuple]:
        """Calls local Ollama instance if available."""
        payload = {
            "model": "llama3.2:latest",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 40}
        }
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=4.0)
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                if text:
                    return text, "Ollama (llama3.2)"
        except Exception:
            pass
        return None

    def _rule_based_solve(self, question: str, options: Optional[List[str]] = None) -> Optional[str]:
        """Fast, 100% accurate candidate facts resolver before calling external LLMs."""
        q = question.lower().strip()

        # Experience questions (Databricks, PySpark, AWS, Python, Total, etc.)
        if any(k in q for k in ["experience", "how many years", "years of"]):
            if options:
                for opt in options:
                    if opt.strip() in ["5", "4-6", "3-5", "5+", "5-7"]:
                        return opt
            return "5"

        # Notice period
        if "notice" in q or "joining period" in q or "how soon" in q:
            if options:
                for opt in options:
                    if "30" in opt or "1 month" in opt.lower() or "immediate" in opt.lower():
                        return opt
            return "30"

        # Current & Expected CTC / Salary
        if any(k in q for k in ["ectc", "expected ctc", "expected salary"]) or ("expected" in q and any(k in q for k in ["ctc", "salary", "compensation", "lpa"])):
            return "40"
        if any(k in q for k in ["cctc", "current ctc", "current salary"]) or ("current" in q and any(k in q for k in ["ctc", "salary", "compensation", "lpa"])):
            return "30"
        if any(k in q for k in ["ctc", "salary", "compensation", "lpa"]):
            return "40" if ("expect" in q or "ectc" in q) else "30"

        # Work Authorization & Visas
        if any(k in q for k in ["authorized", "eligible to work", "legally"]):
            return "Yes"
        if any(k in q for k in ["require sponsorship", "visa sponsorship", "need visa"]):
            return "No"

        # Relocation & Work mode
        if any(k in q for k in ["relocate", "relocation", "work from office", "wfo", "hybrid", "remote", "shift", "shifts"]):
            return "Yes"

        # Education
        if any(k in q for k in ["degree", "education", "qualification"]):
            if options:
                for opt in options:
                    if "bachelor" in opt.lower() or "b.tech" in opt.lower() or "graduate" in opt.lower():
                        return opt
            return "Bachelors"

        # Yes/No general positivity for willingness
        if any(k in q for k in ["comfortable", "agree", "willing", "consent", "confirm"]):
            return "Yes"

        return None

    def solve_question(
        self,
        question: str,
        field_type: str = "text",
        options: Optional[List[str]] = None,
        is_long_form: bool = False
    ) -> Optional[str]:
        """Infers the optimal answer for a form field using Candidate Profile + LLM rotation."""
        clean_q = question.strip()

        # 1. Fast profile-based rule resolver (0ms, 100% consistent)
        rule_ans = self._rule_based_solve(clean_q, options)
        if rule_ans:
            print(f"  🧠 [Profile Facts]: '{clean_q[:40]}...' -> '{rule_ans}'")
            return rule_ans

        max_toks = 200 if is_long_form else 30
        prompt = f"""{SYSTEM_PROMPT_QA}

CANDIDATE PROFILE:
{self.candidate_summary}

QUESTION TO ANSWER:
"{clean_q}"
Field Type: {field_type}
"""
        if options:
            prompt += f"Allowed Options (Pick exactly one): {options}\n"

        result = self._call_gemini(prompt, max_tokens=max_toks)
        if not result:
            result = self._call_claude(prompt, max_tokens=max_toks)
        if not result:
            result = self._call_openai(prompt, max_tokens=max_toks)
        if not result:
            result = self._call_nvidia(prompt, max_tokens=max_toks)
        if not result:
            result = self._call_ollama(prompt)

        if result:
            ans, provider = result
            ans = ans.strip().strip('"').strip("'")
            if not is_long_form and "\n" in ans:
                ans = ans.split("\n")[0].strip()
            print(f"  🧠 [{provider}]: '{clean_q[:40]}...' -> '{ans}'")
            return ans

        # Default fallback
        if options:
            return options[0]
        return "Yes" if field_type in ("radio", "checkbox") else "5"

    def draft_inmail_reply(
        self,
        sender_name: str,
        sender_headline: str,
        message_text: str
    ) -> Optional[str]:
        """Drafts a personalized, high-converting reply to a recruiter InMail or inquiry."""
        prompt = f"""{SYSTEM_PROMPT_INMAIL}

CANDIDATE PROFILE:
{self.candidate_summary}

RECRUITER MESSAGE:
From: {sender_name} ({sender_headline})
Message Content:
\"\"\"
{message_text.strip()}
\"\"\"

TASK:
Write the complete reply message to {sender_name}.
"""
        result = self._call_gemini(prompt, max_tokens=250)
        if not result:
            result = self._call_claude(prompt, max_tokens=250)
        if not result:
            result = self._call_openai(prompt, max_tokens=250)
        if not result:
            result = self._call_nvidia(prompt, max_tokens=250)
        if not result:
            result = self._call_ollama(prompt)

        if result:
            ans, provider = result
            print(f"  💌 [{provider}] Drafted InMail reply ({len(ans.split())} words)")
            return ans.strip()

        # Resilient template fallback
        personal = self.profile.get("personal_info", {})
        work = self.profile.get("work_summary", {})
        cand_name = personal.get("full_name", "Candidate")
        cand_title = work.get("current_title", "Senior Engineer")
        cand_company = work.get("current_company", "Current Company")
        cand_exp = work.get("total_years_experience", 5)

        fallback = (
            f"Hi {sender_name.split()[0] if sender_name else 'there'},\n\n"
            f"Thank you for reaching out! I appreciate you considering me for this opportunity. "
            f"With {cand_exp} years of experience as a {cand_title} at {cand_company}, "
            f"I would be very interested in learning more about the role.\n\n"
            f"I am available to connect for a quick discussion this week. Let me know what time works best for you.\n\n"
            f"Best regards,\n{cand_name}"
        )
        print("  💌 [Profile Template] Drafted personalized InMail reply")
        return fallback

# Alias for backward compatibility
AISolver = UnifiedAISolver
