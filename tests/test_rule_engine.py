# tests/test_rule_engine.py

import pytest

from core.rule_engine import (
    evaluate_rules,
    InvalidRuleDefinition,
    MissingContextField,
    RuleEvaluationTypeError,
)


def test_simple_rule_evaluates_true_and_produces_fact():
    """Happy Path: Simple rule fires and produces fact"""
    context = {"amount": 15000}

    rules = [
        {
            "rule_id": "R-1",
            "priority": 1,
            "enabled": True,
            "condition": {
                "field": "amount",
                "operator": ">",
                "value": 10000,
            },
            "output_fact": {"high_amount": True},
        }
    ]

    result = evaluate_rules(context=context, rules=rules)

    assert result["facts"] == {"high_amount": True}
    assert len(result["trace"]) == 1

    trace = result["trace"][0]
    assert trace["evaluation_status"] == "EVALUATED_TRUE"
    assert trace["produced_fact"] == {"high_amount": True}


def test_rule_evaluates_false_produces_no_fact():
    """Condition evaluates False (no fact)"""
    context = {"amount": 500}

    rules = [
        {
            "rule_id": "R-2",
            "priority": 1,
            "enabled": True,
            "condition": {
                "field": "amount",
                "operator": ">",
                "value": 1000,
            },
            "output_fact": {"high_amount": True},
        }
    ]

    result = evaluate_rules(context=context, rules=rules)

    assert result["facts"] == {}

    trace = result["trace"][0]
    assert trace["evaluation_status"] == "EVALUATED_FALSE"
    assert trace["produced_fact"] is None


def test_missing_context_field_is_traceable_failure():
    """Missing context field → hard failure (but engine survives)"""
    context = {"amount": 1000}

    rules = [
        {
            "rule_id": "R-3",
            "priority": 1,
            "enabled": True,
            "condition": {
                "field": "credit_score",
                "operator": ">",
                "value": 700,
            },
            "output_fact": {"good_credit": True},
        }
    ]

    result = evaluate_rules(context=context, rules=rules)

    trace = result["trace"][0]
    assert trace["evaluation_status"] == "FAILED_MISSING_CONTEXT"
    assert trace["error"]["type"] == "MissingContextField"
    assert result["facts"] == {}


def test_invalid_operator_fails_definition():
    """Invalid operator → definition failure"""
    context = {"amount": 1000}

    rules = [
        {
            "rule_id": "R-4",
            "priority": 1,
            "enabled": True,
            "condition": {
                "field": "amount",
                "operator": ">>",
                "value": 500,
            },
            "output_fact": {"flag": True},
        }
    ]

    result = evaluate_rules(context=context, rules=rules)

    trace = result["trace"][0]
    assert trace["evaluation_status"] == "FAILED_INVALID_DEFINITION"
    assert "Unsupported operator" in trace["error"]["message"]


def test_invalid_output_fact_is_caught_before_evaluation():
    """output_fact malformed → rejected BEFORE evaluation"""
    context = {"amount": 5000}

    rules = [
        {
            "rule_id": "R-5",
            "priority": 1,
            "enabled": True,
            "condition": {
                "field": "amount",
                "operator": ">",
                "value": 1000,
            },
            # INVALID: multiple keys
            "output_fact": {"a": 1, "b": 2},
        }
    ]

    result = evaluate_rules(context=context, rules=rules)

    trace = result["trace"][0]
    assert trace["evaluation_status"] == "FAILED_INVALID_DEFINITION"
    assert trace["condition_result"] is None


def test_disabled_rule_is_skipped_but_traced():
    """Disabled rule is skipped (but traced)"""
    context = {"amount": 10000}

    rules = [
        {
            "rule_id": "R-6",
            "priority": 1,
            "enabled": False,
            "condition": {
                "field": "amount",
                "operator": ">",
                "value": 1,
            },
            "output_fact": {"flag": True},
        }
    ]

    result = evaluate_rules(context=context, rules=rules)

    trace = result["trace"][0]
    assert trace["evaluation_status"] == "SKIPPED_DISABLED"
    assert result["facts"] == {}


def test_higher_priority_rule_overwrites_fact():
    """Priority override (last-write-wins)"""
    context = {"amount": 2000}

    rules = [
        {
            "rule_id": "R-low",
            "priority": 1,
            "enabled": True,
            "condition": {
                "field": "amount",
                "operator": ">",
                "value": 100,
            },
            "output_fact": {"risk": "LOW"},
        },
        {
            "rule_id": "R-high",
            "priority": 10,
            "enabled": True,
            "condition": {
                "field": "amount",
                "operator": ">",
                "value": 1000,
            },
            "output_fact": {"risk": "HIGH"},
        },
    ]

    result = evaluate_rules(context=context, rules=rules)

    assert result["facts"]["risk"] == "HIGH"


def test_engine_error_is_captured_safely(monkeypatch):
    """Engine safety net (FAILED_ENGINE_ERROR)"""
    context = {"amount": 100}

    rules = [
        {
            "rule_id": "R-7",
            "priority": 1,
            "enabled": True,
            "condition": {
                "field": "amount",
                "operator": "==",
                "value": 100,
            },
            "output_fact": {"ok": True},
        }
    ]

    # Force an unexpected engine bug
    from core import rule_engine
    monkeypatch.setattr(rule_engine, "_evaluate_node", lambda *_: 1 / 0)

    result = evaluate_rules(context=context, rules=rules)

    trace = result["trace"][0]
    assert trace["evaluation_status"] == "FAILED_ENGINE_ERROR"
    assert "UNEXPECTED ENGINE ERROR" in trace["error"]["message"]