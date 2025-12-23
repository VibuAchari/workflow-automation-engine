"""
transition_guards.py

Purpose:
--------
Defines guard requirements for specific state transitions.

This file is purely declarative:
-------------------------------
- No computation
- No conditionals
- No database access
- No business logic

Think of this as a POLICY TABLE, not executable logic.

If a transition is not listed here:
-----------------------------------
- It has NO guards
- It only needs to be structurally legal
"""

from core.state import CaseState


# Mapping:
# (from_state, to_state) -> { fact_name: expected_value }
TRANSITION_GUARDS = {

    # Case can move to review only if required data is present
    (CaseState.CREATED, CaseState.UNDER_REVIEW): {
        "required_fields_complete": True,
    },

    # Approval requires successful risk evaluation
    (CaseState.UNDER_REVIEW, CaseState.APPROVED): {
        "risk_rules_passed": True,
        "amount_within_threshold": True,
    },

    # Rejection is allowed when validation explicitly fails
    (CaseState.UNDER_REVIEW, CaseState.REJECTED): {
        "validation_failed": True,
    },

    # Escalation happens due to risk or time pressure
    (CaseState.UNDER_REVIEW, CaseState.ESCALATED): {
        "high_amount": True,
    },

    # Pause workflow until missing information is provided
    (CaseState.UNDER_REVIEW, CaseState.WAITING_INFO): {
        "missing_info_detected": True,
    },

    # Closing is allowed only when no async work remains
    (CaseState.APPROVED, CaseState.CLOSED): {
        "no_pending_actions": True,
    },

    (CaseState.REJECTED, CaseState.CLOSED): {
        "no_pending_actions": True,
    },

    # Escalated cases must be reviewed before re-entering flow
    (CaseState.ESCALATED, CaseState.UNDER_REVIEW): {
        "supervisor_review_complete": True,
    },

    # Resume review after user provides required information
    (CaseState.WAITING_INFO, CaseState.UNDER_REVIEW): {
        "additional_info_provided": True,
    },
}
