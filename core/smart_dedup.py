"""
CareerEngine Smart Cross-Platform Deduplication Engine.
Normalizes company entities and job titles using token analysis and fuzzy string matching
to prevent applying to duplicate openings across LinkedIn, Naukri, Indeed, Glassdoor, and Foundit.
"""

import re
import difflib
import sqlite3
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# Suffixes and noise tokens to strip from company names
COMPANY_NOISE_TOKENS = [
    r"\bpvt\b", r"\bltd\b", r"\bprivate\b", r"\blimited\b", r"\binc\b",
    r"\bincorporated\b", r"\bllc\b", r"\bllp\b", r"\bcorp\b", r"\bcorporation\b",
    r"\btechnologies\b", r"\btechnology\b", r"\bsolutions\b", r"\bservices\b",
    r"\bsoftware\b", r"\bconsulting\b", r"\bgroup\b", r"\bholdings\b",
    r"\bindia\b", r"\bglobal\b", r"\binternational\b", r"\bsystems\b"
]

# Suffixes and location/workplace noise to strip from job titles
TITLE_NOISE_PATTERNS = [
    r"\[.*?\]",               # [AS324], [Remote], etc.
    r"\(.*?\)",               # (Remote), (Immediate Joiner), etc.
    r"\bimmediate joiner\b",
    r"\burgent requirement\b",
    r"\burgent\b",
    r"\bhiring\b",
    r"\bactively hiring\b",
    r"\bremote\b",
    r"\bhybrid\b",
    r"\bonsite\b",
    r"\bfull[\s\-]time\b",
    r"\bpart[\s\-]time\b",
    r"\bcontract\b",
    r"\bfreelance\b",
    r"\bindia\b",
    r"\bbangalore\b",
    r"\bbengaluru\b",
    r"\bhyderabad\b",
    r"\bpune\b",
    r"\bgurgaon\b",
    r"\bnoida\b",
    r"\bmumbai\b",
    r"\bdelhi\b"
]

class SmartDeduplicator:
    """Detects and resolves duplicate job postings across platforms."""

    @staticmethod
    def normalize_company(name: str) -> str:
        """Normalizes company name by stripping legal suffixes and punctuation."""
        if not name:
            return ""
        norm = name.lower().strip()
        # Remove punctuation
        norm = re.sub(r"[^\w\s]", " ", norm)
        # Strip noise tokens
        for pattern in COMPANY_NOISE_TOKENS:
            norm = re.sub(pattern, " ", norm, flags=re.IGNORECASE)
        # Collapse multi-spaces
        norm = re.sub(r"\s+", " ", norm).strip()
        return norm

    @staticmethod
    def clean_job_title(title: str) -> str:
        """Standardizes job title by stripping hiring tags, locations, and bracketed noise."""
        if not title:
            return ""
        cleaned = title.lower().strip()
        for pattern in TITLE_NOISE_PATTERNS:
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def token_similarity(cls, str1: str, str2: str) -> float:
        """Calculates token-based Jaccard similarity between two strings."""
        tokens1 = set(str1.split())
        tokens2 = set(str2.split())
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        return len(intersection) / len(union)

    @classmethod
    def sequence_similarity(cls, str1: str, str2: str) -> float:
        """Calculates character sequence similarity ratio (0.0 to 1.0)."""
        if not str1 or not str2:
            return 0.0
        return difflib.SequenceMatcher(None, str1, str2).ratio()

    @staticmethod
    def clean_company_name(name: str) -> str:
        """Alias for normalize_company."""
        return SmartDeduplicator.normalize_company(name)

    @classmethod
    def title_similarity(cls, str1: str, str2: str) -> float:
        """Calculates normalized title similarity."""
        c1 = cls.clean_job_title(str1)
        c2 = cls.clean_job_title(str2)
        if c1 == c2 and c1 != "":
            return 1.0
        return max(cls.sequence_similarity(c1, c2), cls.token_similarity(c1, c2))

    @classmethod
    def is_match(
        cls,
        title1: str = "",
        company1: str = "",
        title2: str = "",
        company2: str = "",
        company_threshold: float = 0.80,
        title_threshold: float = 0.75,
        **kwargs
    ) -> bool:
        """
        Determines whether two job postings represent the exact same opportunity.
        Supports both positional and keyword arguments (title_a, company_a, title_b, company_b).
        """
        t1 = title1 or kwargs.get("title_a", "")
        c1 = company1 or kwargs.get("company_a", "")
        t2 = title2 or kwargs.get("title_b", "")
        c2 = company2 or kwargs.get("company_b", "")

        norm_c1 = cls.normalize_company(c1)
        norm_c2 = cls.normalize_company(c2)

        # 1. Company check
        if norm_c1 == norm_c2 and norm_c1 != "":
            comp_match = True
        else:
            comp_sim = max(
                cls.sequence_similarity(norm_c1, norm_c2),
                cls.token_similarity(norm_c1, norm_c2)
            )
            # Substring match if name is sufficiently long
            if len(norm_c1) >= 4 and len(norm_c2) >= 4:
                if norm_c1 in norm_c2 or norm_c2 in norm_c1:
                    comp_sim = max(comp_sim, 0.88)
            comp_match = comp_sim >= company_threshold

        if not comp_match:
            return False

        # 2. Title check
        clean_t1 = cls.clean_job_title(t1)
        clean_t2 = cls.clean_job_title(t2)

        if clean_t1 == clean_t2 and clean_t1 != "":
            return True

        title_sim = max(
            cls.sequence_similarity(clean_t1, clean_t2),
            cls.token_similarity(clean_t1, clean_t2)
        )
        if clean_t1 and clean_t2:
            if clean_t1 in clean_t2 or clean_t2 in clean_t1:
                title_sim = max(title_sim, 0.82)

        return title_sim >= title_threshold

    def audit_database_duplicates(self, db_path: str) -> List[Dict[str, Any]]:
        """
        Scans SQLite database to discover cross-platform duplicates.
        Returns pairs/groups of suspected duplicate applications.
        """
        if not Path(db_path).exists():
            return []

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, job_id, title, company, platform, status, created_at FROM applications ORDER BY id ASC")
        records = [dict(r) for r in c.fetchall()]
        conn.close()

        duplicates = []
        n = len(records)
        seen = set()

        for i in range(n):
            if records[i]["id"] in seen:
                continue
            group = [records[i]]
            for j in range(i + 1, n):
                if records[j]["id"] in seen:
                    continue
                if self.is_match(
                    records[i].get("title", ""),
                    records[i].get("company", ""),
                    records[j].get("title", ""),
                    records[j].get("company", "")
                ):
                    group.append(records[j])
                    seen.add(records[j]["id"])
            if len(group) > 1:
                duplicates.append({
                    "primary": group[0],
                    "duplicate_count": len(group) - 1,
                    "matches": group[1:]
                })

        return duplicates

smart_deduplicator = SmartDeduplicator()
