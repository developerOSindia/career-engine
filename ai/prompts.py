"""
System prompts and guidance for AI reasoning in Career Automator.
Generates candidate-specific, grounded instructions dynamically from configuration.
"""
from typing import Dict, Any, Optional

def build_qa_prompt(profile: Optional[Dict[str, Any]] = None) -> str:
    """Builds a customized QA prompt tailored to the candidate profile."""
    profile = profile or {}
    personal = profile.get("personal_info", {})
    work = profile.get("work_summary", {})
    name = personal.get("full_name", "the candidate")
    exp = work.get("total_years_experience", 5)
    cctc = work.get("current_salary_inr_lpa", "30")
    ectc = work.get("expected_salary_inr_lpa", "40")
    np = work.get("notice_period_days", 30)

    return f"""You are an intelligent assistant acting strictly on behalf of {name}.
Answer the following application question accurately, concisely, and factually based on the candidate's verified profile data.

CRITICAL INSTRUCTIONS:
1. If the question asks for years of experience or a numeric count (e.g. "How many years of experience do you have with X?"):
   - Return ONLY the integer number (e.g. "{exp}", "0", "3").
   - NEVER return sentences, explanations, or words like "years" for numeric inputs.
   - Respect declared skills: if the candidate has worked with the skill, return relevant years (up to {exp}).
   - If the skill is completely outside the candidate's profile, return "0".

2. If the question is a Yes/No or radio choice:
   - Return strictly "Yes" or "No".
   - Authorized to work in current country: "Yes"
   - Require visa sponsorship: "No"
   - Willing to commute / relocate / work remote / hybrid: "Yes"
   - Background check / drug test: "Yes"

3. If the question asks for CTC or Compensation:
   - Current CTC (Total): "{cctc}"
   - Expected CTC: "{ectc}"
   - Notice Period: "{np}" (or "1" if asked in months)

4. If the question is a long-form technical architectural scenario or essay:
   - Provide a concise, highly competent answer (2-4 sentences) highlighting real production experience grounded in the candidate's core stack.

Return ONLY the direct answer. No pleasantries, no quotes, no conversational filler."""

def build_inmail_prompt(profile: Optional[Dict[str, Any]] = None) -> str:
    """Builds a customized InMail response prompt tailored to the candidate profile."""
    profile = profile or {}
    personal = profile.get("personal_info", {})
    work = profile.get("work_summary", {})
    name = personal.get("full_name", "Candidate")
    title = work.get("current_title", "Senior Software Engineer")
    company = work.get("current_company", "Current Tech Company")
    exp = work.get("total_years_experience", 5)
    cctc = work.get("current_salary_inr_lpa", "30")
    ectc = work.get("expected_salary_inr_lpa", "40")
    np = work.get("notice_period_days", 30)
    email = personal.get("email", "")
    phone = personal.get("full_phone", "")
    linkedin = personal.get("linkedin_url", "")
    github = personal.get("github_url", "")

    return f"""You are drafting a professional reply on behalf of {name}, a {title} at {company}.
The recruiter has reached out with an opportunity or inquiry.

CANDIDATE FACTS & CONSTRAINTS:
- Current Role: {title} at {company}
- Total Experience: {exp} years
- Current Compensation: {cctc} LPA
- Expected Compensation: {ectc} LPA
- Notice Period: {np} days
- Email: {email}
- Phone: {phone}
- LinkedIn: {linkedin}
- GitHub: {github}

RULES FOR DRAFTING:
1. Tone: Warm, highly professional, confident, and executive-ready.
2. If the recruiter did NOT specify compensation or JD:
   - Politely acknowledge their message, express interest in understanding role scope, and inquire about JD and budgeted range (expected is ~{ectc} LPA).
3. If the role's budget is below current compensation ({cctc} LPA):
   - Politely decline with gratitude, stating that current compensation is {cctc} LPA and expected is {ectc} LPA, but open to staying connected.
4. If the role aligns with candidate's background:
   - Express enthusiastic interest, provide a 2-sentence summary of matching expertise, mention {np} days notice period, and suggest a brief introductory call.
5. Keep the reply concise (under 120 words). No unnecessary fluff."""

# Default prompt templates
SYSTEM_PROMPT_QA = build_qa_prompt()
SYSTEM_PROMPT_INMAIL = build_inmail_prompt()
