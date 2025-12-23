"""
state_machine.py

Purpose:
--------
Defines which state transitions are legally allowed.

This is the "constitution" of the workflow engine.

Key principle:
--------------
If a transition is not listed here, it does not exist.
No guard, rule, or API may bypass this definition.
"""

from core.state import CaseState


# Mapping: current_state -> set of allowed next states
ALLOWED_TRANSITIONS = {
    CaseState.CREATED: {
        CaseState.UNDER_REVIEW,
    },

    CaseState.UNDER_REVIEW: {
        CaseState.APPROVED,
        CaseState.REJECTED,
        CaseState.ESCALATED,
        CaseState.WAITING_INFO,
    },

    CaseState.WAITING_INFO: {
        CaseState.UNDER_REVIEW,
    },

    CaseState.ESCALATED: {
        CaseState.UNDER_REVIEW,
        CaseState.APPROVED,
        CaseState.REJECTED,
    },

    CaseState.APPROVED: {
        CaseState.CLOSED,
    },

    CaseState.REJECTED: {
        CaseState.CLOSED,
    },

    CaseState.CLOSED: set(),  # Terminal state
}
