"""
Salary & Offer Negotiation Copilot for CareerEngine.
Provides compensation benchmarking across global tech markets, percentile band estimation,
and tactical negotiation scripts for counter-offers, competing offer leverage, and total rewards trade-offs.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.config_loader import get_config
from ai.ai_solver import UnifiedAISolver


# Market compensation percentiles (Base CTC / Total Compensation)
# Rates: INR LPA for India, USD thousands for US Remote, EUR thousands for EU
MARKET_BENCHMARKS: Dict[str, Dict[str, Dict[str, int]]] = {
    "india_inr_lpa": {
        "junior": {"p25": 10, "p50": 16, "p75": 24, "p90": 32},
        "mid": {"p25": 18, "p50": 26, "p75": 36, "p90": 48},
        "senior": {"p25": 30, "p50": 42, "p75": 55, "p90": 70},
        "staff_lead": {"p25": 45, "p50": 60, "p75": 85, "p90": 120},
        "principal_director": {"p25": 70, "p50": 95, "p75": 130, "p90": 180}
    },
    "us_remote_usd_k": {
        "junior": {"p25": 90, "p50": 115, "p75": 140, "p90": 165},
        "mid": {"p25": 125, "p50": 155, "p75": 185, "p90": 220},
        "senior": {"p25": 160, "p50": 195, "p75": 240, "p90": 290},
        "staff_lead": {"p25": 210, "p50": 260, "p75": 320, "p90": 390},
        "principal_director": {"p25": 270, "p50": 340, "p75": 420, "p90": 550}
    },
    "eu_remote_eur_k": {
        "junior": {"p25": 45, "p50": 58, "p75": 70, "p90": 85},
        "mid": {"p25": 65, "p50": 80, "p75": 98, "p90": 115},
        "senior": {"p25": 85, "p50": 105, "p75": 130, "p90": 160},
        "staff_lead": {"p25": 110, "p50": 140, "p75": 175, "p90": 215},
        "principal_director": {"p25": 140, "p50": 180, "p75": 230, "p90": 290}
    }
}


@dataclass
class NegotiationStrategy:
    """Strategy package for a specific negotiation scenario."""
    scenario_title: str
    scenario_type: str  # counter_offer, competing_offer, total_rewards, anchor_early
    recommended_target: str
    rationale: str
    email_subject: str
    email_body: str
    phone_talking_points: List[str]
    leverage_points: List[str]
    caution_notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompensationReport:
    """Holistic compensation intelligence and negotiation playbook."""
    target_company: str
    target_title: str
    current_compensation: str
    offered_compensation: str
    currency: str
    seniority_level: str
    market_percentiles: Dict[str, int]
    target_recommendation: str
    strategies: List[NegotiationStrategy]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_company": self.target_company,
            "target_title": self.target_title,
            "current_compensation": self.current_compensation,
            "offered_compensation": self.offered_compensation,
            "currency": self.currency,
            "seniority_level": self.seniority_level,
            "market_percentiles": self.market_percentiles,
            "target_recommendation": self.target_recommendation,
            "strategies": [s.to_dict() for s in self.strategies],
            "generated_at": self.generated_at
        }


class SalaryNegotiator:
    """Analyzes compensation offers, computes market benchmarks, and formulates tactical negotiation plans."""

    def __init__(self, profile_data: Optional[Dict[str, Any]] = None):
        self.config = get_config()
        self.profile = profile_data or self.config.profile
        self.ai = UnifiedAISolver(self.profile)

    def infer_seniority(self, title: str, years_exp: int) -> str:
        """Determines seniority bracket from job title and candidate years of experience."""
        t = title.lower()
        if any(k in t for k in ["director", "vp", "head of", "principal"]):
            return "principal_director"
        if any(k in t for k in ["staff", "lead", "architect", "manager"]):
            return "staff_lead"
        if any(k in t for k in ["senior", "sr", "sr.", "iii", "expert"]):
            return "senior"
        if any(k in t for k in ["junior", "associate", "entry", "intern"]):
            return "junior"

        # Experience fallback
        if years_exp >= 10:
            return "staff_lead"
        if years_exp >= 5:
            return "senior"
        if years_exp >= 2:
            return "mid"
        return "junior"

    def get_market_benchmark(
        self,
        seniority: str,
        market: str = "india_inr_lpa"
    ) -> Dict[str, int]:
        """Fetches market percentile distribution."""
        market_data = MARKET_BENCHMARKS.get(market, MARKET_BENCHMARKS["india_inr_lpa"])
        return market_data.get(seniority, market_data["senior"])

    def analyze_and_plan(
        self,
        company: str,
        title: str,
        offered_comp: Optional[float] = None,
        current_comp: Optional[float] = None,
        market_region: str = "india_inr_lpa",
        competing_offer: Optional[str] = None
    ) -> CompensationReport:
        """Formulates comprehensive compensation intelligence and negotiation scripts."""
        work = self.profile.get("work_summary", {})
        personal = self.profile.get("personal_info", {})
        cand_name = personal.get("full_name", "Kalash Jindal")
        years_exp = int(work.get("total_years_experience", 5))

        clean_comp = company.strip() if company else "Target Company"
        clean_title = title.strip() if title else "Senior Engineer"

        # Fallbacks for compensation
        if current_comp is None:
            current_comp = float(work.get("current_salary_inr_lpa", 30))
        if offered_comp is None:
            offered_comp = float(work.get("expected_salary_inr_lpa", 40))

        seniority = self.infer_seniority(clean_title, years_exp)
        market_data = self.get_market_benchmark(seniority, market_region)

        currency_unit = "LPA (INR)" if "india" in market_region else "k USD" if "us" in market_region else "k EUR"

        # Recommended anchor: 15-20% above offer or 75th percentile of market
        target_num = max(offered_comp * 1.18, float(market_data.get("p75", 45)))
        target_str = f"{target_num:.1f} {currency_unit}"
        current_str = f"{current_comp:.1f} {currency_unit}"
        offered_str = f"{offered_comp:.1f} {currency_unit}"

        # Build 3 tactical negotiation strategies
        strategies = [
            self._build_counter_offer_strategy(
                cand_name=cand_name,
                company=clean_comp,
                title=clean_title,
                offered=offered_str,
                target=target_str,
                currency=currency_unit
            ),
            self._build_competing_offer_strategy(
                cand_name=cand_name,
                company=clean_comp,
                title=clean_title,
                offered=offered_str,
                target=target_str,
                competing_info=competing_offer or "an active competing offer in late stages"
            ),
            self._build_total_rewards_strategy(
                cand_name=cand_name,
                company=clean_comp,
                title=clean_title,
                offered=offered_str
            )
        ]

        return CompensationReport(
            target_company=clean_comp,
            target_title=clean_title,
            current_compensation=current_str,
            offered_compensation=offered_str,
            currency=currency_unit,
            seniority_level=seniority.replace("_", " ").title(),
            market_percentiles=market_data,
            target_recommendation=target_str,
            strategies=strategies
        )

    def _build_counter_offer_strategy(
        self,
        cand_name: str,
        company: str,
        title: str,
        offered: str,
        target: str,
        currency: str
    ) -> NegotiationStrategy:
        """Formulates a respectful, high-leverage counter-offer based on market alignment and value delivery."""
        subject = f"Follow-up on Offer & Next Steps - {title} - {cand_name}"
        body = (
            f"Dear {company} Team,\n\n"
            f"Thank you so much for extending the offer to join {company} as a {title}! "
            f"I truly enjoyed our conversations and came away genuinely excited about the problems the engineering team is solving.\n\n"
            f"I've had the chance to review the details of the offer ({offered}). Based on the scope of the role, "
            f"my background delivering high-throughput production systems, and current market benchmarks for this seniority, "
            f"I was targeting a total compensation closer to {target}.\n\n"
            f"If we are able to reach {target}, I would be ready to accept immediately, conclude my other ongoing conversations, "
            f"and start making an impact with the team on day one.\n\n"
            f"I look forward to your thoughts and would be happy to hop on a brief call if helpful.\n\n"
            f"Best regards,\n{cand_name}"
        )

        talking_points = [
            f"Start with genuine enthusiasm: 'I want to reiterate how excited I am about the team and role.'",
            f"Anchor to market value: 'Looking at peer benchmarks and the technical ownership expected, {target} is where I see the match.'",
            f"Signal immediate close: 'If we can solve this, I will sign today and withdraw from all other interview loops.'",
            "Listen silently after stating your number — do not negotiate against yourself."
        ]

        leverage = [
            "Demonstrated track record of delivering revenue-critical or cost-saving engineering projects.",
            "Short notice period enabling fast onboarding.",
            "Strong cultural and technical alignment established across interviews."
        ]

        caution = [
            "Never issue an ultimatum or aggressive deadline unless you genuinely have an expiring competing offer.",
            "Avoid sharing personal expense reasons (e.g. rent or personal bills); keep it strictly about market value."
        ]

        return NegotiationStrategy(
            scenario_title="Tactical Counter-Offer (Market Value Anchor)",
            scenario_type="counter_offer",
            recommended_target=target,
            rationale=f"Anchors at market P75 ({target}) with an immediate commitment to sign upon agreement.",
            email_subject=subject,
            email_body=body,
            phone_talking_points=talking_points,
            leverage_points=leverage,
            caution_notes=caution
        )

    def _build_competing_offer_strategy(
        self,
        cand_name: str,
        company: str,
        title: str,
        offered: str,
        target: str,
        competing_info: str
    ) -> NegotiationStrategy:
        """Leverages competing opportunities without hostility or ultimatums."""
        subject = f"Timeline Update & Offer Review - {title} - {cand_name}"
        body = (
            f"Dear {company} Team,\n\n"
            f"Thank you again for the offer for the {title} role. As mentioned earlier, {company} remains my top choice "
            f"because of the engineering culture and technical challenges we discussed.\n\n"
            f"In the spirit of complete transparency, I have received {competing_info} that is positioned at a higher compensation band. "
            f"However, because I strongly prefer the mission and team at {company}, I want to see if we can close the gap towards {target}.\n\n"
            f"If we can align around this figure, I am prepared to decline the other opportunity and sign with {company} without delay.\n\n"
            f"Could we schedule a quick 10-minute check-in today or tomorrow to finalize this?\n\n"
            f"Warmly,\n{cand_name}"
        )

        talking_points = [
            f"Affirm top-choice preference: '{company} is where I want to build, but the delta is significant enough to pause.'",
            f"Provide decision clarity: 'Give me confidence on {target}, and I will immediately decline the other offer.'",
            "Show flexibility on compensation structure (base vs signing bonus vs equity)."
        ]

        leverage = [
            "Multi-company validation of candidate market demand.",
            "Short decision timeline that creates natural urgency for the recruiter."
        ]

        caution = [
            "Never bluff a non-existent offer; recruiters often ask for confirmation or role details.",
            "Always emphasize that this company is your first choice."
        ]

        return NegotiationStrategy(
            scenario_title="Competing Offer Leverage",
            scenario_type="competing_offer",
            recommended_target=target,
            rationale="Leverages outside market interest to justify moving above the initial offer band.",
            email_subject=subject,
            email_body=body,
            phone_talking_points=talking_points,
            leverage_points=leverage,
            caution_notes=caution
        )

    def _build_total_rewards_strategy(
        self,
        cand_name: str,
        company: str,
        title: str,
        offered: str
    ) -> NegotiationStrategy:
        """Pivots to non-base rewards (signing bonus, equity, remote days) when base salary bands are capped."""
        subject = f"Exploring Total Rewards Components - {title} - {cand_name}"
        body = (
            f"Dear {company} Team,\n\n"
            f"I understand that internal compensation bands for base salary at this level may have constraints. "
            f"Since I am very eager to join {company}, I would love to explore whether there is flexibility across other components of the package.\n\n"
            f"Specifically, could we look into:\n"
            f"1. A one-time Signing / Joining Bonus to bridge the first-year compensation gap.\n"
            f"2. Additional equity / ESOP allocation or an accelerated 6-month performance review cycle.\n"
            f"3. Flexibility on remote working arrangement or home office setup stipend.\n\n"
            f"Any of these levers would make it very easy for me to move forward with enthusiasm. Let me know your thoughts!\n\n"
            f"Best regards,\n{cand_name}"
        )

        talking_points = [
            "Acknowledge base band limitations respectfully without accepting a discount on total value.",
            "Propose joining bonus as a win-win: doesn't disrupt internal team equity.",
            "Ask about performance-linked bonus or accelerated review timelines."
        ]

        leverage = [
            "Signing bonuses are one-off budget items that recruiters have more discretionary power to approve.",
            "Demonstrates commercial maturity and practical collaboration."
        ]

        caution = [
            "Ensure verbal promises regarding accelerated reviews or bonus payouts are documented in the formal offer letter."
        ]

        return NegotiationStrategy(
            scenario_title="Total Rewards & Flexibility Pivot",
            scenario_type="total_rewards",
            recommended_target=offered,
            rationale="Captures financial value through signing bonuses, equity, or perks when base salary bands are rigid.",
            email_subject=subject,
            email_body=body,
            phone_talking_points=talking_points,
            leverage_points=leverage,
            caution_notes=caution
        )
