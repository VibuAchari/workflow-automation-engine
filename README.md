# 🚦 Workflow Automation Engine — Phase 1

*A deterministic, audit-first workflow automation core inspired by enterprise BPM / case management systems (Pega-style engines), implemented in Python.*

This repository currently contains **Phase 1** of the system:  
a **test-proven workflow integrity engine** that enforces state machines, guarded transitions, and atomic persistence with full auditability.

---

## 🧠 Why This Project Exists

In real enterprise systems, workflows are **not CRUD records** — they are **long-lived cases** that:

- Move through **well-defined states**
- Must obey **strict transition rules**
- Are governed by **policies that evolve over time**
- Require **complete audit trails** for compliance, debugging, and forensic reconstruction

This project exists to build that **workflow backbone correctly first**, before adding complexity.

**Phase 1 prioritizes correctness over features.**

---

## 🎯 Phase 1 Scope — What *Is* Implemented

### ✅ Core Capabilities

#### 🔒 Explicit State Machine
- Finite, well-defined case states
- Illegal transitions are **impossible by construction**

#### 🧭 Single Transition Authority
- All state changes flow through **one transition engine**
- No direct state mutation anywhere else in the system

#### 🛡️ Guarded Transitions
- Transitions execute **only if guards pass**
- Guards depend solely on **pre-computed facts**
- No business logic hidden inside transitions

#### 🧱 Atomic Persistence
- State update **and** audit log insertion occur in a **single transaction**
- Partial or half-applied transitions cannot exist

#### 📜 Audit-First Design
- Every successful transition is **permanently recorded**
- Full reconstruction of case history is always possible

#### 🧪 Test-Proven Invariants
- Illegal transitions are rejected
- Guard failures roll back cleanly
- Audit logs are mandatory
- Atomicity verified through failure simulation

---

## 🚫 What Phase 1 Explicitly Does *Not* Include

To keep the core minimal, understandable, and correct, Phase 1 **deliberately excludes**:

- Rule evaluation engines
- SLA computation or scheduling
- Background workers
- HTTP / API layers
- UI or dashboards
- Domain-specific business logic

These will be layered **on top of Phase 1**, never inside it — without weakening its guarantees.

---

## 🗂️ Project Structure (Current)

```text
workflow-automation-engine/
│
├── core/                         # Workflow integrity core
│   ├── state.py                  # State definitions
│   ├── state_machine.py          # Allowed transitions
│   ├── guards.py                 # Guard evaluation (facts only)
│   ├── transition_guards.py      # Guard-to-transition mapping
│   └── transition_engine.py      # Single transition authority
│
├── db/
│   ├── schema.sql                # Audit-first persistence schema
│   └── database.py               # Transaction management
│
├── tests/
│   ├── conftest.py
│   ├── helpers.py
│   └── test_transitions.py       # Invariant-focused test suite
│
├── docs/
│   └── architecture.md           # Frozen Phase 1 architecture contract
│
├── requirements.txt
└── README.md

```

---

## ▶️ Running the Tests

Phase 1 is entirely test-driven.

### 📦 Requirements 
-Python 3.10+
-pytest

### 🔧 Install Dependencies
```bash
pip install -r requirements.txt
```

###🧪 Run Tests (from project root)
```bash
pytest -v
```
✅ All tests must pass before progressing to the next phase. 

### 🧱 Architectural Principles (Phase 1)
These principles are non-negotiable:
- State integrity over features
- Auditability by construction
- Determinism over convenience
- Separation of enforcement from decision-making
- Tests as proof, not afterthoughts

If future code violates these principles, the code is wrong.

---

## 🛣️ Roadmap (High-Level)
- Phase 2: Rule Engine (decision logic produces facts)
- Phase 3: SLA & Time-Based Evaluation
- Phase 4: Actions & Side Effects
- Phase 5: API Layer & Dashboards
  
Each phase builds on top of Phase 1 — never inside it.

----

## 📌 Status

### ✅ Phase 1 complete
- 🧪 All core invariants covered by tests
- 🔒 Architecture frozen and documented
  
---

## ℹ️ Final Note
This repository represents a workflow integrity engine,
not a full application.

It is designed to be the bedrock upon which complex, enterprise-grade workflow systems can be safely built.
