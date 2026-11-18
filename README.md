# SWE-Bench Task Lab: Reference Environment & Deterministic Verifier

A reference implementation demonstrating how to engineer **Reinforcement Learning (RL) coding environments** and **deterministic test verifiers** for evaluating autonomous software engineering agents.

Inspired by real-world open-source pull requests (similar to `psf/requests` Issue #2949), this repository illustrates the end-to-end task curation, sandboxing, and verification architecture.

---

## 🏗️ Architecture Overview

```
swe-bench-task-lab/
├── task_instance.json             # Task metadata, problem statement & test suites
├── Dockerfile                     # Hermetic, unprivileged sandbox definition
├── solution.patch                 # Golden reference patch authored by human engineers
├── verify.py                      # Anti-cheating & automated grading harness
├── src/
│   └── http_resilience/          # Target codebase with intentional defect at base commit
│       ├── __init__.py
│       ├── client.py              # Defect: Authorization header forwarded across origin redirects
│       └── exceptions.py
└── tests/
    ├── test_client_regression.py  # PASS_TO_PASS: Baseline regression test suite
    └── test_redirect_auth_leak.py # FAIL_TO_PASS: Defect reproduction test suite
```

---

## ⚡ Quickstart: Verifying the Lifecycle

### 1. Test the Unpatched Base State (Must Fail)
In the initial unpatched state, the regression suite passes, but the defect test fails:
```bash
python -m pytest tests/test_client_regression.py  # Passes (PASS_TO_PASS)
python -m pytest tests/test_redirect_auth_leak.py   # Fails (FAIL_TO_PASS)
```

Running the verification harness confirms the task is `UNRESOLVED`:
```bash
python verify.py
# Output: [VERDICT: UNRESOLVED] Candidate patch failed to fix target defect.
```

### 2. Apply the Golden Reference Patch
Apply the human-verified solution:
```bash
git apply solution.patch
```

### 3. Run the Verifier Harness (Must Pass)
```bash
python verify.py
# Output: [VERDICT: RESOLVED] All target defects fixed with zero regressions.
```

---

## 🛡️ Anti-Cheating Invariants
The verifier enforces:
1. **File Immutability:** Any modifications to `tests/`, `verify.py`, or `Dockerfile` immediately trigger an exit code `2` with `Anti-cheating violation`.
2. **Determinism:** Tests run without network access and use deterministic mocks to guarantee reproducible results across every trial.
