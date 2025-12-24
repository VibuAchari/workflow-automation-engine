# =============================================================================
# File: workflow_orchestrator.py
# Purpose: Orchestrates rule evaluation and state transitions
# =============================================================================

"""
Workflow Orchestrator

Purpose:
--------
Coordinates Rule Engine and Transition Engine execution.

This module:
- Fetches case data
- Builds evaluation context
- Invokes Rule Engine → produces facts
- Passes facts to Transition Engine
- Returns complete trace

It does NOT:
- Compute facts
- Make transition decisions
- Filter or transform facts
- Contain business logic
- Interpret rule results

Invariants:
-----------
1. No if/else on rule results
2. No state machine logic
3. No business thresholds
4. Facts passed unchanged
5. All decisions delegated to engines
6. Must remain mechanically boring

Critical Rule:
--------------
If this module starts "deciding" anything, Phase 3 has failed.
"""

from typing import Dict, Any

from core.rule_engine import evaluate_rules
from core.transition_engine import execute_transition
from repositories.protocols import CaseRepository, RulesRepository
from builders.context_builder import ContextBuilder


def run_workflow_step(
    *,
    case_id: str,
    target_state: str,
    case_repository: CaseRepository,
    rules_repository: RulesRepository
) -> Dict[str, Any]:
    """
    Orchestrates rule evaluation and state transition.
    
    This function is MECHANICAL. It performs these steps in order:
    1. Fetch case data (via repository)
    2. Build context (explicit transformation)
    3. Evaluate rules → facts (Phase 2)
    4. Execute transition with facts (Phase 1)
    5. Return complete trace (transparency)
    
    Parameters:
    -----------
    case_id : str
        Unique case identifier
        
    target_state : str
        Desired target state
        
    case_repository : CaseRepository
        Abstraction for case data access
        
    rules_repository : RulesRepository
        Abstraction for rules data access
    
    Returns:
    --------
    dict
        {
            "case_id": str,
            "from_state": str,
            "to_state": str,
            "facts": dict,
            "rule_trace": list,
            "transition_status": str,
            "audit_entry": dict
        }
    
    Raises:
    -------
    CaseNotFoundError
        If case does not exist (from repository)
        
    InvalidTransitionError
        If transition is illegal (from transition engine)
    
    Notes:
    ------
    - Facts are passed to transition engine UNCHANGED
    - No filtering, no transformation, no interpretation
    - Rule failures do not block transition attempts
    - Transition failures propagate (no swallowing)
    - All traces preserved for auditability
    
    Assumptions:
    ------------
    - case.case_type exists (will fail loudly if not)
    - Rules repository returns valid rule format
    - Transition engine accepts facts as context
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Fetch case data
    # -------------------------------------------------------------------------
    # Repository handles existence check and error raising
    case = case_repository.get_case(case_id)
    
    # -------------------------------------------------------------------------
    # Step 2: Build evaluation context
    # -------------------------------------------------------------------------
    # Explicit, testable, deterministic transformation
    context = ContextBuilder.build(case)
    
    # -------------------------------------------------------------------------
    # Step 3: Evaluate rules
    # -------------------------------------------------------------------------
    # Load rules for this case type
    # Assumption: case.case_type exists (documented, will fail if not)
    rules = rules_repository.get_active_rules(case.case_type)
    
    # Invoke Rule Engine (Phase 2 - pure function)
    rule_result = evaluate_rules(
        context=context,
        rules=rules
    )
    
    # Extract facts and trace
    facts = rule_result["facts"]
    rule_trace = rule_result["trace"]
    
    # -------------------------------------------------------------------------
    # Step 4: Execute transition
    # -------------------------------------------------------------------------
    # Pass facts to Transition Engine UNCHANGED
    # No filtering, no merging, no "helping"
    # Guards decide if facts are sufficient
    transition_result = execute_transition(
        case_id=case_id,
        action=target_state,
        facts=facts  # ← Semantic hygiene: facts, not context
    )
    
    # -------------------------------------------------------------------------
    # Step 5: Return complete trace
    # -------------------------------------------------------------------------
    # Transparency: caller sees everything
    return {
        "case_id": case_id,
        "from_state": case.current_state,
        "to_state": transition_result["new_state"],
        "facts": facts,
        "rule_trace": rule_trace,
        "transition_status": transition_result["status"],
        "audit_entry": transition_result.get("audit_entry")
    }


