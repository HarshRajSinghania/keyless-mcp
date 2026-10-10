#!/usr/bin/env python3
"""Fail CI unless the latest M3 report proves every adapter was tested through M3.

``m3 ci test`` already fails the job when a test fails. This script closes the gap it cannot:
a test file that passes without ever driving the MCP server (a typo in a marker, a mistaken
``-k``, a deselected suite) would leave CI green and prove nothing. So it reads the newest
``.m3/reports/*/feedback.json`` and asserts:

* the run finished, with no failed, errored or not-run tests and no collection errors;
* every adapter in ``keyless_mcp.adapters`` has tests in the report, and at least one of them
  produced an M3 execution id (an execution id is M3's receipt that a server call was made,
  recorded and evaluated). Pure-Python helper tests in an adapter's file have none, which is
  fine as long as the adapter's server tests do.

Run it from the repository root after ``make test`` or ``m3 ci test``:
``.venv/bin/python scripts/check_feature_results.py [REPORTS_DIR]``.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from keyless_mcp.core import discover_adapters  # noqa: E402


def latest_report(reports_dir: Path) -> Path | None:
    """The newest ``feedback.json`` under ``reports_dir``, or None when there is none."""
    candidates = sorted(reports_dir.glob("*/feedback.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def check(feedback: dict, adapter_names: list[str]) -> tuple[list[str], str]:
    """Return ``(problems, summary)`` for a parsed feedback.json."""
    problems: list[str] = []
    tests = feedback.get("tests", [])
    summary = feedback.get("summary", {})
    outcomes = Counter(t["outcome"] for t in tests)

    if summary.get("run_status") != "finished":
        problems.append(f"run did not finish (run_status={summary.get('run_status')!r})")
    if not tests:
        problems.append("the report contains no tests")
    if summary.get("collection_errors"):
        problems.append(f"{summary['collection_errors']} collection error(s)")
    bad = {k: v for k, v in outcomes.items() if k not in ("passed", "xfailed") and v}
    if bad:
        failing = [t["node_id"] for t in tests if t["outcome"] in bad][:10]
        problems.append(f"tests did not pass {dict(bad)}: " + "; ".join(failing))

    per_adapter: dict[str, list[dict]] = {name: [] for name in adapter_names}
    for test in tests:
        parts = test["node_id"].split("::")[0].split("/")
        if len(parts) >= 3 and parts[0] == "m3_tests" and parts[1] == "adapters":
            per_adapter.setdefault(parts[2], []).append(test)
    for name in adapter_names:
        adapter_tests = per_adapter[name]
        with_execution = [t for t in adapter_tests if t.get("execution_ids")]
        if not adapter_tests:
            problems.append(f"adapter {name!r}: no tests in the report (m3_tests/adapters/{name})")
        elif not with_execution:
            problems.append(
                f"adapter {name!r}: {len(adapter_tests)} test(s) ran but none produced an M3 "
                "execution id, so no server call was recorded"
            )

    covered = sum(
        1 for name in adapter_names if any(t.get("execution_ids") for t in per_adapter[name])
    )
    unlinked = sum(not t.get("execution_ids") for t in tests)
    text = (
        f"M3 coverage: {len(tests)} tests ({outcomes.get('passed', 0)} passed, "
        f"{unlinked} pure-Python without an execution id); "
        f"{covered}/{len(adapter_names)} adapters have M3-recorded server calls; "
        f"run status {summary.get('run_status')}."
    )
    return problems, text


def main(argv: list[str]) -> int:
    reports_dir = Path(argv[1]) if len(argv) > 1 else ROOT / ".m3" / "reports"
    report = latest_report(reports_dir)
    if report is None:
        print(f"FAIL: no feedback.json under {reports_dir}. Did the M3 run write a report?")
        return 1
    feedback = json.loads(report.read_text(encoding="utf-8"))
    problems, summary = check(feedback, [spec.name for spec in discover_adapters()])
    print(f"report: {report.relative_to(ROOT) if report.is_relative_to(ROOT) else report}")
    print(summary)
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with Path(step_summary).open("a", encoding="utf-8") as handle:
            handle.write(f"{summary}\n")
    if problems:
        print("\nFAIL:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
