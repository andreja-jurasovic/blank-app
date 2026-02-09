"""
HAOD Digital Assistant (Miran) - Streamlit Application

Main application entry point demonstrating Policy-Controlled LLM Architecture.
Designed for client demos showcasing Enterprise AI Governance.
"""
import streamlit as st
from dataclasses import dataclass
from typing import Optional
import os
from datetime import datetime

from classifier import classify
from config import CLASSIFICATION_MODE
from calculator import calculate_full, CalculationResult
from policy_engine import get_policy_engine
from guardrails import guardrail_check, validate_response_length

# Check if LLM is available
LLM_AVAILABLE = bool(os.getenv("GEMINI_API_KEY"))

# Try to import LLM functions
try:
    from llm import format_answer, format_restricted_response
except Exception:
    LLM_AVAILABLE = False


@dataclass
class ProcessingResult:
    """Result of processing a user question."""
    category: str
    confidence: float
    action: str
    calculation: Optional[CalculationResult]
    response: str
    debug_info: dict


def log_debug(question: str, result: ProcessingResult, classification_mode: str):
    """Print debug information to terminal."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[{timestamp}] NEW QUERY")
    print(f"{'='*60}")
    print(f"Question: {question}")
    print(f"Classification Mode: {classification_mode}")
    print(f"Category: {result.category} ({result.confidence:.0%})")
    print(f"Action: {result.action}")
    print(f"KB Entry: {result.debug_info.get('entry_id', 'N/A')}")
    print(f"LLM Formatting: {result.debug_info.get('llm_used', False)}")

    if result.calculation:
        print(f"\nCalculation:")
        for dep in result.calculation.deposits:
            print(f"  - {dep.bank_name}: {dep.amount:,.0f}€ → {dep.insured:,.0f}€ insured")
        print(f"  Total Insured: {result.calculation.total_insured:,.0f}€")
        print(f"  Total Excess: {result.calculation.total_excess:,.0f}€")

    print(f"{'='*60}\n")


def process_question(question: str, use_llm: bool = True) -> ProcessingResult:
    """
    Process a user question through the full pipeline.
    """
    # Step 1: Classify intent
    category, confidence = classify(question)

    # Step 2: Evaluate policy
    policy_engine = get_policy_engine()
    decision = policy_engine.evaluate(category, confidence, question)

    # Step 3: Get approved answer
    approved_answer = policy_engine.get_approved_answer(decision)

    # Initialize result
    calculation = None
    response = ""

    # Step 4 & 5: Generate response based on action
    if decision.action == "restrict":
        if use_llm and LLM_AVAILABLE:
            response = format_restricted_response(approved_answer)
        else:
            response = approved_answer

    elif decision.action == "calculate":
        calculation = calculate_full(question)
        calc_text = calculation.format_result()

        # Never send calculation results through the LLM - it gets confused by math.
        # The calculator already formats results correctly.
        response = f"{approved_answer}\n\n**Izračun:**\n{calc_text}"

    else:
        if use_llm and LLM_AVAILABLE:
            try:
                response = format_answer(
                    question=question,
                    approved_answer=approved_answer,
                    calculation_result=""
                )
            except Exception:
                response = approved_answer
        else:
            response = approved_answer

    # Step 6: Apply guardrails
    response = guardrail_check(response)
    response = validate_response_length(response)

    return ProcessingResult(
        category=decision.category,
        confidence=decision.confidence,
        action=decision.action,
        calculation=calculation,
        response=response,
        debug_info={
            "entry_id": decision.knowledge_entry.id if decision.knowledge_entry else None,
            "entry_title": decision.knowledge_entry.title if decision.knowledge_entry else None,
            "llm_used": use_llm and LLM_AVAILABLE,
        }
    )


# Example questions for demo
EXAMPLE_QUESTIONS = [
    ("ℹ️ Općenito", "Što je HAOD i čime se bavite?"),
    ("💰 Limit", "Što znači limit od 100.000 eura po osobi po banci?"),
    ("🧮 Izračun", "Imam 80.000 € u jednoj banci i 150.000 € u drugoj. Koliko mi je osigurano?"),
    ("👫 Zajednički", "Suprug i ja imamo zajednički račun. Kako se računa limit?"),
    ("📰 Panika", "Čuo sam na vijestima da je moja banka u problemima. Što da radim?"),
    ("🚫 Ograničeno", "Je li banka X sigurna ili hoće li propasti?"),
]


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Miran - HAOD Digital Assistant",
        page_icon="🏦",
        layout="centered",
    )

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Header
    st.title("🏦 Miran")
    st.caption("Digitalni asistent za osiguranje depozita | HAOD Demo")

    st.markdown("""
    Pozdrav! Ja sam **Miran**, digitalni asistent Hrvatske agencije za osiguranje depozita.

    Mogu ti pomoći s informacijama o sustavu osiguranja depozita, izračunom pokrivenosti
    i odgovorima na pitanja o tvojoj štednji.

    *⚠️ Ne dajem financijske savjete niti procjenjujem stabilnost banaka.*
    """)

    st.divider()

    # Example questions in a cleaner layout
    st.markdown("**Primjeri pitanja:**")
    cols = st.columns(3)
    for idx, (emoji_label, question) in enumerate(EXAMPLE_QUESTIONS):
        with cols[idx % 3]:
            if st.button(emoji_label, key=f"ex_{idx}", use_container_width=True):
                # Add to messages and process
                st.session_state.messages.append({"role": "user", "content": question})
                result = process_question(question, use_llm=LLM_AVAILABLE)
                log_debug(question, result, "llm" if LLM_AVAILABLE else "rules")
                st.session_state.messages.append({"role": "assistant", "content": result.response})
                st.rerun()

    st.divider()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Postavi pitanje o osiguranju depozita..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process and display response
        with st.chat_message("assistant"):
            with st.spinner("Razmišljam..."):
                result = process_question(prompt, use_llm=LLM_AVAILABLE)
                log_debug(prompt, result, "llm" if LLM_AVAILABLE else "rules")
            st.markdown(result.response)

        st.session_state.messages.append({"role": "assistant", "content": result.response})

    # Clear button in sidebar
    with st.sidebar:
        st.markdown("### Opcije")
        if st.button("🗑️ Očisti razgovor", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.divider()
        llm_status = "🟢 LLM Aktivan" if LLM_AVAILABLE else "🟡 Demo Mode"
        st.markdown(f"**Status:** {llm_status}")
        st.caption("Debug info se ispisuje u terminal.")


if __name__ == "__main__":
    main()
