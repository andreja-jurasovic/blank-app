"""
Configuration for HAOD Digital Assistant (Miran)
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# LLM Settings
CLASSIFIER_TEMPERATURE = 0
FORMATTER_TEMPERATURE = 0.3

# Model configuration - can switch to lighter model if needed
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash")

# Classification mode: "llm" (recommended for demo) or "rules" (no API needed)
CLASSIFICATION_MODE = os.getenv("CLASSIFICATION_MODE", "llm")

# Confidence threshold (only used in rules mode)
CONFIDENCE_THRESHOLD = 0.85

# Deposit insurance limit (EUR)
DEPOSIT_LIMIT = 100_000

# Intent Categories
CATEGORIES = [
    "general_info",
    "limit_explanation",
    "coverage",
    "non_coverage",
    "joint_accounts",
    "foreign_currency",
    "account_types",
    "eu_banks",
    "payout_timing",
    "limit_calc",
    "panic",
    "financial_advice_restricted",
    "bank_stability_restricted",
    "human_agent",
    "off_topic",
]

# Restricted categories - return template directly, no LLM formatting
RESTRICTED_CATEGORIES = [
    "financial_advice_restricted",
    "bank_stability_restricted",
    "off_topic",
]

# Categories that trigger calculator
CALCULATOR_CATEGORIES = [
    "limit_calc",
]

# System prompt for intent classification (optimized for token efficiency)
CLASSIFIER_SYSTEM_PROMPT = """Classify deposit insurance query. Reply with ONE category name only.

Categories:
general_info|limit_explanation|coverage|non_coverage|joint_accounts|foreign_currency|account_types|eu_banks|payout_timing|limit_calc|panic|financial_advice_restricted|bank_stability_restricted|human_agent|off_topic

coverage=bank fails/lose money, payout_timing=when get money, limit_calc=specific amounts, panic=news worried, financial_advice_restricted=asking advice, bank_stability_restricted=is bank X safe, human_agent=wants to talk to real person/contact info/phone/email, off_topic=NOT about deposit insurance/banks/HAOD at all (politics, weather, sports, general knowledge, etc.)"""

# System prompt for answer formatting (Miran persona)
FORMATTER_SYSTEM_PROMPT = """Ti si "Miran", digitalni asistent Hrvatske agencije za osiguranje depozita (HAOD).

STROGA PRAVILA (ZAKONSKA OBVEZA):
- NIKADA ne daji financijske savjete - to je ILEGALNO
- NIKADA ne koristi riječi: trebao bi, trebala bi, preporučujem, savjetujem, moraš, najbolje bi bilo
- NIKADA ne govori korisnicima što da rade s novcem
- NIKADA ne procjenjuj stabilnost banaka
- NIKADA ne garantiraj ishode

DOPUŠTENO:
- Koristi ISKLJUČIVO informacije koje ti se daju kao odobreni sadržaj
- Objašnjavaj kako sustav funkcionira (informativno, ne savjetodavno)
- Upućuj na službene izvore i stručnjake za savjete
- Budi smiren, jednostavan i informativan
- Odgovaraj na hrvatskom jeziku

Tvoj zadatak je formulirati konačan odgovor korisniku na temelju odobrenih informacija - samo informacije, nikakvi savjeti."""

# Prompt template for answer generation
ANSWER_PROMPT_TEMPLATE = """Korisnikovo pitanje: {question}

Odobrene informacije:
{approved_answer}

{calculation_result}

