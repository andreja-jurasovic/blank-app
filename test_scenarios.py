"""
Test Suite for HAOD Digital Assistant (Miran)

Tests all 18 demo scenarios from questions_answers.md
Run without API key to test classification and pipeline.
Run with API key to test full LLM integration.
"""
import sys
from typing import List, Tuple
from dataclasses import dataclass

from classifier import classify, classify_rules
from calculator import calculate_full
from policy_engine import get_policy_engine, get_knowledge_base
from guardrails import guardrail_check


@dataclass
class TestScenario:
    """A test scenario from the demo."""
    id: int
    name: str
    question: str
    expected_category: str
    expected_action: str  # respond, calculate, restrict
    expected_kb_entry: str  # Knowledge base entry ID
    check_calculation: bool = False
    expected_insured: float = 0
    expected_excess: float = 0


# All 18 test scenarios from questions_answers.md
TEST_SCENARIOS: List[TestScenario] = [
    TestScenario(
        id=1,
        name="What is HAOD",
        question="Bok Miran, što je točno HAOD i čime se vi bavite?",
        expected_category="general_info",
        expected_action="respond",
        expected_kb_entry="general_info",
    ),
    TestScenario(
        id=2,
        name="100k limit meaning",
        question="Svugdje piše 100.000 eura po osobi po banci. Što to točno znači za mene?",
        expected_category="limit_explanation",
        expected_action="respond",
        expected_kb_entry="limit_explanation",
    ),
    TestScenario(
        id=3,
        name="Bank failure - lose everything?",
        question="Ako moja banka propadne, znači li to da sam ostao bez svega?",
        expected_category="coverage",
        expected_action="respond",
        expected_kb_entry="bank_failure",
    ),
    TestScenario(
        id=4,
        name="Multiple banks coverage",
        question="Imam štednju u dvije banke. Gleda li se to sve skupa ili svaka banka posebno?",
        expected_category="coverage",
        expected_action="respond",
        expected_kb_entry="multiple_banks",
    ),
    TestScenario(
        id=5,
        name="Joint accounts",
        question="Suprug i ja imamo zajednički račun. Kako se tu računa ovih 100.000 eura?",
        expected_category="joint_accounts",
        expected_action="respond",
        expected_kb_entry="joint_accounts",
    ),
    TestScenario(
        id=6,
        name="Foreign currency deposits",
        question="Je li devizna štednja i oročena štednja isto u ovom sustavu osiguranja?",
        expected_category="foreign_currency",
        expected_action="respond",
        expected_kb_entry="foreign_currency",
    ),
    TestScenario(
        id=7,
        name="Account types",
        question="Koja je razlika za osiguranje između tekućeg, žiro i štednog računa? Je li sve to pokriveno?",
        expected_category="account_types",
        expected_action="respond",
        expected_kb_entry="account_types",
    ),
    TestScenario(
        id=8,
        name="What's NOT covered",
        question="Što od mojih ulaganja nije pokriveno ovim osiguranjem depozita?",
        expected_category="non_coverage",
        expected_action="respond",
        expected_kb_entry="non_coverage",
    ),
    TestScenario(
        id=9,
        name="EU banks",
        question="Ako imam novac u banci iz druge države EU, štiti li to HAOD?",
        expected_category="eu_banks",
        expected_action="respond",
        expected_kb_entry="eu_banks",
    ),
    TestScenario(
        id=10,
        name="Payout timing",
        question="Koliko bih dugo čekao novac ako banka propadne?",
        expected_category="payout_timing",
        expected_action="respond",
        expected_kb_entry="payout_timing",
    ),
    TestScenario(
        id=11,
        name="Calculate 80k + 150k",
        question="Miran, recimo da imam 80.000 € u jednoj banci i 150.000 € u drugoj. Koliko mi je od toga osigurano?",
        expected_category="limit_calc",
        expected_action="calculate",
        expected_kb_entry="limit_calc",
        check_calculation=True,
        expected_insured=180000,
        expected_excess=50000,
    ),
    TestScenario(
        id=12,
        name="Panic - news about bank",
        question="Miran, upravo sam na vijestima čuo da je moja banka u problemima. Moram li odmah trčati po novac?",
        expected_category="panic",
        expected_action="respond",
        expected_kb_entry="panic_news",
    ),
    TestScenario(
        id=13,
        name="Panic - everyone withdrawing",
        question="Čujem da svi dižu novac iz banke. Trebam li i ja isto napraviti?",
        expected_category="panic",
        expected_action="respond",
        expected_kb_entry="panic_withdrawal",
    ),
    TestScenario(
        id=14,
        name="Panic - over 100k worry",
        question="Miran, imam više od 100.000 € u jednoj banci. Znači li to da će sve iznad toga sigurno propasti?",
        expected_category="panic",
        expected_action="respond",
        expected_kb_entry="panic_over_limit",
    ),
    TestScenario(
        id=15,
        name="Panic - no official news yet",
        question="Vijest je izašla navečer, svi pričaju, a nema još službenih obavijesti. Trebam li čekati ili odmah reagirati?",
        expected_category="panic",
        expected_action="respond",
        expected_kb_entry="panic_no_official",
    ),
    TestScenario(
        id=16,
        name="Bank stability (RESTRICTED)",
        question="Možeš li mi ti reći je li banka X sigurna ili hoće li propasti?",
        expected_category="bank_stability_restricted",
        expected_action="restrict",
        expected_kb_entry="bank_stability_restricted",
    ),
    TestScenario(
        id=17,
        name="Payout guarantee",
        question="Okej, svi govore o tih 100.000 €, ali koliko mogu biti siguran da će to stvarno biti isplaćeno ako banka propadne?",
        expected_category="coverage",
        expected_action="respond",
        expected_kb_entry="payout_guarantee",
    ),
    TestScenario(
        id=18,
        name="Crisis calc 60k + 140k",
        question="Miran, ako se baš sad dogodi najgore: imam 60.000 € u jednoj banci i 140.000 € u drugoj. Koliko bi od toga bilo sigurno pokriveno osiguranjem depozita?",
        expected_category="limit_calc",
        expected_action="calculate",
        expected_kb_entry="limit_calc",
        check_calculation=True,
        expected_insured=160000,
        expected_excess=40000,
    ),
]


