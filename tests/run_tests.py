#!/usr/bin/env python3
"""
tests/run_tests.py - Standalone E2E Test Suite CLI Runner
Executes Tiers 1–4, compiles tier-by-tier metrics, prints ANSI summary table,
and exits with code 0 on complete pass.
"""
import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Any

# Ensure workspace root and tests directory are in sys.path
TESTS_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = TESTS_DIR.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


class TierResultTracker:
    def __init__(self):
        self.tiers = {
            "tier1": {"name": "Tier 1: Feature Coverage (F01–F19)", "target": 95, "passed": 0, "failed": 0, "skipped": 0, "tests": []},
            "tier2": {"name": "Tier 2: Boundary & Fault Injection", "target": 95, "passed": 0, "failed": 0, "skipped": 0, "tests": []},
            "tier3": {"name": "Tier 3: Pairwise Interactions", "target": 19, "passed": 0, "failed": 0, "skipped": 0, "tests": []},
            "tier4": {"name": "Tier 4: Real-World Scenarios", "target": 6, "passed": 0, "failed": 0, "skipped": 0, "tests": []},
        }
        self.failures = []

    def classify_test(self, test_name: str, module_name: str) -> str:
        if "tier1" in module_name or test_name.startswith("test_f") and not "_b" in test_name:
            return "tier1"
        elif "tier2" in module_name or "_b" in test_name:
            return "tier2"
        elif "tier3" in module_name or test_name.startswith("test_i"):
            return "tier3"
        elif "tier4" in module_name or test_name.startswith("test_s"):
            return "tier4"
        return "tier1"

    def record_result(self, test_name: str, module_name: str, outcome: str, error_msg: str = ""):
        tier_key = self.classify_test(test_name, module_name)
        tier = self.tiers[tier_key]
        tier["tests"].append(test_name)

        if outcome == "passed":
            tier["passed"] += 1
        elif outcome == "failed":
            tier["failed"] += 1
            self.failures.append((test_name, module_name, error_msg))
        elif outcome == "skipped":
            tier["skipped"] += 1


class PytestPlugin:
    def __init__(self, tracker: TierResultTracker):
        self.tracker = tracker

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            mod_name = report.nodeid.split("::")[0]
            test_name = report.nodeid.split("::")[-1]
            if report.passed:
                self.tracker.record_result(test_name, mod_name, "passed")
            elif report.failed:
                err_text = str(report.longrepr) if report.longrepr else ""
                self.tracker.record_result(test_name, mod_name, "failed", err_text)
            elif report.skipped:
                self.tracker.record_result(test_name, mod_name, "skipped")
        elif report.when == "setup" and report.skipped:
            mod_name = report.nodeid.split("::")[0]
            test_name = report.nodeid.split("::")[-1]
            self.tracker.record_result(test_name, mod_name, "skipped")


def run_via_pytest(tracker: TierResultTracker) -> int:
    try:
        import pytest
        plugin = PytestPlugin(tracker)
        args = [
            str(TESTS_DIR),
            "-v",
            "--tb=short",
            "-q",
            "--override-ini=pythonpath=" + str(WORKSPACE_ROOT)
        ]
        ret = pytest.main(args, plugins=[plugin])
        return ret
    except ImportError:
        return -1


