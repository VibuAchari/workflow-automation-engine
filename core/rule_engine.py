"""
rule_engine.py

Purpose:
--------
Pure recursive evaluator for JSON condition trees.

This module:
- Evaluates condition ASTs
- Produces boolean results
- Raises explicit domain exceptions
- Has ZERO side effects

It does NOT:
- Know about rules
- Know about priorities
- Produce facts
- Touch databases

Invariants:
-----------
1. Purely recursive AST traversal
2. Operator-registry driven comparisons
3. Explicit raising of domain exceptions (no generic errors)
4. Context is treated as read-only
5. Nodes are EITHER logical OR comparison - never mixed
6. No extraneous keys allowed in any node
7. Every rule that is considered MUST appear in the trace
8. Rule definition validity is checked BEFORE evaluation
"""

from typing import Any, Dict, List, Callable


# =============================================================================
# Domain Exceptions
# =============================================================================

class RuleEngineError(Exception):
    """Base exception for all rule engine failures."""
    pass


class InvalidRuleDefinition(RuleEngineError):
    """
    Raised when a rule or condition tree is malformed
    or uses unsupported operators.
    
    Status: FAILED_INVALID_DEFINITION
    """
    pass


class MissingContextField(RuleEngineError):
    """
    Raised when a condition references a field
    not present in the provided context.
    
    Status: FAILED_MISSING_CONTEXT
    """
    pass


class RuleEvaluationTypeError(RuleEngineError):
    """
    Raised when a comparison fails due to incompatible types.
    
    Status: FAILED_TYPE_ERROR
    """
    pass


# =============================================================================
# Operator Registry (Whitelist)
# =============================================================================

OPERATORS: Dict[str, Callable[[Any, Any], bool]] = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">":  lambda a, b: a > b,
    "<":  lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}


# =============================================================================
# Core Recursive Evaluator
# =============================================================================

