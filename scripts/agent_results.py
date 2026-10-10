#!/usr/bin/env python3
"""Turn an M3 report from ``make agent`` into ``docs/results/agent-<harness>-latest.json``.

    make agent HARNESS=codex MODEL=<model> TRIALS=3
    uv run scripts/agent_results.py --harness codex --model <model>

It reads the newest ``.m3/reports/*/feedback.json`` (or ``--report PATH``), keeps the tests of
``m3_tests/agent/test_tool_selection.py`` and writes the schema that ``scripts/gen_adapters_md.py``
reads for ADAPTERS.md::

    {"harness": "codex", "model": "...", "date": "YYYY-MM-DD", "trials": 3,
     "results": {"<case id>": {"tool": "<tool>", "passed": 2, "total": 3}}}

Each trial of a prompt is one test; ``passed``/``total`` count its trials. Skipped trials (CLI or
credential missing) are not counted, since nothing was tested; a run where everything skipped
writes no file and exits 1. ``tool`` is the keyless tool the agent actually called (read from the
M3 trace), falling back to the case's first acceptable tool when no call was recorded, so a
failed prompt is still credited to the tool it should have used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEST_FILE = "m3_tests/agent/test_tool_selection.py"
TRIAL_RE = re.compile(r"-trial-(\d+)\]$")
SERVER_ALIAS = "keyless"


def latest_report(reports_dir: Path) -> Path | None:
    candidates = sorted(reports_dir.glob("*/feedback.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def called_tools(report_dir: Path, feedback: dict, test: dict) -> list[str]:
    """Names of keyless tools the agent called successfully during one test, in call order."""
    names: list[str] = []
    for execution_id in test.get("execution_ids", []):
        trace_file = feedback.get("trace_files", {}).get(execution_id)
        if not trace_file or not (report_dir / trace_file).is_file():
            continue
        trace = json.loads((report_dir / trace_file).read_text(encoding="utf-8"))
        for event in trace.get("timeline", []):
            if event.get("kind") != "tool_call" or event.get("server_binding") != SERVER_ALIAS:
                continue
            if event.get("tool_status") == "success":
                names.append((event.get("tool") or {}).get("value", ""))
    return names


def convert(
    feedback: dict, report_dir: Path, cases: dict[str, tuple[str, ...]], harness: str, model: str
) -> dict:
    """Build the result document. ``cases`` maps case id to its acceptable tool names."""
    ordered_ids = sorted(cases, key=len, reverse=True)  # longest first, so a prefix cannot win
    passed: Counter[str] = Counter()
    total: Counter[str] = Counter()
    tools: dict[str, Counter[str]] = defaultdict(Counter)
    trials = 0
    finished = ""
    for test in feedback.get("tests", []):
        node = test["node_id"]
        if not node.startswith(TEST_FILE) or test["outcome"] == "skipped":
            continue
        param = node.split("[", 1)[-1]
        case_id = next((c for c in ordered_ids if param.startswith(f"{c}-")), None)
        if case_id is None:
            continue
        total[case_id] += 1
        passed[case_id] += test["outcome"] == "passed"
        match = TRIAL_RE.search(node)
        trials = max(trials, int(match.group(1)) if match else 1)
        finished = max(finished, test.get("finished_at") or "")
        for name in called_tools(report_dir, feedback, test):
            if name in cases[case_id]:
                tools[case_id][name] += 1
    results = {
        case_id: {
            "tool": tools[case_id].most_common(1)[0][0] if tools[case_id] else cases[case_id][0],
            "passed": passed[case_id],
            "total": total[case_id],
        }
        for case_id in cases
        if total[case_id]
    }
    return {
        "harness": harness,
        "model": model,
        "date": finished[:10],
        "trials": trials,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--harness", required=True, help="harness name for the file and column")
    parser.add_argument("--model", required=True, help="model id, recorded in the file")
    parser.add_argument("--report", type=Path, help="feedback.json to read (default: newest)")
    parser.add_argument("--out", type=Path, help="output path (default docs/results/...)")
    parser.add_argument("--date", help="override the run date (YYYY-MM-DD)")
    args = parser.parse_args()

    report = args.report or latest_report(ROOT / ".m3" / "reports")
    if report is None or not report.is_file():
        sys.exit("agent_results: no feedback.json found; run `make agent` first")
    from m3_tests.agent.test_tool_selection import CASES

    feedback = json.loads(report.read_text(encoding="utf-8"))
    cases = {case.id: case.tools for case in CASES}
    document = convert(feedback, report.parent, cases, args.harness, args.model)
    if args.date:
        document["date"] = args.date
    if not document["results"]:
        sys.exit(
            f"agent_results: {report} has no executed {TEST_FILE} tests (all skipped or none "
            "collected); nothing written"
        )
    out = args.out or ROOT / "docs" / "results" / f"agent-{args.harness}-latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    passed = sum(r["passed"] for r in document["results"].values())
    total = sum(r["total"] for r in document["results"].values())
    print(f"wrote {out} ({passed}/{total} trials passed across {len(document['results'])} prompts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
