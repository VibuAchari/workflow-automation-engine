"""
transition_engine.py

Purpose:
--------
The SINGLE authority responsible for changing a case's state.

This module enforces the most critical system invariants:
---------------------------------------------------------
1. State transitions must follow the state machine.
2. All guard conditions must be satisfied BEFORE mutation.
3. State update and audit log insertion are ATOMIC.
4. Partial transitions are impossible.
5. Every successful transition is explainable and auditable.

This file must NEVER:
---------------------
- Compute business facts
- Call rule engines
- Call external services
- Contain UI or API logic

If you violate these rules, the system becomes untrustworthy.
"""

from core.state_machine import ALLOWED_TRANSITIONS
from core.transition_guards import TRANSITION_GUARDS
from core.guards import evaluate_guards, GuardViolation
from db.database import transaction


# -----------------------------------------------------------------------------
# Exceptions (explicit failure modes)
# -----------------------------------------------------------------------------

class IllegalTransition(Exception):
    """
    Raised when a transition violates the state machine.

    Example:
    --------
    CREATED -> APPROVED (illegal jump)
    """
    pass


# -----------------------------------------------------------------------------
# Transition Authority
# -----------------------------------------------------------------------------

def transition_case(
    *,
    case_id: str,
    from_state,
    to_state,
    facts: dict,
    reason: str,
    db_conn,
) -> None:
    """
    Attempts to transition a case from one state to another.

    Parameters:
    -----------
    case_id : str
        Unique identifier of the case.

    from_state : CaseState
        The current state of the case (caller must supply this explicitly).

    to_state : CaseState
        The desired target state.

    facts : dict
        Pre-computed facts about the case.
        These come from:
        - validators
        - rule engines
        - SLA checkers

        This function WILL NOT compute or mutate facts.

    reason : str
        Human-readable explanation for why this transition occurred.
        Stored permanently in the audit log.

    db_conn : sqlite3.Connection
        Active database connection.

    Raises:
    -------
    IllegalTransition
        If the state machine forbids this transition.

    GuardViolation
        If required guard conditions are not satisfied.

    Guarantees:
    -----------
    - Either BOTH the case state and audit log are written
      OR NEITHER is written.
    - No partial or silent failures are possible.
    """

    # -------------------------------------------------------------------------
    # 1. Structural legality check (state machine enforcement)
    # -------------------------------------------------------------------------

    allowed_targets = ALLOWED_TRANSITIONS.get(from_state, set())

    if to_state not in allowed_targets:
        raise IllegalTransition(
            f"Illegal transition: {from_state.value} -> {to_state.value}"
        )

    # -------------------------------------------------------------------------
    # 2. Guard validation (facts only, no computation)
    # -------------------------------------------------------------------------

    guard_key = (from_state, to_state)
    required_guards = TRANSITION_GUARDS.get(guard_key)

    if required_guards:
        evaluate_guards(required_guards, facts)

    # -------------------------------------------------------------------------
    # 3. Atomic persistence (state + audit log)
    # -------------------------------------------------------------------------

    # The transaction context manager guarantees:
    # - BEGIN before block
    # - COMMIT on success
    # - ROLLBACK on ANY exception
    with transaction(db_conn) as tx:

        # Update the authoritative current state
        tx.execute(
            """
            UPDATE cases
            SET current_state = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (to_state.value, case_id),
        )

        # Record the transition permanently
        tx.execute(
            """
            INSERT INTO audit_logs (
                case_id,
                from_state,
                to_state,
                reason,
                metadata
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                case_id,
                from_state.value,
                to_state.value,
                reason,
                str(facts),  # JSON serialization comes later
            ),
        )
def execute_transition(
    *,
    case_id: str,
    action: str,
    facts: dict,
) -> dict:
    """
    Public Transition Engine entry point.

    This function:
    - Loads current state internally
    - Maps 'action' → target state
    - Delegates to transition_case
    - Returns a structured result for orchestrators

    Orchestrators MUST call this function.
    """

    # ---------------------------------------------------------------------
    # 1. Load current state (internal concern)
    # ---------------------------------------------------------------------
    # NOTE: This assumes a DB accessor exists.
    # If not yet implemented, stub it for now.
    from db.database import get_connection

    db_conn = get_connection()

    cursor = db_conn.execute(
        "SELECT current_state FROM cases WHERE id = ?",
        (case_id,)
    )
    row = cursor.fetchone()

    if not row:
        raise Exception(f"Case not found: {case_id}")

    from_state_value = row[0]

    # Convert string → CaseState enum
    from core.state import CaseState
    from_state = CaseState(from_state_value)
    to_state = CaseState(action)

    # ---------------------------------------------------------------------
    # 2. Delegate to core transition authority
    # ---------------------------------------------------------------------
    transition_case(
        case_id=case_id,
        from_state=from_state,
        to_state=to_state,
        facts=facts,
        reason=f"Orchestrated transition to {action}",
        db_conn=db_conn,
    )

    # ---------------------------------------------------------------------
    # 3. Return structured result
    # ---------------------------------------------------------------------
    return {
        "new_state": to_state.value,
        "status": "SUCCESS",
        "audit_entry": {
            "case_id": case_id,
            "from_state": from_state.value,
            "to_state": to_state.value,
            "reason": f"Orchestrated transition to {action}",
        }
    }
