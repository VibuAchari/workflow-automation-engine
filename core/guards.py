"""
guards.py

Purpose:
--------
Provides a generic mechanism to validate guard conditions
before allowing a state transition.

Key Design Principles:
----------------------
1. Guards NEVER compute facts.
2. Guards ONLY compare expected values against provided facts.
3. Guards are deterministic and side-effect free.
4. Any failure must be explicit and explainable.

This file must NOT:
-------------------
- Access the database
- Call rule engines
- Compute business logic
- Modify facts

If you feel tempted to add logic here, you are breaking the architecture.
"""


class GuardViolation(Exception):
    """
    Raised when a guard condition is not satisfied.

    Why a dedicated exception?
    --------------------------
    - Allows the transition engine to distinguish
      between structural illegality and guard failure.
    - Makes test assertions precise.
    """
    pass


def evaluate_guards(required_guards: dict, facts: dict) -> None:
    """
    Validates that all required guard conditions are satisfied.

    Parameters:
    -----------
    required_guards : dict
        A mapping of fact_name -> expected_value.
        Example:
            {
                "risk_rules_passed": True,
                "no_pending_actions": True
            }

    facts : dict
        Snapshot of pre-computed facts about the case.
        Example:
            {
                "risk_rules_passed": True,
                "no_pending_actions": False,
                "amount": 12000
            }

    Raises:
    -------
    GuardViolation
        If any required guard is missing or has an unexpected value.

    Guarantees:
    -----------
    - Does not mutate input data
    - Does not compute or infer facts
    - Fails fast on first violation

    Notes for learners:
    -------------------
    This function is intentionally simple.
    Its power comes from *where* it is used, not *what* it does.
    """

    for guard_key, expected_value in required_guards.items():
        # Fetch the actual value from facts
        actual_value = facts.get(guard_key)

        # Guard fails if:
        # 1. Fact is missing
        # 2. Fact exists but value does not match expectation
        if actual_value != expected_value:
            raise GuardViolation(
                f"Guard failed: '{guard_key}' expected={expected_value}, actual={actual_value}"
            )