def test_classification() -> Tuple[int, int, List[str]]:
    """Test classification for all scenarios."""
    passed = 0
    failed = 0
    errors = []

    print("\n" + "=" * 70)
    print("CLASSIFICATION TESTS")
    print("=" * 70)

    for scenario in TEST_SCENARIOS:
        category, confidence = classify_rules(scenario.question)

        if category == scenario.expected_category:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1
            errors.append(
                f"Q{scenario.id}: Expected '{scenario.expected_category}', got '{category}'"
            )

        print(f"{status} Q{scenario.id:2d} [{scenario.name[:30]:<30}] → {category} ({confidence:.0%})")

    return passed, failed, errors


def test_policy_routing() -> Tuple[int, int, List[str]]:
    """Test policy engine routing for all scenarios."""
    passed = 0
    failed = 0
    errors = []

    pe = get_policy_engine()

    print("\n" + "=" * 70)
    print("POLICY ROUTING TESTS")
    print("=" * 70)

    for scenario in TEST_SCENARIOS:
        category, confidence = classify_rules(scenario.question)
        decision = pe.evaluate(category, confidence, scenario.question)

        action_ok = decision.action == scenario.expected_action
        entry_ok = (decision.knowledge_entry and
                   decision.knowledge_entry.id == scenario.expected_kb_entry)

        if action_ok and entry_ok:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1
            actual_entry = decision.knowledge_entry.id if decision.knowledge_entry else "None"
            if not action_ok:
                errors.append(
                    f"Q{scenario.id}: Action expected '{scenario.expected_action}', got '{decision.action}'"
                )
            if not entry_ok:
                errors.append(
                    f"Q{scenario.id}: Entry expected '{scenario.expected_kb_entry}', got '{actual_entry}'"
                )

        entry_id = decision.knowledge_entry.id if decision.knowledge_entry else "None"
        print(f"{status} Q{scenario.id:2d} action={decision.action:<10} entry={entry_id}")

    return passed, failed, errors