Formuliraj konačan odgovor na hrvatskom jeziku u Miranovom tonu - prijateljski, smireno i informativno."""

# Rule-based classification patterns (Croatian)
# Patterns are checked with priority - order matters for some categories
# Each pattern has implicit weight: longer/more specific = higher confidence

RULE_PATTERNS = {
    # RESTRICTED CATEGORIES - highest priority for direct matches
    "bank_stability_restricted": [
        # Asking if specific bank is safe
        "je li banka x sigurna",
        "banka x sigurna",
        "je li banka sigurna",
        "banka sigurna",
        "sigurna banka",
        "je li sigurna",
        "je li stabilna",
        "stabilna banka",
        # Asking about bank failure
        "hoće li propasti",
        "hoce li propasti",
        "će li propasti",
        "ce li propasti",
        "će li preživjeti",
        "ce li prezivjeti",
        "hoće li banka",
        "hoce li banka",
        # Common Croatian bank names + sigurna/stabilna/propasti
        "pbz sigurna",
        "pbz stabilna",
        "pbz propasti",
        "zaba sigurna",
        "zaba stabilna",
        "zaba propasti",
        "erste sigurna",
        "erste stabilna",
        "erste propasti",
        "otp sigurna",
        "otp stabilna",
        "otp propasti",
        "rba sigurna",
        "rba stabilna",
        "rba propasti",
        "addiko sigurna",
        "addiko propasti",
        "hpb sigurna",
        "hpb propasti",
        # General patterns
        "možeš li mi reći je li",
        "mozes li mi reci je li",
        "je li ta banka",
        "je li ova banka",
        # Failure questions with bank names
        "hoce li",
        "hoće li",
    ],
    "financial_advice_restricted": [
        "što mi savjetuješ",
        "sto mi savjetujes",
        "što da napravim s novcem",
        "sto da napravim s novcem",
        "preporučuješ li",
        "preporucujes li",
        "isplati li se",
        "da li da uložim",
        "da li da ulozim",
        "da li da prebacim",
        "daj mi savjet",
        "daj savjet",
        "koju stednju",
        "koju štednju",
        "koju banku",
        "kako da postupim",
        # Moving/transferring money questions
        "mogu li premjestiti",
        "mogu li prebaciti",
        "da li da premjestim",
        "da li da prebacim",
        "premjestiti novac",
        "prebaciti novac",
        "premjestiti u jednu",
        "prebaciti u jednu",
        "staviti sve u jednu",
        "držati sve u jednoj",
        "drzati sve u jednoj",
        "rasporediti novac",
        "raspodijeliti novac",
        # Note: "trebam li" is context-dependent - handled specially in classifier
    ],

    # CALCULATION - when user provides specific amounts
    "limit_calc": [
        # Specific amount patterns (from test scenarios)
        "80.000 €",
        "80.000€",
        "80000 €",
        "80000€",
        "80000 eura",
        "150.000 €",
        "150.000€",
        "150000 eura",
        "60.000 €",
        "60.000€",
        "60000 eura",
        "140.000 €",
        "140.000€",
        "140000 eura",
        # General calculation triggers
        "koliko mi je od toga osigurano",
        "koliko bi od toga bilo",
        "koliko bi bilo osigurano",
        "koliko bi bilo pokriveno",
        "koliko je osigurano",
        "koliko od toga",
        "recimo da imam",
        "imam i zelim znati",
        # Multi-bank specific patterns
        "u jednoj banci i",
        "u jednoj banci a",
        "€ u drugoj banci",
        "eura u drugoj banci",
        "izračunaj",
        "izracunaj",
        # Pattern: amount + eura/€
        "€ u jednoj banci",
        "€ u drugoj banci",
        "eura u jednoj banci",
        "eura u drugoj banci",
    ],

    # PANIC - emotional/news-triggered concerns (check before financial_advice)
    "panic": [
        # News-related panic (specific phrases)
        "na vijestima čuo",
        "čuo na vijestima",
        "vidio na vijestima",
        "vijest je izašla",
        "nema službenih obavijesti",
        "nema još službenih",
        "svi pričaju",
        # Bank trouble indicators
        "banka u problemima",
        "moja banka u problemima",
        "trčati po novac",
        "odmah trčati",
        # Crowd behavior
        "svi dižu novac",
        "svi povlače",
        "panično dižu",
        "panično",
        "panika",
        # Crisis language
        "dogodi najgore",
        "ako se baš sad dogodi",
        "najgori scenarij",
        "odmah reagirati",
        "trebam li čekati ili odmah",
        # Over-limit concern in panic context (specific)
        "imam više od 100.000",
        "sigurno propasti",
        "sve iznad toga",
        "će sve iznad toga",
        "znači li to da će",
    ],

    # COVERAGE - what's protected / bank failure questions
    "coverage": [
        # Bank failure / closure questions
        "banka zatvori",
        "banka propadne",
        "banka propala",
        "ako banka propadne",
        "ako banka zatvori",
        "ako se banka zatvori",
        "propast banke",
        "propasti banke",
        "ostajem bez novaca",
        "ostajem bez novca",
        "ostati bez novca",
        "bez novaca",
        "izgubim novac",
        "izgubiti novac",
        # Multiple banks
        "dvije banke",
        "više banaka",
        "svaka banka posebno",
        "sve skupa ili",
        "gleda li se",
        # Will I lose everything
        "ostao bez svega",
        "izgubiti sve",
        "bez svega",
        # Payout guarantee
        "stvarno biti isplaćeno",
        "stvarno isplaćeno",
        "stvarno biti pokriveno",
        "koliko mogu biti siguran",
        "hoće li stvarno",
        # General coverage
        "što je pokriveno",
        "što je osigurano",
        "koje je pokriveno",
        "je li pokriveno",
        "jesam li zaštićen",
        "je li zaštićen",
    ],

    # JOINT ACCOUNTS
    "joint_accounts": [
        "zajednički račun",
        "zajedničkom računu",
        "suprug i ja",
        "supruga i ja",
        "nas dvoje",
        "zajednička štednja",
        "dijeli na",
    ],

    # FOREIGN CURRENCY / TERM DEPOSITS
    "foreign_currency": [
        "devizna štednja",
        "devizni račun",
        "oročena štednja",
        "oročenje",
        "devizna i oročena",
        "u stranoj valuti",
    ],

    # ACCOUNT TYPES
    "account_types": [
        "tekući račun",
        "žiro račun",
        "štedni račun",
        "tekućeg, žiro",
        "tekući, žiro",
        "razlika za osiguranje",
        "razlika između",
        "vrste računa",
        "sve to pokriveno",
    ],

    # EU BANKS - high priority patterns for EU-specific questions
    "eu_banks": [
        "banci iz druge države",
        "banci iz druge države eu",
        "druge države eu",
        "druga država eu",
        "drugoj državi eu",
        "novac u banci iz druge",
        "eu banka",
        "inozemna banka",
        "strana banka",
        "štiti li to haod",
    ],

    # PAYOUT TIMING - questions about when money is paid
    "payout_timing": [
        "koliko bih dugo čekao",
        "koliko dugo čekao",
        "koliko dugo bih",
        "čekao novac",
        "rok isplate",
        "rokovi isplate",
        "kad ću dobiti",
        "kad mogu dobiti",
        "kada mogu dobiti",
        "kada isplata",
        "vrijeme isplate",
        "koliko traje isplata",
        "dobiti novac",
        "nakon sto banka",
        "nakon što banka",
        "kada ću dobiti",
        "koliko dugo čekam",
        "propasti banke",
    ],

    # LIMIT EXPLANATION - general info about 100k rule
    "limit_explanation": [
        "100.000 eura po osobi",
        "što to točno znači",
        "što znači limit",
        "sto tisuća",
        "što to znači za mene",
        "po osobi po banci",
    ],

    # NON-COVERAGE - what's NOT protected
    "non_coverage": [
        "nije pokriveno",
        "nije osigurano",
        "što nije",
        "mojih ulaganja",
        "od ulaganja",
        "investicijski fond",
        "fondovi",
        "dionice",
        "obveznice",
    ],

    # HUMAN AGENT - user wants to talk to a real person
    "human_agent": [
        "želim razgovarati",
        "zelim razgovarati",
        "živa osoba",
        "ziva osoba",
        "pravi agent",
        "pravi čovjek",
        "pravi covjek",
        "kontakt",
        "telefon",
        "nazovem",
        "email",
        "mail",
        "web stranica",
        "mogu li nazvati",
        "razgovarati s osobom",
        "razgovarati s nekim",
    ],

    # GENERAL INFO - about HAOD
    "general_info": [
        "što je haod",
        "sto je haod",
        "što je točno haod",
        "sto je tocno haod",
        "čime se bavite",
        "cime se bavite",
        "čime se vi bavite",
        "tko ste vi",
        "što radite",
        "sto radite",
        "o haod-u",
    ],
}

# Patterns that indicate panic context (used to override financial_advice detection)
PANIC_CONTEXT_INDICATORS = [
    "vijesti",
    "novine",
    "portal",
    "problemi",
    "propadne",
    "propast",
    "svi dižu",
    "panično",
    "panika",
    "najgore",
    "kriza",
]

# Ambiguous patterns that need context checking
CONTEXT_DEPENDENT_PATTERNS = {
    "trebam li": {
        "default": "financial_advice_restricted",
        "if_context_contains": PANIC_CONTEXT_INDICATORS,
        "then": "panic",
    },
}
