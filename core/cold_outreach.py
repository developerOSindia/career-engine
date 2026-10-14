"""
CareerEngine Recruiter Cold Outreach & Direct Contact Discovery.
Synthesizes Boolean X-Ray search queries, corporate email permutations,
and 3 high-converting outreach message frameworks with 1-click mailto launch.
"""

import re
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from core.config_loader import get_config
from ai.ai_solver import UnifiedAISolver

@dataclass
class RecruiterOutreachKit:
    company: str
    job_title: str
    predicted_domain: str
    email_patterns: List[Dict[str, str]]
    linkedin_search_url: str
    google_xray_search_url: str
    templates: Dict[str, Dict[str, str]]

    @property
    def target_role(self) -> str:
        return self.job_title

    @property
    def email_permutations(self) -> List[str]:
        return [p.get("pattern", "") for p in self.email_patterns]

    @property
    def email_frameworks(self) -> List[Dict[str, str]]:
        frameworks = []
        for val in self.templates.values():
            item = dict(val)
            if "mailto" in item and "mailto_link" not in item:
                item["mailto_link"] = item["mailto"]
            frameworks.append(item)
        return frameworks

    @property
    def talent_discovery_queries(self) -> List[Dict[str, str]]:
        return [
            {
                "channel": "LinkedIn Talent Search",
                "label": "Direct Recruiter Search",
                "search_url": self.linkedin_search_url,
                "query": f"recruiter {self.company}"
            },
            {
                "channel": "Google X-Ray (LinkedIn)",
                "label": "Precision Boolean Talent X-Ray",
                "search_url": self.google_xray_search_url,
                "query": f'site:linkedin.com/in ("Technical Recruiter" OR "Talent Acquisition") "{self.company}"'
            }
        ]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["target_role"] = self.target_role
        d["email_permutations"] = self.email_permutations
        d["email_frameworks"] = self.email_frameworks
        d["talent_discovery_queries"] = self.talent_discovery_queries
        return d


