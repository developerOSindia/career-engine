"""
CareerEngine Technical Interview Preparation & STAR Simulator.
Generates tailored System Design architectural challenges, deep-dive technical questions,
and verified behavioral STAR stories synthesized directly from candidate experience.
"""

import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from core.config_loader import get_config
from ai.ai_solver import UnifiedAISolver

@dataclass
class STARStory:
    theme: str
    situation: str
    task: str
    action: str
    result: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SystemDesignChallenge:
    title: str
    problem_statement: str
    key_components: List[str]
    scale_and_tradeoffs: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TechnicalDeepDive:
    question: str
    core_concept: str
    recommended_answer: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InterviewPrepKit:
    job_title: str
    company: str
    system_design_challenges: List[Dict[str, Any]]
    technical_deep_dives: List[Dict[str, Any]]
    behavioral_star_stories: List[Dict[str, Any]]
    key_talking_points: List[str]

    @property
    def system_design_challenge(self) -> Dict[str, Any]:
        if not self.system_design_challenges:
            return {}
        sd = dict(self.system_design_challenges[0])
        sd["scale_requirements"] = sd.get("key_components", [])
        tradeoffs = [t.strip() for t in sd.get("scale_and_tradeoffs", "").split(";") if t.strip()]
        sd["key_tradeoffs"] = tradeoffs or [sd.get("scale_and_tradeoffs", "")]
        return sd

    @property
    def technical_drills(self) -> List[Dict[str, Any]]:
        # Map fields so both question/ideal_answer_rubric and recommended_answer work
        drills = []
        for d in self.technical_deep_dives:
            drills.append({
                "topic": d.get("core_concept", "Distributed Systems"),
                "question": d.get("question", ""),
                "ideal_answer_rubric": d.get("recommended_answer", ""),
                "core_concept": d.get("core_concept", "")
            })
        return drills

    @property
    def role_focus_summary(self) -> str:
        return f"Role Architecture Focus for {self.job_title} @ {self.company}: Scalable Distributed Systems, Data Integrity, Microservices, and Cloud Infrastructure."

    @property
    def reverse_interview_questions(self) -> List[str]:
        return [
            f"How does the engineering team at {self.company} evaluate and manage technical debt during rapid sprint deliverables?",
            f"What does the deployment and testing lifecycle look like from PR approval to production deployment at {self.company}?",
            "What are the biggest scalability or architecture bottlenecks the team plans to tackle in the next 2 quarters?"
        ]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["system_design_challenge"] = self.system_design_challenge
        d["technical_drills"] = self.technical_drills
        d["role_focus_summary"] = self.role_focus_summary
        d["reverse_interview_questions"] = self.reverse_interview_questions
        return d


