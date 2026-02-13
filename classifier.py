"""
Intent Classification Module for HAOD Digital Assistant

Supports two modes:
- LLM mode (default): Uses Gemini for accurate classification
- Rules mode: Pattern-based fallback when API unavailable
"""
from typing import Tuple, List, Dict
import re
import os

from config import (
    RULE_PATTERNS,
    CONFIDENCE_THRESHOLD,
    CATEGORIES,
    CLASSIFICATION_MODE,
)


# Category priority order (used in rules mode)
CATEGORY_PRIORITY = [
    "bank_stability_restricted",
    "eu_banks",
    "payout_timing",
    "panic",
    "limit_calc",
    "financial_advice_restricted",
    "joint_accounts",
    "foreign_currency",
    "account_types",
    "coverage",
    "non_coverage",
    "limit_explanation",
    "general_info",
]


def classify_with_llm(text: str) -> Tuple[str, float]:
    """
    Classify user intent using Gemini LLM.
    More accurate than rules for natural language variations.

    Args:
        text: User input text

    Returns:
        Tuple of (category, confidence)
    """
    from llm import classify_intent

    try:
        category = classify_intent(text)
        if category in CATEGORIES:
            return category, 0.95
        # If LLM returns unknown category, try to find closest match
        for cat in CATEGORIES:
            if cat in category or category in cat:
                return cat, 0.85
        return "general_info", 0.70
    except Exception as e:
        print(f"[CLASSIFIER] LLM error: {e}")
        raise


def calculate_match_score(text: str, patterns: List[str]) -> Tuple[int, float, str]:
    """Calculate match score for a category based on pattern matches."""
    matches = 0
    best_pattern = ""
    best_pattern_len = 0

    for pattern in patterns:
        if pattern in text:
            matches += 1
            if len(pattern) > best_pattern_len:
                best_pattern = pattern
                best_pattern_len = len(pattern)

    if matches == 0:
        return 0, 0.0, ""

    base_confidence = min(0.7 + (matches * 0.1), 0.95)
    length_bonus = min(best_pattern_len / 50, 0.15)
    confidence = min(base_confidence + length_bonus, 0.98)

    return matches, confidence, best_pattern


def has_specific_amounts(text: str) -> bool:
    """Check if text contains specific monetary amounts."""
    amount_pattern = r'\d{2,3}[.,]\d{3}'
    return bool(re.search(amount_pattern, text))


def count_amounts(text: str) -> int:
    """Count how many monetary amounts appear in text."""
    return len(re.findall(r'\d{2,3}[.,]\d{3}', text))


def has_bank_mentions(text: str) -> bool:
    """Check if text mentions banks (indicating a deposit scenario)."""
    bank_patterns = [
        "banci", "banka", "banke", "banku", "bankom", "banaka",
        "prvoj", "drugoj", "trećoj",
        "jednoj", "dvije", "tri",
    ]
    text_lower = text.lower()
    return any(p in text_lower for p in bank_patterns)


