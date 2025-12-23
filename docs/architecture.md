# Workflow Automation Engine — Architecture (Phase 1)

## Purpose of This Document

This document defines the **architectural foundations** of the Workflow Automation Engine
as implemented in Phase 1.

It exists to:
- Lock system invariants
- Explain *why* the design is structured this way
- Prevent future changes from violating core guarantees
- Serve as the reference point for all future phases

If an implementation decision contradicts this document,
**the implementation is wrong**, not the document.

---

## Phase 1 Scope (Explicit)

### What Phase 1 DOES

Phase 1 implements the **core workflow integrity layer**:

- A deterministic state machine
- Guarded state transitions
- Atomic persistence
- Mandatory audit logging
- Test-proven invariants

### What Phase 1 DOES NOT Do

Phase 1 deliberately excludes:
- Rule evaluation logic
- SLA computation or scheduling
- Background workers
- APIs or HTTP concerns
- UI, dashboards, or visualization
- Business-domain-specific behavior

These will be layered on later phases
*without weakening Phase 1 guarantees*.

---

## Core Architectural Principle

> **State integrity is more important than features.**

The system is designed such that:
- No feature can bypass the state machine
- No state change can occur without audit evidence
- No partial transitions are possible

This principle drives every design choice in Phase 1.

---

## State Machine

### States

The system defines a finite, explicit set of states:

- CREATED
- UNDER_REVIEW
- WAITING_INFO
- ESCALATED
- APPROVED
- REJECTED
- CLOSED (terminal)

States represent **system truth**, not UI labels.

Illegal states are unrepresentable by design.

---

### Allowed Transitions

Transitions are explicitly defined and centralized.

Examples:
- CREATED → UNDER_REVIEW
- UNDER_REVIEW → APPROVED | REJECTED | ESCALATED | WAITING_INFO
- APPROVED → CLOSED
- REJECTED → CLOSED

If a transition is not explicitly listed,
**it does not exist**.

The database does not enforce this.
The transition engine does.

---

## Transition Engine (Single Authority)

All state changes occur through **one function**:

