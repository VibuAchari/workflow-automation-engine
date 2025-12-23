#5.1 Illegal transition must fail
import pytest
from core.state import CaseState
from core.transition_engine import transition_case, IllegalTransition
from tests.helpers import insert_case


def test_illegal_transition_rejected(db_conn):
    insert_case(db_conn, "c1", CaseState.CREATED)

    with pytest.raises(IllegalTransition):
        transition_case(
            case_id="c1",
            from_state=CaseState.CREATED,
            to_state=CaseState.APPROVED,  # illegal jump
            facts={},
            reason="Invalid jump",
            db_conn=db_conn,
        )


#5.2 Guard failure blocks transition AND rolls back
def test_guard_failure_blocks_transition(db_conn):
    insert_case(db_conn, "c2", CaseState.CREATED)

    with pytest.raises(Exception):
        transition_case(
            case_id="c2",
            from_state=CaseState.CREATED,
            to_state=CaseState.UNDER_REVIEW,
            facts={"required_fields_complete": False},
            reason="Missing fields",
            db_conn=db_conn,
        )

    row = db_conn.execute(
        "SELECT current_state FROM cases WHERE id = ?",
        ("c2",),
    ).fetchone()

    assert row["current_state"] == CaseState.CREATED.value


#5.3 Valid transition succeeds
def test_valid_transition_succeeds(db_conn):
    insert_case(db_conn, "c3", CaseState.CREATED)

    transition_case(
        case_id="c3",
        from_state=CaseState.CREATED,
        to_state=CaseState.UNDER_REVIEW,
        facts={"required_fields_complete": True},
        reason="Initial review",
        db_conn=db_conn,
    )

    row = db_conn.execute(
        "SELECT current_state FROM cases WHERE id = ?",
        ("c3",),
    ).fetchone()

    assert row["current_state"] == CaseState.UNDER_REVIEW.value


#5.4 Audit log must exist for successful transition
def test_audit_log_written(db_conn):
    insert_case(db_conn, "c4", CaseState.CREATED)

    transition_case(
        case_id="c4",
        from_state=CaseState.CREATED,
        to_state=CaseState.UNDER_REVIEW,
        facts={"required_fields_complete": True},
        reason="Audit test",
        db_conn=db_conn,
    )

    row = db_conn.execute(
        """
        SELECT from_state, to_state, reason
        FROM audit_logs
        WHERE case_id = ?
        """,
        ("c4",),
    ).fetchone()

    assert row["from_state"] == CaseState.CREATED.value
    assert row["to_state"] == CaseState.UNDER_REVIEW.value
    assert row["reason"] == "Audit test"

"""
5.5 Atomicity: no ghost updates

We simulate a failure inside the transaction.
"""
def test_atomicity_no_partial_commit(db_conn):
    insert_case(db_conn, "c5", CaseState.CREATED)

    # Break audit logging intentionally
    db_conn.execute("DROP TABLE audit_logs")

    with pytest.raises(Exception):
        transition_case(
            case_id="c5",
            from_state=CaseState.CREATED,
            to_state=CaseState.UNDER_REVIEW,
            facts={"required_fields_complete": True},
            reason="Should rollback",
            db_conn=db_conn,
        )

    row = db_conn.execute(
        "SELECT current_state FROM cases WHERE id = ?",
        ("c5",),
    ).fetchone()

    assert row["current_state"] == CaseState.CREATED.value
