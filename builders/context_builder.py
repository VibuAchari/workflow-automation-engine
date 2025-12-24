
# =============================================================================
# File: builders/context_builder.py
# Purpose: Explicit context construction from case data
# =============================================================================

"""
Context Builder

Purpose:
--------
Transforms case data into rule evaluation context.

This module:
- Extracts relevant fields from Case
- Computes derived values (dates, counts, flags)
- Returns flat dictionary for Rule Engine

It does NOT:
- Evaluate conditions
- Make decisions
- Know about rules or facts
- Touch databases

Invariants:
-----------
1. Deterministic (same input → same output)
2. Pure function (no side effects)
3. Testable in isolation
4. All derivations explicit and documented
"""

from typing import Dict, Any
from datetime import datetime
from repositories.protocols import Case


class ContextBuilder:
    """
    Builds rule evaluation context from case data.
    
    This is a TRANSFORMATION layer, not a decision layer.
    """
    
    @staticmethod
    def build(case: Case) -> Dict[str, Any]:
        """
        Build context dictionary from case data.
        
        Parameters:
        -----------
        case : Case
            Source case data
            
        Returns:
        --------
        dict
            Flat dictionary of fields for rule evaluation
            
        Notes:
        ------
        - Extracts all case.data fields
        - Adds computed/derived fields explicitly
        - All computations must be deterministic
        - No business logic (just data shaping)
        
        Example:
        --------
        Input case.data:
            {"amount": 50000, "created_at": "2024-01-01"}
            
        Output context:
            {
                "amount": 50000,
                "created_at": "2024-01-01",
                "days_open": 23,  # Computed
                "current_state": "pending_review"  # From case
            }
        """
        
        # Start with raw case data (shallow copy to avoid mutation)
        context = dict(case.data)
        
        # Add case metadata
        context["case_id"] = case.case_id
        context["current_state"] = case.current_state
        context["case_type"] = case.case_type
        
        # Compute derived fields (example: days_open)
        # NOTE: Only add this if created_at exists in case.data
        if "created_at" in case.data:
            context["days_open"] = ContextBuilder._compute_days_open(
                case.data["created_at"]
            )
        
        return context
    
    @staticmethod
    def _compute_days_open(created_at: str) -> int:
        """
        Compute days between creation and now.
        
        This is an example of explicit derivation.
        All such computations should be:
        - Documented
        - Testable
        - Deterministic (given same input)
        
        Parameters:
        -----------
        created_at : str
            ISO format date string
            
        Returns:
        --------
        int
            Number of days case has been open
        """
        created = datetime.fromisoformat(created_at)
        now = datetime.now()
        delta = now - created
        return delta.days


