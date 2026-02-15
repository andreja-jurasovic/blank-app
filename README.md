# Miran - HAOD Digital Assistant

A policy-controlled, AI-powered digital assistant for the **Croatian Deposit Insurance Agency (HAOD - Hrvatska agencija za osiguranje depozita)**. Miran helps Croatian citizens understand deposit insurance rules, coverage limits, and payout procedures — while strictly avoiding financial advice, as required by law.

## Features

- **Multi-layered compliance pipeline** — Classification → Policy Evaluation → Knowledge Base → Guardrails filtering
- **Dual classification modes** — LLM-based (Gemini) for accuracy, rules-based for offline fallback
- **Deposit calculator** — Parses complex inputs with multiple banks and amounts, calculates insured vs. excess
- **Panic response handling** — Recognizes news-triggered anxiety and provides calming, factual information
- **Croatian language support** — Handles accent variations, informal spelling, and colloquial phrasing
- **115+ forbidden phrase guardrails** — Prevents any financial advice or bank stability predictions from reaching users
- **Pre-approved knowledge base** — All responses vetted for legal compliance

## Quick Start

### Prerequisites

- Python 3.x
- A [Google Gemini API key](https://makersuite.google.com/app/apikey) (optional — works offline in rules mode)

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
GEMINI_API_KEY=your_api_key_here
```

Optional settings:

| Variable | Default | Description |
|---|---|---|
| `GEMINI_MODEL` | `gemini-1.5-flash` | Primary LLM model |
| `GEMINI_FALLBACK_MODEL` | `gemini-1.5-flash` | Fallback model |
| `CLASSIFICATION_MODE` | `llm` | `llm` or `rules` |

### Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

### Run Tests (no API key needed)

```bash
python test_scenarios.py
```

Runs 18 scenarios covering classification, policy routing, and calculations.

## How It Works

```
User Question
    ↓
[1] CLASSIFY — Rules-based or LLM classification into 13 intent categories
    ↓
[2] POLICY EVALUATE — Determine action: respond / calculate / restrict
    ↓
[3] KNOWLEDGE BASE — Retrieve pre-approved answer
    ↓
[4] PROCESS
    ├─ restrict  → Return refusal template (no LLM)
    ├─ calculate → Parse amounts, run calculator, format result
    └─ respond   → Optional LLM formatting in Miran's persona
    ↓
[5] GUARDRAILS — Filter output for forbidden phrases
    ↓
[6] RESPONSE — Return to user
```

## Intent Categories

| Category | Example | Action |
|---|---|---|
| `general_info` | "What is HAOD?" | respond |
| `limit_explanation` | "What does 100,000 EUR mean?" | respond |
| `coverage` | "What happens if a bank fails?" | respond |
| `non_coverage` | "What's NOT covered?" | respond |
| `joint_accounts` | "How do joint accounts work?" | respond |
| `foreign_currency` | "Foreign currency deposits?" | respond |
| `account_types` | "Are all account types covered?" | respond |
| `eu_banks` | "Are EU bank deposits protected?" | respond |
| `payout_timing` | "How long until payout?" | respond |
| `limit_calc` | "I have 80k in bank A, 150k in bank B" | calculate |
| `panic` | "I saw news about bank problems" | respond |
| `financial_advice_restricted` | "What should I do with my money?" | restrict |
| `bank_stability_restricted` | "Is bank X safe?" | restrict |

## Calculator

The calculator parses complex deposit descriptions and computes coverage per bank:

- Supports formats: `80.000 €`, `80,000`, `80000`, `80k`, `200K`, `50 k`
- Maps amounts to named banks
- Applies the 100,000 EUR limit per depositor per bank
- Reports insured totals, excess amounts, and per-bank breakdowns

## Project Structure

```
├── app.py                 # Streamlit web interface
├── classifier.py          # Intent classification (LLM + rules)
├── calculator.py          # Deposit coverage calculation
├── policy_engine.py       # Policy routing & knowledge base
├── guardrails.py          # Output filtering & compliance
├── llm.py                 # Gemini API integration
├── config.py              # Configuration, patterns, system prompts
├── knowledge_base.json    # Pre-approved responses (Croatian)
├── test_scenarios.py      # 18 test scenarios
├── requirements.txt       # Dependencies
└── .env.example           # Environment variable template
```

## Classification Modes

**LLM mode** (default) — Uses Gemini with a smart fallback strategy:
- If rules match with ≥90% confidence, skip the LLM call
- If a restricted category is detected at 70%+, skip the LLM call
- Otherwise, call the LLM for accurate classification
- Falls back to rules if the LLM is unavailable

**Rules mode** — Pattern matching only, no API calls needed. Works entirely offline.

## Guardrails

All responses pass through output filtering that blocks:
- Financial advice phrases ("trebao bi", "preporučujem")
- Bank stability predictions ("sigurna banka", "neće propasti")
- Guarantees ("garantiram", "100% sigurno")
- Imperative financial instructions ("stavi novac", "prebaci", "otvori račun")

Blocked responses are replaced with a standard disclaimer explaining Miran's informational-only role.

## Dependencies

- `streamlit>=1.28.0` — Web UI
- `google-generativeai>=0.3.0` — Gemini LLM
- `python-dotenv>=1.0.0` — Environment management

## License

This project was built for the Croatian Deposit Insurance Agency (HAOD).