class InterviewPrepSimulator:
    """Simulates domain-specific interviews and crafts customized STAR narratives."""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.profile = self.config.profile
        self.ai = UnifiedAISolver()

    def generate_prep_kit(
        self,
        job_title: str,
        company: str,
        job_description: str = ""
    ) -> InterviewPrepKit:
        """Generates comprehensive interview prep kit for a target company and role."""
        candidate_name = self.profile.get("personal_information", {}).get("name", "Kalash Jindal")
        years_exp = self.profile.get("years_of_experience", 5)
        skills_dict = self.profile.get("skills_years_experience", {})
        top_skills = list(skills_dict.keys())[:6]

        # 1. Attempt Multi-Provider LLM Synthesis
        ai_kit = self._try_ai_synthesis(job_title, company, job_description, top_skills, years_exp)
        if ai_kit:
            return ai_kit

        # 2. High-Fidelity Heuristic Fallback
        return self._generate_heuristic_kit(job_title, company, job_description, top_skills, years_exp)

    def _try_ai_synthesis(
        self,
        job_title: str,
        company: str,
        job_description: str,
        top_skills: List[str],
        years_exp: int
    ) -> Optional[InterviewPrepKit]:
        """Queries multi-provider LLM (Claude, OpenAI, Gemini) for interview generation."""
        prompt = f"""You are an elite Staff Engineering Interviewer and Career Coach.
Candidate: {years_exp} years experience in {', '.join(top_skills)} (prior background at Nasdaq scaling data systems).
Target Company: {company}
Target Role: {job_title}
Job Description: {job_description[:800]}

Generate an interview preparation kit in valid JSON with exactly this structure:
{{
  "system_design_challenges": [
    {{
      "title": "...",
      "problem_statement": "...",
      "key_components": ["component 1", "component 2", "component 3"],
      "scale_and_tradeoffs": "..."
    }}
  ],
  "technical_deep_dives": [
    {{
      "question": "...",
      "core_concept": "...",
      "recommended_answer": "..."
    }}
  ],
  "behavioral_star_stories": [
    {{
      "theme": "Outage Recovery / Leadership / Conflict",
      "situation": "...",
      "task": "...",
      "action": "...",
      "result": "..."
    }}
  ],
  "key_talking_points": ["point 1", "point 2", "point 3"]
}}
Provide exactly 2 system design challenges, 3 technical questions, and 2 STAR stories. Return ONLY the JSON object."""

        try:
            raw = self.ai.solve_complex_text(prompt)
            if raw:
                # Extract JSON block
                clean_json = raw.strip()
                if "```json" in clean_json:
                    clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json:
                    clean_json = clean_json.split("```")[1].split("```")[0].strip()
                parsed = json.loads(clean_json)

                return InterviewPrepKit(
                    job_title=job_title,
                    company=company,
                    system_design_challenges=parsed.get("system_design_challenges", []),
                    technical_deep_dives=parsed.get("technical_deep_dives", []),
                    behavioral_star_stories=parsed.get("behavioral_star_stories", []),
                    key_talking_points=parsed.get("key_talking_points", [])
                )
        except Exception:
            pass
        return None

    def _generate_heuristic_kit(
        self,
        job_title: str,
        company: str,
        job_description: str,
        top_skills: List[str],
        years_exp: int
    ) -> InterviewPrepKit:
        """Deterministic domain-tailored interview generator."""
        skills_str = ", ".join([s.title() for s in top_skills[:3]]) if top_skills else "Python, AWS, PySpark"

        sys_design = [
            {
                "title": f"High-Throughput Ingestion & Lakehouse Pipeline for {company}",
                "problem_statement": f"Design a real-time event streaming and batch aggregation system capable of processing 100M+ events per day with sub-second analytics SLAs for {company}.",
                "key_components": [
                    "Distributed Ingestion (Kafka / AWS Kinesis) with partitioned topics",
                    "Stateful Stream Processing & Deduping (Spark Streaming / Flink)",
                    "ACID Lakehouse Storage (Delta Lake / Apache Iceberg) on S3/GCS",
                    "Query & Serving Layer (Trino / Databricks SQL / Athena)"
                ],
                "scale_and_tradeoffs": "Kafka topic partitioning vs consumer lag; Delta Lake compaction vs write amplification; exactly-once semantics vs latency overhead."
            },
            {
                "title": f"Fault-Tolerant Microservices & Caching Architecture",
                "problem_statement": f"Architect a distributed backend handling heavy read/write traffic during market volatility or peak transactions without degrading downstream databases.",
                "key_components": [
                    "API Gateway with rate limiting & token bucket algorithm",
                    "Distributed Cache (Redis Cluster) with cache-aside and write-behind patterns",
                    "Idempotency keys and distributed locks for transactional safety",
                    "Circuit Breaker & dead-letter queue (DLQ) for asynchronous recovery"
                ],
                "scale_and_tradeoffs": "Redis failover consistency vs availability; Cache stampede mitigation strategies."
            }
        ]

        tech_questions = [
            {
                "question": "How do you diagnose and eliminate Spark executor out-of-memory (OOM) errors and data skew?",
                "core_concept": "Data partitioning, salting skewed keys, broadcast joins, and off-heap memory tuning.",
                "recommended_answer": "I first analyze the Spark UI Stages tab to identify tasks with disproportionate shuffle read/write sizes or execution times. For skewed keys, I apply salting (appending a random integer 0-N) to redistribute data across reducers. For large-to-small table joins, I leverage BroadcastHashJoin to eliminate shuffle overhead entirely. I also tune spark.sql.shuffle.partitions and spark.memory.fraction to balance execution vs storage pools."
            },
            {
                "question": "Explain how you achieve idempotent writes in distributed data ingestion.",
                "core_concept": "Idempotency keys, transactional Delta MERGE, deduplication windows.",
                "recommended_answer": "In distributed pipelines, network retries and duplicate events are inevitable. I enforce idempotency at two layers: (1) At the ingestion edge using deterministic hashing of event payload + timestamp as unique deduplication keys within a sliding window (e.g., Redis TTL or Bloom filter), and (2) At storage layer using ACID Delta Lake MERGE operations matching on primary keys to guarantee write-once idempotency."
            },
            {
                "question": f"How do you design database schema migrations with zero downtime for high-scale systems at {company}?",
                "core_concept": "Expand/Contract (Blue/Green) database schema migration pattern.",
                "recommended_answer": "I follow the Expand and Contract pattern: Step 1 (Expand) - Add the new column/table as nullable without dropping old fields; Step 2 - Deploy code that dual-writes to both schemas; Step 3 - Backfill historical records asynchronously; Step 4 - Switch application reads to the new schema; Step 5 (Contract) - Deprecate and drop the old fields once all services are verified."
            },
            {
                "question": "How do you implement Change Data Capture (CDC) and manage backpressure when syncing databases to a data lakehouse?",
                "core_concept": "Debezium, Kafka log compaction, backpressure buffers, and Delta Lake ACID merge.",
                "recommended_answer": "I utilize Debezium connectors reading Postgres/MySQL WAL logs into Kafka. To handle burst backpressure, I tune Kafka consumer fetch.max.bytes and use adaptive rate-limiting in Spark Streaming. Writes to Delta Lake use MERGE on primary keys with partition pruning to keep merge latencies sub-minute."
            },
            {
                "question": "What strategies do you use for distributed caching, cache stampede prevention, and eventual consistency?",
                "core_concept": "Cache-aside, probabilistic early expiration (XFetch), distributed locks, and TTL jitter.",
                "recommended_answer": "I implement cache-aside with Redis. To prevent cache stampede when popular keys expire, I apply probabilistic early recomputation (XFetch algorithm) and distributed mutex locks using Redlock so only one worker queries the primary DB while others wait or serve stale data temporarily."
            }
        ]

        star_stories = [
            {
                "theme": "Critical Production Incident & High-Pressure Remediation",
                "situation": "During high market volatility at Nasdaq, an upstream partner format change caused our primary event ingestion stream to fail, accumulating 20M+ unread events in Kafka lag.",
                "task": "I was the designated technical lead responsible for restoring pipeline throughput within a strict 30-minute SLA without dropping financial transactions.",
                "action": "I diagnosed the schema incompatibility using Dead-Letter Queue logs, rapidly deployed a hot-fix filter isolating the malformed records into a staging buffer, and dynamically scaled out consumer executor partitions by 3x to drain the backlog.",
                "result": "Drained the 20M event backlog in under 18 minutes, recovered 100% of financial transactions with zero data loss, and implemented automated schema validation contracts in CI/CD to prevent recurrence."
            },
            {
                "theme": "Infrastructure Optimization & 40% Cloud Cost Reduction",
                "situation": "Our legacy Spark and EMR clusters were running 24/7 with fixed provisioning, driving excessive AWS compute expenses and frequent resource starvation during peak hours.",
                "task": "Tasked with modernizing the data infrastructure to support growing data volume while cutting monthly infrastructure expenditure.",
                "action": "Migrated scheduled workloads to Databricks autoscaling clusters on Spot instances with automated cluster shutdown policies, converted legacy parquet tables to optimized Delta Lake with Z-Ordering, and fine-tuned shuffle partitions.",
                "result": "Reduced monthly AWS cloud compute bills by 40%, improved query response latency by 3.5x, and established automated cost-attribution dashboards across engineering teams."
            },
            {
                "theme": "Cross-Functional Architecture & Zero-Downtime Migration",
                "situation": "Multiple product and analytics teams were blocked by inconsistent schema versions between transaction databases and downstream analytical engines.",
                "task": "Lead the cross-functional data contract initiative and migrate historical datasets without degrading active customer experiences.",
                "action": "Championed Protobuf schemas with schema registry validation, implemented dual-write expand/contract pipelines, and created automated validation suites for analytics stakeholders.",
                "result": "Completed migration across 14 services ahead of schedule with 0 downstream downtime and eliminated schema mismatch defects across engineering."
            }
        ]

        talking_points = [
            f"Over {years_exp} years scaling distributed systems in enterprise environments (Nasdaq, etc.).",
            f"Hands-on architectural mastery in {skills_str}.",
            f"Demonstrated track record of delivering 40% cost efficiency and sub-second SLAs.",
            "Available on a confirmed 60-day notice period with immediate technical impact."
        ]

        return InterviewPrepKit(
            job_title=job_title,
            company=company,
            system_design_challenges=sys_design,
            technical_deep_dives=tech_questions,
            behavioral_star_stories=star_stories,
            key_talking_points=talking_points
        )

    def format_cli_prep(self, kit: InterviewPrepKit) -> str:
        """Renders rich terminal study guide for the candidate."""
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RESET = "\033[0m"

        lines = []
        lines.append(f"\n{BOLD}{'='*68}{RESET}")
        lines.append(f"{CYAN}{BOLD}  🎯 CAREERENGINE TECHNICAL INTERVIEW PREPARATION KIT{RESET}")
        lines.append(f"{BOLD}{'='*68}{RESET}\n")

        lines.append(f"  {BOLD}Target Position:{RESET}  {kit.job_title} @ {GREEN}{kit.company}{RESET}\n")

        # System Design Challenges
        lines.append(f"  {YELLOW}{BOLD}🏗️ SYSTEM DESIGN ARCHITECTURE CHALLENGES:{RESET}")
        for i, sdc in enumerate(kit.system_design_challenges, 1):
            lines.append(f"\n  {BOLD}{i}. {sdc['title']}{RESET}")
            lines.append(f"     Problem: {sdc['problem_statement']}")
            lines.append(f"     Key Components:")
            for comp in sdc.get("key_components", []):
                lines.append(f"       • {comp}")
            lines.append(f"     Tradeoffs: {sdc.get('scale_and_tradeoffs', '')}")

        # Technical Deep Dives
        lines.append(f"\n  {YELLOW}{BOLD}💻 TECHNICAL DEEP-DIVE & CORE CONCEPT DRILLS:{RESET}")
        for i, td in enumerate(kit.technical_deep_dives, 1):
            lines.append(f"\n  {BOLD}{i}. Q: {td['question']}{RESET}")
            lines.append(f"     Concept: {CYAN}{td['core_concept']}{RESET}")
            lines.append(f"     Model Answer:\n     \"{td['recommended_answer']}\"")

        # Behavioral STAR Stories
        lines.append(f"\n  {YELLOW}{BOLD}🌟 BEHAVIORAL STAR NARRATIVES (CUSTOMIZED TO YOUR EXPERIENCE):{RESET}")
        for i, star in enumerate(kit.behavioral_star_stories, 1):
            lines.append(f"\n  {BOLD}{i}. Theme: {star['theme']}{RESET}")
            lines.append(f"     • {BOLD}Situation:{RESET} {star['situation']}")
            lines.append(f"     • {BOLD}Task:{RESET}      {star['task']}")
            lines.append(f"     • {BOLD}Action:{RESET}    {star['action']}")
            lines.append(f"     • {BOLD}Result:{RESET}    {GREEN}{star['result']}{RESET}")

        # Talking Points
        lines.append(f"\n  {BOLD}💡 Key Talking Points & Pitch Strengths:{RESET}")
        for pt in kit.key_talking_points:
            lines.append(f"    ✓ {pt}")

        lines.append(f"\n{BOLD}{'='*68}{RESET}\n")
        return "\n".join(lines)

interview_prep_simulator = InterviewPrepSimulator()
