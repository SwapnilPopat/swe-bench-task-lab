#!/usr/bin/env python3
"""
verify.py - Automated Deterministic Verifier Harness for Coding Benchmarks.
Validates candidate patches against anti-cheating rules, FAIL_TO_PASS, and PASS_TO_PASS suites.
"""

import sys
import os
import json
import subprocess
from pathlib import Path

TASK_INSTANCE_PATH = Path(__file__).parent / "task_instance.json"

def run_command(cmd, cwd=None):
    env = dict(os.environ)
    src_path = str(Path(__file__).parent / "src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = src_path

    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, env=env)
    return res.returncode, res.stdout, res.stderr

def check_anti_cheating_rules():
    """Ensure candidate has not modified test files, verifiers, or configuration."""
    code, out, _ = run_command("git status --porcelain")
    if code != 0:
        return False, "Failed to inspect git working tree status."

    forbidden_prefixes = ("tests/", "task_instance.json", "verify.py", "Dockerfile", "solution.patch")
    modified_files = [line.strip().split()[-1] for line in out.splitlines() if line.strip()]

    for f in modified_files:
        for prefix in forbidden_prefixes:
            if f == prefix or f.startswith(prefix):
                return False, f"Anti-cheating violation: prohibited modification to '{f}'"

    return True, "Integrity check passed."

def run_test_case(test_identifier):
    """Executes a specific test node identifier deterministically using unittest."""
    cmd = f'"{sys.executable}" -m unittest -v {test_identifier}'
    code, stdout, stderr = run_command(cmd)
    return code == 0, stdout + "\n" + stderr

def main():
    print("=" * 60)
    print("  RUNNING DETERMINISTIC VERIFIER HARNESS")
    print("=" * 60)

    with open(TASK_INSTANCE_PATH, "r", encoding="utf-8") as f:
        task_data = json.load(f)

    instance_id = task_data.get("instance_id")
    fail_to_pass = task_data.get("FAIL_TO_PASS", [])
    pass_to_pass = task_data.get("PASS_TO_PASS", [])

    report = {
        "instance_id": instance_id,
        "anti_cheating_status": "PENDING",
        "fail_to_pass_results": {},
        "pass_to_pass_results": {},
        "resolved": False,
        "failure_reason": None
    }

    # Step 1: Anti-cheating verification
    ok, msg = check_anti_cheating_rules()
    if not ok:
        report["anti_cheating_status"] = "FAILED"
        report["failure_reason"] = msg
        print(f"[ERROR] {msg}")
        with open("eval_result.json", "w") as out_f:
            json.dump(report, out_f, indent=2)
        sys.exit(2)
    report["anti_cheating_status"] = "PASSED"
    print("[PASS] File modification integrity check passed.")

    # Step 2: Run FAIL_TO_PASS suite (must all pass on resolved patch)
    all_f2p_passed = True
    print("\n--- Evaluating FAIL_TO_PASS (Defect Resolution Tests) ---")
    for test_node in fail_to_pass:
        passed, log = run_test_case(test_node)
        report["fail_to_pass_results"][test_node] = "PASSED" if passed else "FAILED"
        if passed:
            print(f"  [PASS] {test_node}")
        else:
            print(f"  [FAIL] {test_node}")
            all_f2p_passed = False

    # Step 3: Run PASS_TO_PASS suite (regression tests)
    all_p2p_passed = True
    print("\n--- Evaluating PASS_TO_PASS (Regression Tests) ---")
    for test_node in pass_to_pass:
        passed, log = run_test_case(test_node)
        report["pass_to_pass_results"][test_node] = "PASSED" if passed else "FAILED"
        if passed:
            print(f"  [PASS] {test_node}")
        else:
            print(f"  [FAIL] {test_node}")
            all_p2p_passed = False

    # Final verdict
    if all_f2p_passed and all_p2p_passed:
        report["resolved"] = True
        print("\n[VERDICT: RESOLVED] All target defects fixed with zero regressions.")
        exit_code = 0
    elif not all_f2p_passed:
        report["failure_reason"] = "One or more FAIL_TO_PASS tests did not pass."
        print("\n[VERDICT: UNRESOLVED] Candidate patch failed to fix target defect.")
        exit_code = 1
    else:
        report["failure_reason"] = "FAIL_TO_PASS passed but PASS_TO_PASS regressions were introduced."
        print("\n[VERDICT: REGRESSION] Candidate patch broke existing features.")
        exit_code = 1

    with open("eval_result.json", "w") as out_f:
        json.dump(report, out_f, indent=2)

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