def _evaluate_node(node: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    Recursively evaluates a JSON condition node.

    Parameters:
    -----------
    node : dict
        A condition node (logical or comparison).

    context : dict
        Snapshot of case data. Must be treated as read-only.

    Returns:
    --------
    bool
        Result of condition evaluation.

    Raises:
    -------
    InvalidRuleDefinition
        If the node structure or operator is invalid.

    MissingContextField
        If a required field is not present in context.

    RuleEvaluationTypeError
        If comparison fails due to incompatible types.

    Notes:
    ------
    - Evaluation is depth-first
    - Logical nodes short-circuit by design
    - Missing data is an ERROR, not False
    - Empty 'all' evaluates to True (vacuous truth)
    - Empty 'any' evaluates to False
    - Nodes must be EITHER logical OR comparison - never both
    - No extraneous keys allowed
    """

    # -------------------------------------------------------------------------
    # GUARD: Prevent logical node ambiguity
    # -------------------------------------------------------------------------
    has_all = "all" in node
    has_any = "any" in node
    has_field = "field" in node
    
    # A node cannot be both logical AND comparison
    is_logical = has_all or has_any
    is_comparison = has_field
    
    if is_logical and is_comparison:
        raise InvalidRuleDefinition(
            "Node cannot be both logical (all/any) and comparison (field/operator/value)"
        )
    
    # A node cannot have both 'all' and 'any'
    if has_all and has_any:
        raise InvalidRuleDefinition(
            "Node cannot contain both 'all' and 'any' - choose one"
        )

    # -------------------------------------------------------------------------
    # BRANCH A: Logical AND (all)
    # -------------------------------------------------------------------------
    if has_all:
        # Enforce strict key schema
        if set(node.keys()) != {"all"}:
            raise InvalidRuleDefinition(
                f"Logical 'all' node must contain only the 'all' key. Found: {list(node.keys())}"
            )
        
        children = node["all"]
        
        if not isinstance(children, list):
            raise InvalidRuleDefinition(
                "'all' node must contain a list of conditions"
            )
        
        # Mathematical invariant: all([]) is True (vacuous truth)
        # Python's all() handles short-circuiting natively
        return all(_evaluate_node(child, context) for child in children)

    # -------------------------------------------------------------------------
    # BRANCH B: Logical OR (any)
    # -------------------------------------------------------------------------
    if has_any:
        # Enforce strict key schema
        if set(node.keys()) != {"any"}:
            raise InvalidRuleDefinition(
                f"Logical 'any' node must contain only the 'any' key. Found: {list(node.keys())}"
            )
        
        children = node["any"]
        
        if not isinstance(children, list):
            raise InvalidRuleDefinition(
                "'any' node must contain a list of conditions"
            )
        
        # Mathematical invariant: any([]) is False
        # Python's any() handles short-circuiting natively
        return any(_evaluate_node(child, context) for child in children)

    # -------------------------------------------------------------------------
    # BRANCH C: Comparison Leaf
    # -------------------------------------------------------------------------
    
    # Enforce strict key schema for leaf nodes
    required_keys = {"field", "operator", "value"}
    actual_keys = set(node.keys())
    
    if actual_keys != required_keys:
        missing = required_keys - actual_keys
        extra = actual_keys - required_keys
        
        error_parts = []
        if missing:
            error_parts.append(f"missing keys: {missing}")
        if extra:
            error_parts.append(f"unexpected keys: {extra}")
        
        raise InvalidRuleDefinition(
            f"Leaf node must contain exactly {{field, operator, value}}. "
            f"Found {list(actual_keys)}. Issues: {', '.join(error_parts)}"
        )
    
    # Extract values (we know they exist due to schema check above)
    field = node["field"]
    operator = node["operator"]
    expected_value = node["value"]
    
    # Guard 1: Operator Whitelist
    if operator not in OPERATORS:
        raise InvalidRuleDefinition(
            f"Unsupported operator: '{operator}'. "
            f"Allowed operators: {list(OPERATORS.keys())}"
        )
    
    # Guard 2: Context Integrity
    if field not in context:
        raise MissingContextField(
            f"Field '{field}' not found in provided context. "
            f"Available fields: {list(context.keys())}"
        )
    
    actual_value = context[field]
    
    # Guard 3: Type/Execution Integrity
    # ONLY catch TypeError - let everything else bubble (those are real bugs)
    try:
        return OPERATORS[operator](actual_value, expected_value)
    except TypeError as e:
        raise RuleEvaluationTypeError(
            f"Type mismatch: cannot compare {type(actual_value).__name__} "
            f"(actual) with {type(expected_value).__name__} (expected) "
            f"using operator '{operator}'. Original error: {str(e)}"
        )


# =============================================================================
# Public Rule Engine API
# =============================================================================

def evaluate_rules(*, context: Dict[str, Any], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Public entry point for the Rule Engine.

    Purpose:
    --------
    Evaluates a list of rules against a context snapshot and produces:
    - a final set of facts
    - a complete, ordered evaluation trace

    This function:
    ----------------
    - Sorts rules deterministically by priority
    - Respects rule enable/disable flags
    - Validates rule structure BEFORE evaluation
    - Evaluates conditions via _evaluate_node
    - Catches domain exceptions and converts them into trace entries
    - NEVER mutates context
    - NEVER raises rule-level exceptions outward

    Returns:
    --------
    {
        "facts": dict,
        "trace": list[dict]
    }

    Engine-level failures (invalid rules list structure) may still raise.
    
    Trace Status Values:
    --------------------
    - SKIPPED_DISABLED: Rule was disabled
    - EVALUATED_TRUE: Condition evaluated to True, fact produced
    - EVALUATED_FALSE: Condition evaluated to False
    - FAILED_INVALID_DEFINITION: Rule structure or condition tree malformed
    - FAILED_MISSING_CONTEXT: Required field not in context
    - FAILED_TYPE_ERROR: Type mismatch during comparison
    - FAILED_ENGINE_ERROR: Unexpected engine failure (should never happen)
    """

    # -------------------------------------------------------------------------
    # Pre-flight validation (engine-level, not rule-level)
    # -------------------------------------------------------------------------
    if not isinstance(rules, list):
        raise InvalidRuleDefinition(
            "Rules must be provided as a list of rule definitions"
        )

    # -------------------------------------------------------------------------
    # Deterministic ordering
    # -------------------------------------------------------------------------
    # Priority semantics:
    # - Lower priority evaluated first
    # - Higher priority evaluated later
    # - Later rules may overwrite facts (last-write-wins)
    sorted_rules = sorted(
        rules,
        key=lambda r: r.get("priority", 0)
    )

    final_facts: Dict[str, Any] = {}
    trace: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Rule evaluation loop
    # -------------------------------------------------------------------------
    for rule in sorted_rules:
        # Extract rule metadata safely
        rule_id = rule.get("rule_id", "<unknown>")
        priority = rule.get("priority", 0)
        enabled = rule.get("enabled", True)

        # Base trace entry (filled progressively)
        trace_entry = {
            "rule_id": rule_id,
            "priority": priority,
            "evaluated": False,
            "evaluation_status": None,
            "condition_result": None,
            "produced_fact": None,
            "error": None,
        }

        # ---------------------------------------------------------------------
        # GUARD: Validate required structural keys
        # ---------------------------------------------------------------------
        if "condition" not in rule:
            trace_entry.update({
                "evaluated": False,
                "evaluation_status": "FAILED_INVALID_DEFINITION",
                "error": {
                    "type": "InvalidRuleDefinition",
                    "message": "Rule missing required 'condition' key"
                }
            })
            trace.append(trace_entry)
            continue

        # ---------------------------------------------------------------------
        # Skip disabled rules
        # ---------------------------------------------------------------------
        if not enabled:
            trace_entry.update({
                "evaluated": False,
                "evaluation_status": "SKIPPED_DISABLED",
            })
            trace.append(trace_entry)
            continue

        # ---------------------------------------------------------------------
        # GUARD: Validate output_fact structure BEFORE evaluation
        # ---------------------------------------------------------------------
        # Definition errors are static, not runtime
        # Check this before wasting cycles on condition evaluation
        output_fact = rule.get("output_fact")
        if not isinstance(output_fact, dict) or len(output_fact) != 1:
            trace_entry.update({
                "evaluated": False,
                "evaluation_status": "FAILED_INVALID_DEFINITION",
                "error": {
                    "type": "InvalidRuleDefinition",
                    "message": (
                        f"Rule '{rule_id}' must define output_fact "
                        f"as a dict with exactly one key"
                    )
                }
            })
            trace.append(trace_entry)
            continue

        # ---------------------------------------------------------------------
        # Evaluate rule condition
        # ---------------------------------------------------------------------
        try:
            result = _evaluate_node(rule["condition"], context)

            trace_entry["evaluated"] = True
            trace_entry["condition_result"] = result

            if result:
                trace_entry["evaluation_status"] = "EVALUATED_TRUE"
                
                # Apply fact (last-write-wins)
                final_facts.update(output_fact)
                trace_entry["produced_fact"] = output_fact
            else:
                trace_entry["evaluation_status"] = "EVALUATED_FALSE"

        # ---------------------------------------------------------------------
        # Domain exception handling → trace mapping
        # ---------------------------------------------------------------------
        except InvalidRuleDefinition as e:
            trace_entry.update({
                "evaluated": True,
                "evaluation_status": "FAILED_INVALID_DEFINITION",
                "error": {
                    "type": "InvalidRuleDefinition",
                    "message": str(e),
                },
            })

        except MissingContextField as e:
            trace_entry.update({
                "evaluated": True,
                "evaluation_status": "FAILED_MISSING_CONTEXT",
                "error": {
                    "type": "MissingContextField",
                    "message": str(e),
                },
            })

        except RuleEvaluationTypeError as e:
            trace_entry.update({
                "evaluated": True,
                "evaluation_status": "FAILED_TYPE_ERROR",
                "error": {
                    "type": "RuleEvaluationTypeError",
                    "message": str(e),
                },
            })

        # ---------------------------------------------------------------------
        # Safety net: Catch unexpected engine failures
        # ---------------------------------------------------------------------
        # This should NEVER happen if the engine is correct
        # But if it does, we fail safely and preserve traceability
        except Exception as e:
            trace_entry.update({
                "evaluated": True,
                "evaluation_status": "FAILED_ENGINE_ERROR",
                "error": {
                    "type": type(e).__name__,
                    "message": f"UNEXPECTED ENGINE ERROR (this is a bug): {str(e)}"
                },
            })

        # ---------------------------------------------------------------------
        # Append trace entry (always)
        # ---------------------------------------------------------------------
        trace.append(trace_entry)

    # -------------------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------------------
    return {
        "facts": final_facts,
        "trace": trace,
    }
