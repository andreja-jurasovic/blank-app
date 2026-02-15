"""
Deposit Coverage Calculator Module for HAOD Digital Assistant

Calculates insured and uninsured amounts based on deposit insurance rules.
"""
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

from config import DEPOSIT_LIMIT


def normalize_amounts(text: str) -> str:
    """
    Normalize shorthand amount formats to plain numbers.
    Handles: 100k, 200K, 100 k, 1.5k, etc.
    """
    # "100k" / "200K" / "100 k" → multiply by 1000
    def replace_k(match):
        num = match.group(1).replace(",", ".").strip()
        return str(int(float(num) * 1000))

    text = re.sub(r'(\d+(?:[.,]\d+)?)\s*[kK]\b', replace_k, text)
    return text


@dataclass
class BankDeposit:
    """Represents a deposit in a single bank."""
    bank_name: str
    amount: float
    insured: float = 0.0
    excess: float = 0.0


@dataclass
class CalculationResult:
    """Result of coverage calculation."""
    deposits: List[BankDeposit]
    total_amount: float
    total_insured: float
    total_excess: float

    def format_result(self) -> str:
        """Format the calculation result for display."""
        lines = []

        for i, dep in enumerate(self.deposits, 1):
            bank_label = dep.bank_name or f"Banka {i}"
            lines.append(f"- **{bank_label}: {dep.amount:,.0f} €**")

            if dep.amount <= DEPOSIT_LIMIT:
                lines.append(f"  - Cijeli iznos je unutar limita od {DEPOSIT_LIMIT:,} €")
                lines.append(f"  - Osigurano: {dep.insured:,.0f} €")
            else:
                lines.append(f"  - Do {DEPOSIT_LIMIT:,} € je unutar limita")
                lines.append(f"  - Osigurano: {dep.insured:,.0f} €")
                lines.append(f"  - Iznad limita: {dep.excess:,.0f} € (nije pokriveno)")

        lines.append("")
        lines.append("**Ukupno:**")
        lines.append(f"- Ukupni depoziti: {self.total_amount:,.0f} €")
        lines.append(f"- Osigurano: {self.total_insured:,.0f} €")
        if self.total_excess > 0:
            lines.append(f"- Neosigurano (iznad limita): {self.total_excess:,.0f} €")

        return "\n".join(lines)


def extract_amount(text: str) -> Optional[float]:
    """
    Extract a single monetary amount from text.
    Handles formats: 80.000, 80,000, 80000

    Returns:
        Amount as float or None if not found
    """
    # Try European format first (80.000)
    match = re.search(r'(\d{1,3}(?:\.\d{3})+)', text)
    if match:
        clean = match.group(1).replace(".", "")
        return float(clean)

    # Try US format (80,000)
    match = re.search(r'(\d{1,3}(?:,\d{3})+)', text)
    if match:
        clean = match.group(1).replace(",", "")
        return float(clean)

    # Try plain number (80000)
    match = re.search(r'(\d{4,})', text)
    if match:
        return float(match.group(1))

    return None


def extract_all_amounts(text: str) -> List[float]:
    """
    Extract all monetary amounts from text in order of appearance.

    Returns:
        List of amounts as floats
    """
    amounts = []

    # Find all European format numbers (80.000)
    for match in re.finditer(r'\d{1,3}(?:\.\d{3})+', text):
        clean = match.group().replace(".", "")
        amount = float(clean)
        if amount >= 1000:
            amounts.append((match.start(), amount))

    # Find all plain large numbers not already matched
    for match in re.finditer(r'\d{5,}', text):
        amount = float(match.group())
        # Check if this position overlaps with already found amounts
        pos = match.start()
        if not any(abs(pos - p) < 10 for p, _ in amounts):
            if amount >= 1000:
                amounts.append((pos, amount))

    # Sort by position and return just amounts
    amounts.sort(key=lambda x: x[0])
    return [a for _, a in amounts]


def find_amount_near_position(text: str, indicator_pos: int, indicator_len: int) -> Optional[float]:
    """
    Find the monetary amount associated with a bank indicator.
    Looks both before and after the indicator position.

    Strategy:
    1. First look for amount BEFORE the indicator (pattern: "80.000 € u jednoj banci")
    2. If not found, look for amount AFTER the indicator (pattern: "u prvoj banci imam 80.000 €")
    """
    # Look BEFORE the indicator
    segment_before = text[:indicator_pos]
    amounts_before = []

    for match in re.finditer(r'\d{1,3}(?:\.\d{3})+', segment_before):
        clean = match.group().replace(".", "")
        amount = float(clean)
        if amount >= 1000:
            amounts_before.append((match.end(), amount))

    for match in re.finditer(r'\d{5,}', segment_before):
        amount = float(match.group())
        pos_match = match.end()
        if not any(abs(pos_match - p) < 5 for p, _ in amounts_before):
            if amount >= 1000:
                amounts_before.append((pos_match, amount))

    if amounts_before:
        # Return the amount closest to the indicator
        amounts_before.sort(key=lambda x: x[0], reverse=True)
        return amounts_before[0][1]

    # Look AFTER the indicator (within reasonable distance)
    after_start = indicator_pos + indicator_len
    segment_after = text[after_start:after_start + 50]  # Look within 50 chars

    for match in re.finditer(r'\d{1,3}(?:\.\d{3})+', segment_after):
        clean = match.group().replace(".", "")
        amount = float(clean)
        if amount >= 1000:
            return amount

    for match in re.finditer(r'\d{5,}', segment_after):
        amount = float(match.group())
        if amount >= 1000:
            return amount

    return None