def test_calculations() -> Tuple[int, int, List[str]]:
    """Test calculator for calculation scenarios."""
    passed = 0
    failed = 0
    errors = []

    print("\n" + "=" * 70)
    print("CALCULATION TESTS")
    print("=" * 70)

    calc_scenarios = [s for s in TEST_SCENARIOS if s.check_calculation]

    for scenario in calc_scenarios:
        result = calculate_full(scenario.question)

        insured_ok = abs(result.total_insured - scenario.expected_insured) < 1
        excess_ok = abs(result.total_excess - scenario.expected_excess) < 1

        if insured_ok and excess_ok:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1
            errors.append(
                f"Q{scenario.id}: Expected {scenario.expected_insured}/{scenario.expected_excess}, "
                f"got {result.total_insured}/{result.total_excess}"
            )

        print(f"{status} Q{scenario.id:2d} Insured: {result.total_insured:>10,.0f} €  Excess: {result.total_excess:>10,.0f} €")
        for dep in result.deposits:
            print(f"      {dep.bank_name}: {dep.amount:,.0f} € → {dep.insured:,.0f} € insured")

    return passed, failed, errors


def test_guardrails() -> Tuple[int, int, List[str]]:
    """Test guardrails filtering."""
    passed = 0
    failed = 0
    errors = []

    print("\n" + "=" * 70)
    print("GUARDRAILS TESTS")
    print("=" * 70)

    test_cases = [
        ("Safe response", "Limit od 100.000 eura pokriva tvoj depozit.", True),
        ("Contains advice", "Preporučujem da povučeš novac odmah.", False),
        ("Bank stability claim", "Ova banka je sigurna, ne brini.", False),
        ("Guarantee claim", "Garantiram da ćeš dobiti novac.", False),
        ("Safe with numbers", "Osigurano je 80.000 € od ukupno 150.000 €.", True),
    ]

    for name, text, should_pass in test_cases:
        result = guardrail_check(text)
        actually_passed = (result == text)

        if actually_passed == should_pass:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1
            errors.append(f"Guardrail '{name}': expected pass={should_pass}, got {actually_passed}")

        outcome = "PASS" if actually_passed else "BLOCKED"
        print(f"{status} {name:<25} → {outcome}")

    return passed, failed, errors


def test_knowledge_base() -> Tuple[int, int, List[str]]:
    """Test knowledge base completeness."""
    passed = 0
    failed = 0
    errors = []

    print("\n" + "=" * 70)
    print("KNOWLEDGE BASE TESTS")
    print("=" * 70)

    kb = get_knowledge_base()

    # Check all expected entries exist
    expected_entries = set(s.expected_kb_entry for s in TEST_SCENARIOS)

    for entry_id in expected_entries:
        if entry_id in kb.by_id:
            status = "✓"
            passed += 1
            entry = kb.by_id[entry_id]
            print(f"{status} {entry_id:<30} → {entry.title[:40]}")
        else:
            status = "✗"
            failed += 1
            errors.append(f"Missing KB entry: {entry_id}")
            print(f"{status} {entry_id:<30} → MISSING!")

    print(f"\nTotal KB entries: {len(kb.entries)}")
    print(f"Categories: {len(kb.by_category)}")

    return passed, failed, errors


def run_all_tests():
    """Run all test suites and print summary."""
    print("\n" + "=" * 70)
    print("  MIRAN - HAOD DIGITAL ASSISTANT TEST SUITE")
    print("=" * 70)

    all_passed = 0
    all_failed = 0
    all_errors = []

    # Run each test suite
    suites = [
        ("Classification", test_classification),
        ("Policy Routing", test_policy_routing),
        ("Calculations", test_calculations),
        ("Guardrails", test_guardrails),
        ("Knowledge Base", test_knowledge_base),
    ]

    for name, test_func in suites:
        passed, failed, errors = test_func()
        all_passed += passed
        all_failed += failed
        all_errors.extend(errors)

    # Print summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print(f"  Total Passed: {all_passed}")
    print(f"  Total Failed: {all_failed}")
    print(f"  Success Rate: {all_passed / (all_passed + all_failed) * 100:.1f}%")

    if all_errors:
        print("\n  ERRORS:")
        for error in all_errors:
            print(f"    • {error}")

    print("=" * 70)

    return all_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