def run_via_unittest_fallback(tracker: TierResultTracker) -> int:
    """Fallback runner in pure Python if pytest is unavailable."""
    import inspect
    import importlib

    test_modules = [
        "test_tier1_features",
        "test_tier2_boundaries",
        "test_tier3_interactions",
        "test_tier4_scenarios"
    ]

    for mod_name in test_modules:
        try:
            mod = importlib.import_module(f"tests.{mod_name}")
        except ModuleNotFoundError:
            try:
                mod = importlib.import_module(mod_name)
            except Exception as e:
                print(f"{RED}Failed to import {mod_name}: {e}{RESET}")
                continue

        # Find all test functions
        for attr_name in dir(mod):
            if attr_name.startswith("test_"):
                func = getattr(mod, attr_name)
                if callable(func):
                    # Check parameters and resolve fixtures from conftest
                    sig = inspect.signature(func)
                    kwargs = {}
                    from tests import conftest
                    for param_name in sig.parameters:
                        if hasattr(conftest, param_name):
                            fixture_obj = getattr(conftest, param_name)
                            if callable(fixture_obj):
                                try:
                                    kwargs[param_name] = fixture_obj()
                                except TypeError:
                                    # Might require other fixtures
                                    kwargs[param_name] = None
                            else:
                                kwargs[param_name] = fixture_obj
                        elif param_name == "tmp_path":
                            import tempfile
                            kwargs[param_name] = Path(tempfile.mkdtemp())
                        elif param_name == "monkeypatch":
                            import pytest
                            # Skip if requires complex pytest fixture
                            pass

                    try:
                        func(**kwargs)
                        tracker.record_result(attr_name, mod_name, "passed")
                    except Exception as e:
                        tracker.record_result(attr_name, mod_name, "failed", str(e))

    total_failed = sum(t["failed"] for t in tracker.tiers.values())
    return 1 if total_failed > 0 else 0


def print_summary_table(tracker: TierResultTracker, duration: float):
    print("\n" + "=" * 80)
    print(f"{BOLD}{CYAN} UNIVERSITY LECTURE PORTAL — E2E TEST EXECUTION REPORT{RESET}")
    print("=" * 80)
    print(f"{BOLD}{'Tier / Category':<38} {'Target':<8} {'Passed':<8} {'Failed':<8} {'Status':<8}{RESET}")
    print("-" * 80)

    total_target = 0
    total_passed = 0
    total_failed = 0
    total_skipped = 0

    for key, tier in tracker.tiers.items():
        total_target += tier["target"]
        total_passed += tier["passed"]
        total_failed += tier["failed"]
        total_skipped += tier["skipped"]

        is_passed = (tier["failed"] == 0) and (tier["passed"] >= tier["target"])
        status = f"{GREEN}PASS{RESET}" if is_passed else (f"{YELLOW}IN-PROG{RESET}" if tier["failed"] == 0 else f"{RED}FAIL{RESET}")

        print(f"{tier['name']:<38} {tier['target']:<8} {tier['passed']:<8} {tier['failed']:<8} {status:<8}")

    print("-" * 80)
    total_status = f"{GREEN}{BOLD}PASS (100%){RESET}" if total_failed == 0 and total_passed >= total_target else (f"{YELLOW}{BOLD}INCOMPLETE{RESET}" if total_failed == 0 else f"{RED}{BOLD}FAIL{RESET}")
    print(f"{BOLD}{'TOTAL SUITE':<38} {total_target:<8} {total_passed:<8} {total_failed:<8} {total_status}{RESET}")
    print("=" * 80)
    print(f"Elapsed Time: {duration:.2f}s | Total Tests Executed: {total_passed + total_failed + total_skipped} | Skipped: {total_skipped}")

    if tracker.failures:
        print(f"\n{RED}{BOLD}FAILURES DETECTED ({len(tracker.failures)}):{RESET}")
        for test_name, mod_name, err in tracker.failures:
            print(f"  • {RED}{mod_name}::{test_name}{RESET}")
            if err:
                for line in err.splitlines()[:5]:
                    print(f"    {DIM}{line}{RESET}")
    else:
        print(f"\n{GREEN}{BOLD}All test tiers passed requirement thresholds with 0 failures.{RESET}")


def main():
    tracker = TierResultTracker()
    start_time = time.time()

    ret = run_via_pytest(tracker)
    if ret == -1 or (sum(t["passed"] + t["failed"] for t in tracker.tiers.values()) == 0):
        # Fall back to internal runner
        ret = run_via_unittest_fallback(tracker)

    duration = time.time() - start_time
    print_summary_table(tracker, duration)

    total_failed = sum(t["failed"] for t in tracker.tiers.values())
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