class ColdOutreachSynthesizer:
    """Generates direct recruiter outreach kits and contact intelligence."""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.profile = self.config.profile
        self.ai = UnifiedAISolver()

    def predict_company_domain(self, company: str) -> str:
        """Derives primary corporate domain from company name."""
        return self._predict_domain(company)

    def _predict_domain(self, company: str) -> str:
        """Derives primary corporate domain from company name."""
        clean = re.sub(r"[^\w\s]", "", company.lower())
        words = clean.split()
        if not words:
            return "company.com"
        # Take first meaningful word or combined
        token = words[0]
        common_exceptions = {
            "meta": "meta.com",
            "facebook": "meta.com",
            "google": "google.com",
            "alphabet": "google.com",
            "amazon": "amazon.com",
            "apple": "apple.com",
            "netflix": "netflix.com",
            "microsoft": "microsoft.com",
            "stripe": "stripe.com",
            "databricks": "databricks.com",
            "snowflake": "snowflake.com",
            "epam": "epam.com"
        }
        return common_exceptions.get(token, f"{token}.com")

    def generate_email_permutations(self, name: str, domain: str) -> List[str]:
        """Generates common corporate email permutations for a specific person."""
        parts = re.sub(r"[^\w\s]", "", name.lower()).split()
        first = parts[0] if parts else "john"
        last = parts[1] if len(parts) > 1 else "doe"
        return [
            f"{first}.{last}@{domain}",
            f"{first[0]}.{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}@{domain}",
            f"{last}@{domain}"
        ]

    def _generate_email_patterns(self, domain: str) -> List[Dict[str, str]]:
        """Generates common corporate email permutations."""
        return [
            {"pattern": "first.last@" + domain, "example": f"john.doe@{domain}", "confidence": "High (Tech Standard)"},
            {"pattern": "first@" + domain, "example": f"john@{domain}", "confidence": "Medium (Startups/Mid-market)"},
            {"pattern": "f.last@" + domain, "example": f"j.doe@{domain}", "confidence": "Medium (Enterprise Standard)"},
            {"pattern": "firstlast@" + domain, "example": f"johndoe@{domain}", "confidence": "Low (Legacy Systems)"}
        ]

    def generate_talent_discovery_queries(self, company: str, job_title: str) -> List[Dict[str, str]]:
        """Constructs precision Boolean X-Ray discovery queries as a list of dicts."""
        g_url, l_url = self._build_search_urls(company, job_title)
        clean_comp = re.sub(r"[^\w\s]", "", company).strip()
        return [
            {"channel": "LinkedIn Talent Search", "label": "Direct Recruiter Search", "search_url": l_url, "query": f"recruiter {clean_comp}"},
            {"channel": "Google X-Ray (LinkedIn)", "label": "Precision Boolean Talent X-Ray", "search_url": g_url, "query": f'site:linkedin.com/in ("Technical Recruiter" OR "Talent Acquisition") "{clean_comp}"'},
            {"channel": "Engineering Leadership", "label": "Hiring Managers", "search_url": f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote_plus(f'{clean_comp} Engineering Manager')}", "query": f"{clean_comp} Engineering Manager"}
        ]

    def _build_search_urls(self, company: str, job_title: str) -> Tuple[str, str]:
        """Constructs precision Boolean X-Ray discovery queries."""
        clean_comp = re.sub(r"[^\w\s]", "", company).strip()
        google_query = f'site:linkedin.com/in ("Technical Recruiter" OR "Talent Acquisition" OR "Engineering Manager") "{clean_comp}"'
        google_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(google_query)}"
        linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote_plus(f'recruiter {clean_comp}')}"
        return google_url, linkedin_url

    def generate_outreach_kit(
        self,
        company: str,
        job_title: str = "Senior Software Engineer",
        target_name: Optional[str] = None
    ) -> RecruiterOutreachKit:
        """Synthesizes the complete recruiter outreach package."""
        domain = self._predict_domain(company)
        email_patterns = self._generate_email_patterns(domain)
        google_url, linkedin_url = self._build_search_urls(company, job_title)

        candidate_name = self.profile.get("personal_information", {}).get("name", "Kalash Jindal")
        years_exp = self.profile.get("years_of_experience", 5)
        notice_period = self.profile.get("notice_period_days", 60)
        skills = list(self.profile.get("skills_years_experience", {}).keys())[:4]
        skills_str = ", ".join([s.title() for s in skills]) if skills else "Python, AWS, Distributed Systems"
        greeting = f"Hi {target_name}," if target_name else "Hi there,"

        # 1. The Value Hook Template
        subject_1 = f"{job_title} | {candidate_name} ({years_exp}y Exp in {skills[0].title() if skills else 'Backend'})"
        body_1 = f"""{greeting}

I noticed {company} is scaling its engineering team for the {job_title} role. With over {years_exp} years architecting high-throughput systems and data pipelines at enterprise scale (including Nasdaq), I specialize in {skills_str}.

I've already submitted my application through your careers portal, but wanted to reach out directly to highlight:
• Engineered high-scale pipelines processing 100M+ events/day with 99.99% reliability
• Deep hands-on proficiency with {skills_str}
• Confirmed {notice_period}-day notice period and ready to transition smoothly

I'd welcome 10 minutes to discuss how my background aligns with your team's immediate roadmaps.

Best regards,
{candidate_name}
LinkedIn: linkedin.com/in/kalashjindal
GitHub: github.com/developerOSindia"""

        mailto_1 = f"mailto:?subject={urllib.parse.quote(subject_1)}&body={urllib.parse.quote(body_1)}"

        # 2. The Fast Track (Notice Period & Compensation Fit)
        subject_2 = f"Application: {job_title} - {candidate_name} ({notice_period}-day notice)"
        body_2 = f"""{greeting}

I recently applied for the {job_title} role at {company}. Given how fast-paced your hiring is, here is a quick 3-point snapshot of my profile:

1. Technical Stack: {skills_str}
2. Proven Scale: {years_exp}+ years building resilient, distributed microservices and ETL architectures
3. Availability: Confirmed {notice_period}-day notice period with transparent compensation alignment

Would you have 5 minutes this week for a brief introductory conversation?

Warm regards,
{candidate_name}
Portfolio: developeros.in"""

        mailto_2 = f"mailto:?subject={urllib.parse.quote(subject_2)}&body={urllib.parse.quote(body_2)}"

        # 3. The 48-Hour Application Follow-Up
        subject_3 = f"Following up on application: {job_title} @ {company}"
        body_3 = f"""{greeting}

I hope you're having a productive week.

I submitted my application for the {job_title} position at {company} earlier this week and wanted to confirm receipt. My experience scaling distributed architectures with {skills_str} directly matches the requirements outlined in the job description.

I have attached my tailored resume for your review and would love to connect whenever convenient.

Thank you for your time and consideration!

Sincerely,
{candidate_name}"""

        mailto_3 = f"mailto:?subject={urllib.parse.quote(subject_3)}&body={urllib.parse.quote(body_3)}"

        templates = {
            "value_hook": {"name": "The Value Hook", "subject": subject_1, "body": body_1, "mailto": mailto_1},
            "fast_track": {"name": "The Fast Track Snapshot", "subject": subject_2, "body": body_2, "mailto": mailto_2},
            "followup": {"name": "48-Hour Application Follow-Up", "subject": subject_3, "body": body_3, "mailto": mailto_3}
        }

        return RecruiterOutreachKit(
            company=company,
            job_title=job_title,
            predicted_domain=domain,
            email_patterns=email_patterns,
            linkedin_search_url=linkedin_url,
            google_xray_search_url=google_url,
            templates=templates
        )

    def format_cli_outreach(self, kit: RecruiterOutreachKit) -> str:
        """Renders rich terminal card for recruiter outreach."""
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RESET = "\033[0m"

        lines = []
        lines.append(f"\n{BOLD}{'='*68}{RESET}")
        lines.append(f"{CYAN}{BOLD}  📬 CAREERENGINE RECRUITER COLD OUTREACH & DISCOVERY{RESET}")
        lines.append(f"{BOLD}{'='*68}{RESET}\n")

        lines.append(f"  {BOLD}Target Opportunity:{RESET}  {kit.job_title} @ {GREEN}{kit.company}{RESET}")
        lines.append(f"  {BOLD}Predicted Domain:{RESET}    {kit.predicted_domain}\n")

        lines.append(f"  {BOLD}🔍 Contact Discovery Queries:{RESET}")
        lines.append(f"    • Google X-Ray Search:  {CYAN}{kit.google_xray_search_url}{RESET}")
        lines.append(f"    • LinkedIn Recruiter:   {CYAN}{kit.linkedin_search_url}{RESET}\n")

        lines.append(f"  {BOLD}📧 Corporate Email Permutations:{RESET}")
        for p in kit.email_patterns:
            lines.append(f"    • {p['example']:<26} [{p['confidence']}]")

        lines.append(f"\n  {BOLD}📝 Outreach Templates Generated (3 Frameworks):{RESET}")
        for key, tmpl in kit.templates.items():
            lines.append(f"\n  {YELLOW}{BOLD}[{tmpl['name']}]{RESET}")
            lines.append(f"  Subject: {tmpl['subject']}")
            lines.append(f"  Body Preview:\n    " + tmpl['body'].replace('\n', '\n    ')[:200] + "...")

        lines.append(f"\n{BOLD}{'='*68}{RESET}\n")
        return "\n".join(lines)

cold_outreach_synthesizer = ColdOutreachSynthesizer()
