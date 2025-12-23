/*
===============================================================================
schema.sql

Purpose:
--------
Defines the persistent data model for the Workflow Automation Engine.

Design Philosophy:
------------------
1. The database is the RECORD OF TRUTH, not a cache.
2. Current state and historical state are deliberately separated.
3. State transitions must be auditable, reconstructable, and immutable.
4. No table in this schema is allowed to encode business logic.

This schema supports PHASE 1 ONLY:
----------------------------------
- Case state storage
- State transition history (audit logs)
- Atomic transition guarantees (via transactions in code)

Future phases will EXTEND this schema — not mutate its intent.
===============================================================================
*/


/*
===============================================================================
TABLE: cases
===============================================================================

Purpose:
--------
Stores the CURRENT, authoritative state of each case.

Important:
----------
- This table represents "what the system believes right now".
- It does NOT store history.
- Any corruption here must be detectable by cross-checking audit_logs.

Key Invariants:
---------------
1. Exactly one row per case.
2. current_state must ALWAYS reflect the last successful transition.
3. updated_at only changes on successful state transitions.
*/

CREATE TABLE IF NOT EXISTS cases (
    -- Primary identifier for the case.
    -- UUID is recommended at the application level.
    id TEXT PRIMARY KEY,

    -- Human-readable label.
    -- Purely informational; never used in logic.
    title TEXT NOT NULL,

    -- The single source of truth for the case's current state.
    -- Validity is enforced by the transition engine, NOT the database.
    current_state TEXT NOT NULL,

    /*
    Flexible JSON payload storing "facts" about the case.

    Examples:
    ---------
    {
        "amount": 12000,
        "customer_type": "NEW",
        "required_fields_complete": true
    }

    Rules:
    ------
    - This column stores WHAT IS TRUE, not WHAT TO DO.
    - Structure may vary across workflows.
    - The transition engine treats this as read-only input.
    */
    data TEXT,

    -- Timestamp when the case was first created.
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    /*
    Timestamp of the LAST SUCCESSFUL STATE TRANSITION.

    IMPORTANT:
    ----------
    - This must NOT be updated for:
        * data edits
        * comments
        * metadata changes
    - Only update when current_state changes.
    */
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


/*
===============================================================================
TABLE: audit_logs
===============================================================================

Purpose:
--------
Stores an immutable, append-only history of every state transition.

This table is the FORENSIC BACKBONE of the system.

If audit_logs is missing or corrupted:
--------------------------------------
- SLA analysis is impossible
- Compliance fails
- Debugging becomes guesswork
*/

CREATE TABLE IF NOT EXISTS audit_logs (
    -- Surrogate key for ordering and indexing.
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign key back to the case.
    -- Logical relationship; enforcement is done at the application layer.
    case_id TEXT NOT NULL,

    -- State before the transition.
    from_state TEXT NOT NULL,

    -- State after the transition.
    to_state TEXT NOT NULL,

    /*
    Human-readable explanation for WHY the transition occurred.

    Examples:
    ---------
    - "Initial submission complete"
    - "Risk rule R-104 triggered escalation"
    - "Supervisor approved after review"

    This field is critical for explainability.
    */
    reason TEXT NOT NULL,

    /*
    Snapshot of FACTS used to evaluate guards at transition time.

    Stored as JSON text.

    Why this matters:
    -----------------
    - Enables post-mortem analysis
    - Prevents "but the data changed later" excuses
    - Allows replay-free auditing

    Example:
    --------
    {
        "risk_rules_passed": true,
        "amount_within_threshold": true
    }
    */
    metadata TEXT,

    -- Exact timestamp when the transition was committed.
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


/*
===============================================================================
INDEXES (Performance + Forensics)
===============================================================================

These indexes are NOT premature optimization.
They reflect real query patterns:
- case history reconstruction
- analytics
- audits
*/

-- Fast retrieval of a case's full transition history
CREATE INDEX IF NOT EXISTS idx_audit_logs_case_id
ON audit_logs (case_id);

-- Fast ordering of transitions over time
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
ON audit_logs (created_at);
