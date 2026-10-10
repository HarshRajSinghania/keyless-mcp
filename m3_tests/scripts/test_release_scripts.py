"""Tests for the CI and release helper scripts in ``scripts/`` (no network, no M3 server)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.m3(suite_name="scripts")

ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"script_{name}", ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


def test_adapters_md_is_up_to_date() -> None:
    """Adding or changing an adapter means running `make adapters-md`; CI enforces it."""
    done = run_script("scripts/gen_adapters_md.py", "--check")
    assert done.returncode == 0, done.stdout + done.stderr


def test_adapters_md_lists_every_tool_and_a_column_per_harness(tmp_path: Path) -> None:
    def result(harness: str, passed: int) -> Path:
        path = tmp_path / f"agent-{harness}-latest.json"
        path.write_text(
            json.dumps(
                {
                    "harness": harness,
                    "model": "m",
                    "date": "2026-01-01",
                    "trials": 3,
                    "results": {"a": {"tool": "arxiv_search", "passed": passed, "total": 3}},
                }
            )
        )
        return path

    out = tmp_path / "ADAPTERS.md"
    done = run_script(
        "scripts/gen_adapters_md.py",
        "--results",
        str(result("claude", 3)),
        str(result("codex", 1)),
        "--output",
        str(out),
    )
    assert done.returncode == 0, done.stderr
    text = out.read_text()
    assert "Agent pass rate (claude)" in text and "Agent pass rate (codex)" in text
    arxiv_row = next(line for line in text.splitlines() if "`arxiv_search`" in line)
    assert "| 3/3 | 1/3 |" in arxiv_row
    wikipedia_row = next(line for line in text.splitlines() if "`wikipedia_search`" in line)
    assert wikipedia_row.endswith("| - | - |")


def test_adapters_md_rejects_a_malformed_results_file(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"harness": "x", "results": {"a": {"tool": "t"}}}))
    done = run_script("scripts/gen_adapters_md.py", "--results", str(bad), "--check")
    assert done.returncode != 0 and "results schema" in done.stderr


def feedback(tests: list[dict], **summary: object) -> dict:
    return {"summary": {"run_status": "finished", **summary}, "tests": tests}


def adapter_test(adapter: str, name: str, outcome: str = "passed", executions: int = 1) -> dict:
    return {
        "node_id": f"m3_tests/adapters/{adapter}/test_{adapter}.py::{name}",
        "outcome": outcome,
        "execution_ids": [f"execution-{name}"] * executions,
    }


def test_check_feature_results_accepts_a_covered_run() -> None:
    check = load_script("check_feature_results").check
    problems, _ = check(
        feedback([adapter_test("a", "t1"), adapter_test("a", "helper", executions=0)]), ["a"]
    )
    assert problems == []


def test_check_feature_results_flags_adapters_that_never_reached_the_server() -> None:
    check = load_script("check_feature_results").check
    problems, _ = check(
        feedback([adapter_test("a", "helper", executions=0), adapter_test("b", "t", "failed")]),
        ["a", "b", "c"],
    )
    text = "\n".join(problems)
    assert "'a'" in text and "none produced an M3 execution id" in text
    assert "'c'" in text and "no tests in the report" in text
    assert "tests did not pass" in text


def test_check_feature_results_flags_an_unfinished_run() -> None:
    check = load_script("check_feature_results").check
    problems, _ = check(feedback([adapter_test("a", "t")], run_status="running"), ["a"])
    assert any("did not finish" in p for p in problems)


def agent_node(case: str, trial: int, outcome: str) -> dict:
    return {
        "node_id": "m3_tests/agent/test_tool_selection.py::test_agent_picks_the_right_tool"
        f"[{case}-codex-some-model-codex-trial-{trial}]",
        "outcome": outcome,
        "execution_ids": [f"execution-{case}-{trial}"],
        "finished_at": "2026-03-04T10:00:00+00:00",
    }


def write_trace(report_dir: Path, feedback_doc: dict, case: str, trial: int, tool: str) -> None:
    execution = f"execution-{case}-{trial}"
    path = f"traces/{execution}.json"
    (report_dir / "traces").mkdir(exist_ok=True)
    (report_dir / path).write_text(
        json.dumps(
            {
                "timeline": [
                    {
                        "kind": "tool_call",
                        "server_binding": "keyless",
                        "tool_status": "success",
                        "tool": {"value": tool},
                    }
                ]
            }
        )
    )
    feedback_doc.setdefault("trace_files", {})[execution] = path


def test_agent_results_counts_trials_and_reads_the_called_tool(tmp_path: Path) -> None:
    convert = load_script("agent_results").convert
    doc = feedback(
        [
            agent_node("country", 1, "passed"),
            agent_node("country", 2, "failed"),
            agent_node("country", 3, "passed"),
            agent_node("country-x", 1, "skipped"),
            agent_node("search", 1, "failed"),
        ]
    )
    write_trace(tmp_path, doc, "country", 1, "by_code")
    write_trace(tmp_path, doc, "country", 3, "by_code")
    cases = {"country": ("by_name", "by_code"), "country-x": ("x",), "search": ("search_tool",)}
    out = convert(doc, tmp_path, cases, "codex", "some-model")
    assert out == {
        "harness": "codex",
        "model": "some-model",
        "date": "2026-03-04",
        "trials": 3,
        "results": {
            "country": {"tool": "by_code", "passed": 2, "total": 3},
            "search": {"tool": "search_tool", "passed": 0, "total": 1},
        },
    }


def test_release_metadata_is_consistent() -> None:
    """pyproject.toml, server.json and the OCI tag name one version; bump them together."""
    problems = load_script("check_release").problems_for(None)
    assert problems == []
