"""
conftest.py

Provides shared pytest fixtures.

Key guarantee:
--------------
Each test gets a clean, isolated database.
No state leakage. No order dependence.
"""

import sqlite3
import pytest
from pathlib import Path
import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH for pytest
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def db_conn():
    """
    Provides a fresh in-memory SQLite database for each test.

    Why in-memory?
    --------------
    - Fast
    - Isolated
    - Deterministic
    """

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Load schema
    conn.executescript(
        """
        CREATE TABLE cases (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            current_state TEXT NOT NULL,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            from_state TEXT NOT NULL,
            to_state TEXT NOT NULL,
            reason TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    yield conn

    conn.close()