def parse_multi_bank_amounts(text: str) -> List[Tuple[str, float]]:
    """
    Parse text for amounts in multiple banks.
    Handles patterns like:
    - "X € u jednoj banci i Y € u drugoj"
    - "u prvoj banci imam X €, a u drugoj banci Y €"

    Args:
        text: Input text

    Returns:
        List of (bank_name, amount) tuples
    """
    text = normalize_amounts(text)
    text_lower = text.lower()

    # First, extract all amounts with their positions
    all_amounts = []
    for match in re.finditer(r'\d{1,3}(?:\.\d{3})+', text):
        clean = match.group().replace(".", "")
        amount = float(clean)
        if amount >= 1000:
            all_amounts.append((match.start(), match.end(), amount))

    for match in re.finditer(r'\d{5,}', text):
        amount = float(match.group())
        pos = match.start()
        if not any(abs(pos - s) < 5 for s, _, _ in all_amounts):
            if amount >= 1000:
                all_amounts.append((match.start(), match.end(), amount))

    all_amounts.sort(key=lambda x: x[0])

    if not all_amounts:
        return []

    # Bank indicator patterns with their labels
    bank_indicators = [
        (["u jednoj banci", "u prvoj banci", "u 1. banci"], "Prva banka"),
        (["u drugoj banci", "u drugoj", "u 2. banci"], "Druga banka"),
        (["u trećoj banci", "u 3. banci"], "Treća banka"),
    ]

    # Find positions of all bank indicators
    found_banks = []
    for indicators, bank_name in bank_indicators:
        for indicator in indicators:
            pos = text_lower.find(indicator)
            if pos != -1:
                found_banks.append((pos, len(indicator), bank_name))
                break

    found_banks.sort(key=lambda x: x[0])

    results = []
    used_amounts = set()

    if found_banks:
        # Match each bank indicator with the closest unassigned amount
        for bank_pos, indicator_len, bank_name in found_banks:
            best_amount = None
            best_distance = float('inf')
            best_idx = -1

            for idx, (start, end, amount) in enumerate(all_amounts):
                if idx in used_amounts:
                    continue

                # Calculate distance: amount before indicator, or amount after indicator
                if end <= bank_pos:
                    # Amount is before indicator
                    distance = bank_pos - end
                elif start >= bank_pos + indicator_len:
                    # Amount is after indicator
                    distance = start - (bank_pos + indicator_len)
                else:
                    # Amount overlaps with indicator (shouldn't happen)
                    continue

                if distance < best_distance:
                    best_distance = distance
                    best_amount = amount
                    best_idx = idx

            if best_amount is not None and best_distance < 100:  # Max 100 chars away
                results.append((bank_name, best_amount))
                used_amounts.add(best_idx)

    # If we didn't find bank-specific patterns, assign amounts sequentially
    if not results:
        bank_names = ["Prva banka", "Druga banka", "Treća banka", "Četvrta banka"]
        for idx, (_, _, amount) in enumerate(all_amounts):
            if idx < len(bank_names):
                results.append((bank_names[idx], amount))
            else:
                results.append((f"Banka {idx + 1}", amount))

    return results


def calculate_coverage(amounts: List[float]) -> Tuple[float, float]:
    """
    Calculate total insured and excess amounts.

    Args:
        amounts: List of deposit amounts (each representing a different bank)

    Returns:
        Tuple of (total_insured, total_excess)
    """
    total_insured = sum(min(a, DEPOSIT_LIMIT) for a in amounts)
    total_excess = sum(max(0, a - DEPOSIT_LIMIT) for a in amounts)
    return total_insured, total_excess


def calculate_full(text: str) -> CalculationResult:
    """
    Full calculation with detailed breakdown per bank.

    Args:
        text: User input text containing deposit amounts

    Returns:
        CalculationResult with full breakdown
    """
    bank_amounts = parse_multi_bank_amounts(text)

    deposits = []
    for bank_name, amount in bank_amounts:
        insured = min(amount, DEPOSIT_LIMIT)
        excess = max(0, amount - DEPOSIT_LIMIT)
        deposits.append(BankDeposit(
            bank_name=bank_name,
            amount=amount,
            insured=insured,
            excess=excess
        ))

    total_amount = sum(d.amount for d in deposits)
    total_insured = sum(d.insured for d in deposits)
    total_excess = sum(d.excess for d in deposits)

    return CalculationResult(
        deposits=deposits,
        total_amount=total_amount,
        total_insured=total_insured,
        total_excess=total_excess
    )


# Test utility
if __name__ == "__main__":
    test_cases = [
        "Miran, recimo da imam 80.000 € u jednoj banci i 150.000 € u drugoj. Koliko mi je od toga osigurano?",
        "Miran, ako se baš sad dogodi najgore: imam 60.000 € u jednoj banci i 140.000 € u drugoj. Koliko bi od toga bilo sigurno pokriveno?",
        "Imam 200.000 eura u banci.",
        "U prvoj banci imam 50.000 €, a u drugoj banci 75.000 €.",
    ]

    for q in test_cases:
        print(f"\nQ: {q[:70]}...")
        result = calculate_full(q)
        print(f"Deposits: {[(d.bank_name, d.amount) for d in result.deposits]}")
        print(f"Insured: {result.total_insured:,.0f} € | Excess: {result.total_excess:,.0f} €")