def classify_rules(text: str) -> Tuple[str, float]:
    """
    Rule-based intent classification using pattern matching.
    Used as fallback when LLM is unavailable.

    Args:
        text: User input text

    Returns:
        Tuple of (category, confidence_score)
    """
    text_lower = text.lower()

    # Score all categories
    category_scores: Dict[str, Tuple[int, float, str]] = {}

    for category in CATEGORY_PRIORITY:
        if category not in RULE_PATTERNS:
            continue

        patterns = RULE_PATTERNS[category]
        matches, confidence, best_pattern = calculate_match_score(text_lower, patterns)

        if matches > 0:
            category_scores[category] = (matches, confidence, best_pattern)

    # Auto-detect calculations: amounts + bank mentions = calculation, even without patterns
    # Exclude explanation questions (asking what the limit means, not calculating their deposits)
    explanation_phrases = ["što znači", "sto znaci", "što to znači", "što to točno znači", "po osobi po banci"]
    is_explanation = any(p in text_lower for p in explanation_phrases)
    if has_specific_amounts(text_lower) and has_bank_mentions(text_lower) and not is_explanation:
        return "limit_calc", 0.95

    if not category_scores:
        return "general_info", 0.4

    # Find best category by priority
    best_category: str = "general_info"
    best_confidence = 0.0

    for category in CATEGORY_PRIORITY:
        if category in category_scores:
            _, confidence, _ = category_scores[category]
            if best_category == "general_info":
                best_category = category
                best_confidence = confidence
            elif confidence > best_confidence + 0.15:
                best_category = category
                best_confidence = confidence

    # Additional calc detection for pattern-matched cases
    if "limit_calc" in category_scores and has_specific_amounts(text_lower):
        _, calc_conf, _ = category_scores["limit_calc"]
        asking_calculation = any(q in text_lower for q in [
            "koliko mi je", "koliko bi", "koliko od toga", "izračunaj", "recimo da imam",
        ])
        if asking_calculation and calc_conf >= 0.7:
            best_category = "limit_calc"
            best_confidence = min(calc_conf + 0.1, 0.95)

    # Bank stability always wins if matched
    if "bank_stability_restricted" in category_scores:
        _, stability_conf, _ = category_scores["bank_stability_restricted"]
        if stability_conf >= 0.7:
            return "bank_stability_restricted", 0.95

    return best_category, best_confidence


def classify(text: str) -> Tuple[str, float]:
    """
    Main classification function.

    OPTIMIZED: Uses rules first, only calls LLM if confidence is low.
    This saves tokens while maintaining accuracy.

    Args:
        text: User input text

    Returns:
        Tuple of (category, confidence_score)
    """
    # Always try rules first (free, fast)
    rules_category, rules_confidence = classify_rules(text)

    # If rules are confident (≥90%), skip LLM to save tokens
    if rules_confidence >= 0.90:
        print(f"[CLASSIFIER] Rules confident ({rules_confidence:.0%}), skipping LLM")
        return rules_category, rules_confidence

    # If rules have medium confidence (70-90%), still skip LLM for restricted categories
    # (These are critical and rules patterns are reliable for them)
    if rules_confidence >= 0.70 and rules_category in ["bank_stability_restricted", "financial_advice_restricted"]:
        print(f"[CLASSIFIER] Restricted category detected by rules, skipping LLM")
        return rules_category, rules_confidence

    # Only use LLM for low confidence cases
    use_llm = CLASSIFICATION_MODE.lower() == "llm" and os.getenv("GEMINI_API_KEY")

    if use_llm and rules_confidence < 0.70:
        try:
            print(f"[CLASSIFIER] Low confidence ({rules_confidence:.0%}), using LLM")
            return classify_with_llm(text)
        except Exception:
            print("[CLASSIFIER] LLM failed, using rules result")
            return rules_category, rules_confidence

    return rules_category, rules_confidence


# Testing utility
def test_classification(questions: List[str]) -> None:
    """Test classification on a list of questions."""
    print("\n" + "=" * 60)
    print(f"CLASSIFICATION TEST (mode: {CLASSIFICATION_MODE})")
    print("=" * 60)

    for q in questions:
        category, confidence = classify(q)
        print(f"\nQ: {q[:60]}...")
        print(f"   → {category} ({confidence:.0%})")


if __name__ == "__main__":
    test_questions = [
        "Bok Miran, što je točno HAOD i čime se vi bavite?",
        "ako se banka zatvori je li to znaci da ja ostajem bez novaca?",
        "kad mogu dobiti novac nakon sto banka propadne?",
        "Imam 80.000 € u jednoj banci i 150.000 € u drugoj. Koliko mi je osigurano?",
        "Je li banka X sigurna ili hoće li propasti?",
        "Suprug i ja imamo zajednički račun. Kako se tu računa ovih 100.000 eura?",
    ]
    test_classification(test_questions)
