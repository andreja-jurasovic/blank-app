"""
Guardrails Module for HAOD Digital Assistant

CRITICAL: Output filtering to prevent prohibited content from reaching users.
This is a LEGAL COMPLIANCE requirement - Miran must NEVER give financial advice.
"""
from typing import Tuple

# Forbidden phrases that should NEVER appear in output
# These trigger immediate blocking of the response
FORBIDDEN_PHRASES = [
    # ===== FINANCIAL ADVICE INDICATORS (ILLEGAL) =====
    # Direct advice
    "preporučujem da",
    "preporučam da",
    "preporučujem ti",
    "preporučam ti",
    "savjetujem da",
    "savjetujem ti",
    "moj savjet je",
    "moj savjet",
    "savjet je da",

    # Should/ought language
    "trebao bi",
    "trebala bi",
    "trebali bi",
    "trebali biste",
    "trebao bih",
    "trebas",
    "trebaš",
    "moras",
    "moraš",
    "bi trebao",
    "bi trebala",

    # Best course of action
    "najbolje bi bilo da",
    "najbolje je da",
    "najbolje bi bilo",
    "bilo bi najbolje",
    "bilo bi pametno",
    "bilo bi mudro",
    "pametno bi bilo",
    "mudro bi bilo",

    # Recommendations
    "preporuka je",
    "moja preporuka",
    "preporučam",
    "preporučujem",
    "predlažem da",
    "predlazem da",
    "sugerirao bih",
    "sugerirala bih",
    "sugerujem",

    # Imperative advice
    "stavi novac",
    "prebaci novac",
    "povuci novac",
    "podigni novac",
    "otvori račun",
    "zatvori račun",
    "uloži u",
    "ulozi u",
    "ne ulaži",
    "ne ulazi",
    "kupi",
    "prodaj",
    "čekaj da",
    "cekaj da",
    "ne čekaj",
    "ne cekaj",

    # Opinion as advice
    "ja bih na tvom mjestu",
    "na tvom mjestu bih",
    "da sam ja tebe",
    "da sam na tvom mjestu",

    # ===== BANK STABILITY CLAIMS (PROHIBITED) =====
    "ova banka je sigurna",
    "ta banka je sigurna",
    "banka je sigurna",
    "banka je potpuno sigurna",
    "banka je stabilna",
    "banka je solventna",
    "banka neće propasti",
    "banka će preživjeti",
    "banka je u dobrom stanju",
    "ne brinite sve je sigurno",
    "nema razloga za brigu",
    "banka će sigurno",
    "neće propasti",
    "sigurno neće",

    # ===== GUARANTEES WE CAN'T MAKE =====
    "garantiram",
    "jamčim",
    "jamcim",
    "obećavam",
    "obecavam",
    "100% sigurno",
    "apsolutno sigurno",
    "potpuno sigurno",
    "nema nikakve šanse",
    "nema sanse",
    "nemoguće je",
    "nemoguce je",
    "sigurno ćeš dobiti",
    "sigurno ces dobiti",
    "definitivno ćeš",
    "definitivno ces",
]

# Patterns that indicate advice even without exact phrase match
ADVICE_PATTERNS = [
    "trebao bi",
    "trebala bi",
    "trebali bi",
    "bi trebao",
    "bi trebala",
    "bi trebali",
    "moraš",
    "moras",
    "nemoj",
    "uradi",
    "napravi",
    "učini",
    "ucini",
]

# Replacement message when forbidden content is detected
GUARDRAIL_RESPONSE = (
    "Kao digitalni asistent HAOD-a, mogu dati samo informativna objašnjenja o sustavu "
    "osiguranja depozita. Ne dajem financijske savjete niti procjene stabilnosti banaka "
    "jer to nije moja uloga. Za takve informacije, molim obratite se svojoj banci, "
    "ovlaštenom financijskom savjetniku ili nadležnim institucijama."
)


def check_forbidden_phrases(text: str) -> Tuple[bool, str]:
    """
    Check if text contains any forbidden phrases.

    Args:
        text: Text to check

    Returns:
        Tuple of (is_safe, matched_phrase or empty string)
    """
    text_lower = text.lower()

    for phrase in FORBIDDEN_PHRASES:
        if phrase in text_lower:
            return False, phrase

    return True, ""


def check_advice_patterns(text: str) -> Tuple[bool, str]:
    """
    Check for advice-like patterns that might slip through exact matching.

    Args:
        text: Text to check

    Returns:
        Tuple of (is_safe, matched_pattern or empty string)
    """
    text_lower = text.lower()

    # Check for imperative + action combinations
    imperative_starters = ["trebao bi", "trebala bi", "moraš", "moras", "nemoj"]
    action_words = ["prebaciti", "povući", "podići", "uložiti", "staviti", "zatvoriti", "otvoriti"]

    for starter in imperative_starters:
        if starter in text_lower:
            for action in action_words:
                if action in text_lower:
                    return False, f"{starter}...{action}"

    return True, ""


def guardrail_check(text: str) -> str:
    """
    Main guardrail function - filters output before sending to user.

    CRITICAL: This is the last line of defense against illegal financial advice.
    All LLM output MUST pass through this function.

    Args:
        text: LLM-generated response text

    Returns:
        Original text if safe, or replacement message if forbidden content detected
    """
    # Check 1: Exact forbidden phrases
    is_safe, matched_phrase = check_forbidden_phrases(text)
    if not is_safe:
        print(f"[GUARDRAIL] BLOCKED - Forbidden phrase: '{matched_phrase}'")
        return GUARDRAIL_RESPONSE

    # Check 2: Advice patterns
    is_safe, matched_pattern = check_advice_patterns(text)
    if not is_safe:
        print(f"[GUARDRAIL] BLOCKED - Advice pattern: '{matched_pattern}'")
        return GUARDRAIL_RESPONSE

    return text


def validate_response_length(text: str, max_length: int = 2000) -> str:
    """
    Ensure response isn't too long.

    Args:
        text: Response text
        max_length: Maximum allowed characters

    Returns:
        Truncated text if too long, with ellipsis
    """
    if len(text) > max_length:
        truncated = text[:max_length]
        last_period = truncated.rfind(".")
        if last_period > max_length * 0.7:
            return truncated[:last_period + 1]
        return truncated + "..."

    return text
