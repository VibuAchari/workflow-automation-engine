"""
Workflow Orchestrator Tests

Purpose:
--------
Verify orchestration logic in isolation.

These tests ensure that:
- Data flows correctly between components
- Facts are passed unchanged
- Context building is delegated
- Rule loading is based on case_type
- No business logic exists in the orchestrator

Constraints:
------------
- Mocks ONLY
- No database
- No HTTP
- No real rule evaluation
- No real state transitions
"""

from unittest.mock import Mock, patch

import pytest

from core.workflow_orchestrator import run_workflow_step
from repositories.protocols import Case

'''
Facts must pass through UNCHANGED (critical invariant)
#This is the most important test.
'''
def test_orchestrator_passes_facts_unchanged():
    """
    Facts produced by the Rule Engine must be passed to the
    Transition Engine without modification, filtering, or enrichment.
    """

    mock_case_repo = Mock()
    mock_rules_repo = Mock()

    case = Case(
        case_id="C-123",
        current_state="pending_review",
        case_type="loan_application",
        data={"amount": 50000, "credit_score": 750},
    )
    mock_case_repo.get_case.return_value = case

    mock_rules_repo.get_active_rules.return_value = [
        {
            "rule_id": "R-1",
            "priority": 1,
            "enabled": True,
            "condition": {"field": "amount", "operator": ">", "value": 10000},
            "output_fact": {"high_value": True},
        }
    ]

    with patch("core.workflow_orchestrator.evaluate_rules") as mock_rule_engine, \
         patch("core.workflow_orchestrator.execute_transition") as mock_transition:

        mock_rule_engine.return_value = {
            "facts": {"high_value": True, "approved": True},
            "trace": [{"rule_id": "R-1", "status": "EVALUATED_TRUE"}],
        }

        mock_transition.return_value = {
            "new_state": "approved",
            "status": "SUCCESS",
            "audit_entry": {"action": "approve"},
        }

        result = run_workflow_step(
            case_id="C-123",
            target_state="approved",
            case_repository=mock_case_repo,
            rules_repository=mock_rules_repo,
        )

        # ---- Assertions ----

        # Transition engine called exactly once
        mock_transition.assert_called_once()

        # Facts passed UNCHANGED
        passed_facts = mock_transition.call_args.kwargs["facts"]
        assert passed_facts == {"high_value": True, "approved": True}

        # No extra keys introduced
        assert set(passed_facts.keys()) == {"high_value", "approved"}

        # Output preserved
        assert result["facts"] == passed_facts
        assert result["to_state"] == "approved"


#ContextBuilder must be invoked (delegation test)
#This ensures the orchestrator does not construct context itself.

def test_orchestrator_delegates_context_building():
    """
    Orchestrator must delegate context construction
    to ContextBuilder and not inline logic.
    """

    mock_case_repo = Mock()
    mock_rules_repo = Mock()

    case = Case(
        case_id="C-456",
        current_state="draft",
        case_type="claim_review",
        data={"claim_amount": 5000},
    )
    mock_case_repo.get_case.return_value = case
    mock_rules_repo.get_active_rules.return_value = []

    with patch("core.workflow_orchestrator.ContextBuilder.build") as mock_builder, \
         patch("core.workflow_orchestrator.evaluate_rules") as mock_rule_engine, \
         patch("core.workflow_orchestrator.execute_transition") as mock_transition:

        mock_builder.return_value = {
            "claim_amount": 5000,
            "case_id": "C-456",
            "current_state": "draft",
            "case_type": "claim_review",
        }

        mock_rule_engine.return_value = {"facts": {}, "trace": []}
        mock_transition.return_value = {
            "new_state": "submitted",
            "status": "SUCCESS",
        }

        run_workflow_step(
            case_id="C-456",
            target_state="submitted",
            case_repository=mock_case_repo,
            rules_repository=mock_rules_repo,
        )

        mock_builder.assert_called_once_with(case)


#Rules must be loaded by case_type (no fallback logic)

def test_orchestrator_loads_rules_by_case_type():
    """
    Rules must be fetched strictly by case_type.
    No defaults or fallbacks allowed.
    """

    mock_case_repo = Mock()
    mock_rules_repo = Mock()

    case = Case(
        case_id="C-789",
        current_state="pending",
        case_type="mortgage_application",
        data={},
    )

    mock_case_repo.get_case.return_value = case
    mock_rules_repo.get_active_rules.return_value = []

    with patch("core.workflow_orchestrator.evaluate_rules") as mock_rule_engine, \
         patch("core.workflow_orchestrator.execute_transition") as mock_transition:

        mock_rule_engine.return_value = {"facts": {}, "trace": []}
        mock_transition.return_value = {
            "new_state": "approved",
            "status": "SUCCESS",
        }

        run_workflow_step(
            case_id="C-789",
            target_state="approved",
            case_repository=mock_case_repo,
            rules_repository=mock_rules_repo,
        )

        mock_rules_repo.get_active_rules.assert_called_once_with("mortgage_application")

#Rule trace and audit entry must be preserved
#This enforces full transparency.


def test_orchestrator_preserves_rule_trace_and_audit_entry():
    """
    Orchestrator must return full rule trace and audit entry
    without modification.
    """

    mock_case_repo = Mock()
    mock_rules_repo = Mock()

    case = Case(
        case_id="C-999",
        current_state="review",
        case_type="test",
        data={},
    )

    mock_case_repo.get_case.return_value = case
    mock_rules_repo.get_active_rules.return_value = []

    rule_trace = [
        {"rule_id": "R1", "status": "EVALUATED_TRUE"},
        {"rule_id": "R2", "status": "SKIPPED_DISABLED"},
    ]

    audit_entry = {
        "timestamp": "2024-01-01T10:00:00",
        "actor": "system",
    }

    with patch("core.workflow_orchestrator.evaluate_rules") as mock_rule_engine, \
         patch("core.workflow_orchestrator.execute_transition") as mock_transition:

        mock_rule_engine.return_value = {
            "facts": {"decision": "approve"},
            "trace": rule_trace,
        }

        mock_transition.return_value = {
            "new_state": "approved",
            "status": "SUCCESS",
            "audit_entry": audit_entry,
        }

        result = run_workflow_step(
            case_id="C-999",
            target_state="approved",
            case_repository=mock_case_repo,
            rules_repository=mock_rules_repo,
        )

        assert result["rule_trace"] == rule_trace
        assert result["audit_entry"] == audit_entry
        assert result["facts"]["decision"] == "approve"