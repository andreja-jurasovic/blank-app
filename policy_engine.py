"""
Policy Engine for HAOD Digital Assistant

Routes classified intents to appropriate handlers based on policy rules.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from config import RESTRICTED_CATEGORIES, CALCULATOR_CATEGORIES


@dataclass
class KnowledgeEntry:
    """A single entry from the knowledge base."""
    id: str
    category: str
    title: str
    keywords: List[str]
    approved_answer: str


class KnowledgeBase:
    """Manages access to the approved knowledge base."""

    def __init__(self, kb_path: Optional[Path] = None):
        if kb_path is None:
            kb_path = Path(__file__).parent / "knowledge_base.json"

        with open(kb_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.entries: List[KnowledgeEntry] = []
        self.by_category: Dict[str, List[KnowledgeEntry]] = {}
        self.by_id: Dict[str, KnowledgeEntry] = {}

        for entry_data in data["entries"]:
            entry = KnowledgeEntry(
                id=entry_data["id"],
                category=entry_data["category"],
                title=entry_data["title"],
                keywords=entry_data.get("keywords", []),
                approved_answer=entry_data["approved_answer"],
            )
            self.entries.append(entry)
            self.by_id[entry.id] = entry

            if entry.category not in self.by_category:
                self.by_category[entry.category] = []
            self.by_category[entry.category].append(entry)

    def get_by_category(self, category: str) -> List[KnowledgeEntry]:
        """Get all entries for a category."""
        return self.by_category.get(category, [])

    def get_best_match(self, category: str, query: str) -> Optional[KnowledgeEntry]:
        """
        Get the best matching entry for a category based on query keywords.

        Args:
            category: The intent category
            query: The user's question (for keyword matching)

        Returns:
            Best matching KnowledgeEntry or None
        """
        entries = self.get_by_category(category)
        if not entries:
            return None

        if len(entries) == 1:
            return entries[0]

        # Score entries by keyword matches
        query_lower = query.lower()
        scored = []

        for entry in entries:
            score = 0
            for keyword in entry.keywords:
                if keyword.lower() in query_lower:
                    score += 1
            scored.append((score, entry))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return highest scoring entry (or first if no keywords matched)
        return scored[0][1]


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""
    category: str
    confidence: float
    action: str  # "respond", "calculate", "restrict"
    knowledge_entry: Optional[KnowledgeEntry]
    requires_calculation: bool


class PolicyEngine:
    """
    Evaluates policy rules and determines response strategy.
    """

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    def evaluate(self, category: str, confidence: float, query: str) -> PolicyDecision:
        """
        Evaluate policy for a classified intent.

        Args:
            category: Classified intent category
            confidence: Classification confidence score
            query: Original user query

        Returns:
            PolicyDecision with routing information
        """
        # Determine action based on category
        if category in RESTRICTED_CATEGORIES:
            action = "restrict"
        elif category in CALCULATOR_CATEGORIES:
            action = "calculate"
        else:
            action = "respond"

        # Get best matching knowledge entry
        entry = self.kb.get_best_match(category, query)

        return PolicyDecision(
            category=category,
            confidence=confidence,
            action=action,
            knowledge_entry=entry,
            requires_calculation=(action == "calculate"),
        )

    def get_approved_answer(self, decision: PolicyDecision) -> str:
        """
        Get the approved answer text for a policy decision.

        Args:
            decision: PolicyDecision from evaluate()

        Returns:
            Approved answer text
        """
        if decision.knowledge_entry:
            return decision.knowledge_entry.approved_answer

        # Fallback if no entry found
        return (
            "Žao mi je, nemam specifičnu informaciju o tome. "
            "Molim kontaktirajte HAOD izravno za više informacija."
        )


# Singleton instances for convenience
_knowledge_base: Optional[KnowledgeBase] = None
_policy_engine: Optional[PolicyEngine] = None


def get_knowledge_base() -> KnowledgeBase:
    """Get or create the knowledge base singleton."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base


def get_policy_engine() -> PolicyEngine:
    """Get or create the policy engine singleton."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine(get_knowledge_base())
    return _policy_engine
