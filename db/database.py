"""
database.py

Purpose:
--------
Provides database connection and transaction management
for the Workflow Automation Engine.

Design Principles:
------------------
1. This file handles INFRASTRUCTURE, not business logic.
2. It must not know about states, rules, or transitions.
3. It must make atomic operations POSSIBLE.
4. All higher layers assume this file is correct.

This module is intentionally simple.
If it becomes complex, something above is leaking responsibility.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator


# -----------------------------------------------------------------------------
# Database Connection
# -----------------------------------------------------------------------------

def get_connection(db_path: str) -> sqlite3.Connection:
    """
    Creates and returns a SQLite database connection.

    Parameters:
    -----------
    db_path : str
        Path to the SQLite database file.
        Use ':memory:' for in-memory databases (testing).

    Returns:
    --------
    sqlite3.Connection
        A live database connection.

    Important Configuration:
    ------------------------
    - row_factory enables name-based column access
    - isolation_level=None enables manual transaction control
    """

    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )

    # Enables dict-like row access (row["current_state"])
    conn.row_factory = sqlite3.Row

    return conn


# -----------------------------------------------------------------------------
# Transaction Management
# -----------------------------------------------------------------------------

@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager to execute a block of database operations atomically.

    Usage:
    ------
    with transaction(conn) as tx:
        tx.execute(...)
        tx.execute(...)

    Guarantees:
    -----------
    - Commits if block completes successfully
    - Rolls back if ANY exception occurs
    - Leaves no partial state behind

    Why this exists:
    ----------------
    SQLite auto-commits by default.
    That is dangerous for state transitions.

    This context manager gives us:
    - explicit transaction boundaries
    - predictable rollback behavior
    """

    try:
        conn.execute("BEGIN")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
