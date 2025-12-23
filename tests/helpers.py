"""
helpers.py

Utility helpers for setting up test data.

These helpers:
---------------
- Insert minimal valid rows
- Do NOT perform transitions
- Do NOT contain logic
"""

from core.state import CaseState


def insert_case(conn, case_id: str, state: CaseState):
    """
    Inserts a case with a known state.

    This bypasses the transition engine intentionally,
    because tests need controlled starting conditions.
    """

    conn.execute(
        """
        INSERT INTO cases (id, title, current_state, data)
        VALUES (?, ?, ?, ?)
        """,
        (case_id, "Test Case", state.value, "{}"),
    )
    conn.commit()
