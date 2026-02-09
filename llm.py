"""
LLM Module for HAOD Digital Assistant

Handles all Gemini API interactions for classification and answer formatting.
"""
import google.generativeai as genai

from config import (
    GEMINI_API_KEY,
    MODEL_NAME,
    CLASSIFIER_TEMPERATURE,
    FORMATTER_TEMPERATURE,
    CLASSIFIER_SYSTEM_PROMPT,
    FORMATTER_SYSTEM_PROMPT,
    ANSWER_PROMPT_TEMPLATE,
    CATEGORIES,
)


# Configure Gemini
def init_gemini():
    """Initialize Gemini with API key."""
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        raise ValueError("GEMINI_API_KEY not set. Please set it in environment or config.")


def classify_intent(text: str) -> str:
    """
    Classify user intent using Gemini LLM.

    Args:
        text: User input text

    Returns:
        Category name from CATEGORIES list
    """
    init_gemini()

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=genai.GenerationConfig(
            temperature=CLASSIFIER_TEMPERATURE,
            max_output_tokens=50,
        ),
        system_instruction=CLASSIFIER_SYSTEM_PROMPT,
    )

    response = model.generate_content(
        text,
        request_options={"timeout": 15},
    )

    # Check if response was blocked
    if not response.candidates or not response.candidates[0].content.parts:
        raise ValueError(f"Empty response from Gemini (finish_reason: {response.candidates[0].finish_reason if response.candidates else 'no candidates'})")

    result = response.text.strip().lower()

    # Validate result is a known category
    if result in CATEGORIES:
        return result

    # Try to find partial match
    for cat in CATEGORIES:
        if cat in result or result in cat:
            return cat

    # Default fallback
    return "general_info"


def format_answer(question: str, approved_answer: str, calculation_result: str = "") -> str:
    """
    Format the final answer using Gemini in Miran's tone.

    Args:
        question: Original user question
        approved_answer: Approved content from knowledge base
        calculation_result: Optional calculation results to include

    Returns:
        Formatted answer in Croatian
    """
    init_gemini()

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=genai.GenerationConfig(
            temperature=FORMATTER_TEMPERATURE,
            max_output_tokens=1000,
        ),
        system_instruction=FORMATTER_SYSTEM_PROMPT,
    )

    prompt = ANSWER_PROMPT_TEMPLATE.format(
        question=question,
        approved_answer=approved_answer,
        calculation_result=calculation_result if calculation_result else "",
    )

    response = model.generate_content(
        prompt,
        request_options={"timeout": 20},
    )
    return response.text.strip()


def format_restricted_response(approved_answer: str) -> str:
    """
    For restricted categories, return the template with minimal formatting.
    No LLM processing to ensure strict compliance.

    Args:
        approved_answer: Pre-approved refusal template

    Returns:
        Formatted refusal response
    """
    # For restricted responses, we return the approved answer directly
    # to ensure no LLM hallucination or modification
    return approved_answer
