"""
state.py

Purpose:
--------
Defines all possible states a Case can be in.

Design rules:
-------------
1. States are finite and explicit.
2. States represent *system truth*, not UI labels.
3. This file must NEVER contain logic.
4. Any change here is a breaking change to the workflow engine.

If you feel tempted to add logic here, stop.
"""

from enum import Enum


class CaseState(str, Enum):
    """
    Enumeration of all valid case states.

    Why Enum?
    ---------
    - Prevents typos ("APPROVE" vs "APPROVED")
    - Makes illegal states unrepresentable
    - Enables static reasoning about transitions
    """

    CREATED = "CREATED"
    UNDER_REVIEW = "UNDER_REVIEW"
    WAITING_INFO = "WAITING_INFO"
    ESCALATED = "ESCALATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"
