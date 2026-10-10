---
title: "Group the real-agent tests by category and report a pass rate for each"
labels: ["help wanted", "hacktoberfest", "area:testing"]
---

## Context

The real-agent lane (`m3_tests/agent/test_tool_selection.py`) has ten prompts, roughly one per adapter, and ADAPTERS.md shows pass rates per adapter. That tells us whether each tool can be found. It does not tell us where agents struggle as a group, such as picking between look-alike tools in the `dev` toolset (npm, PyPI, OSV), or leaving the tools alone when a question needs none.

`docs/agent-testing.md` explains the two lanes and how pass rates work.

## Proposed approach

- Add a `category` field to `Case` in `test_tool_selection.py`. Start with each toolset name, plus `look-alike` (for prompts where a neighbouring tool is tempting, using `must_not_call`) and `no-tool` (a plain question where the right behaviour is to call nothing).
- Add at least two more prompts per toolset, and a few `no-tool` prompts. A no-tool case asserts that the agent made no call to a keyless tool.
- Add a `CATEGORY` variable to the `agent` target in the `Makefile`, so `make agent HARNESS=codex MODEL=<id> CATEGORY=dev` runs one category. A pytest marker or `-k` filter both work.
- Extend `scripts/agent_results.py` to write per-category totals into the results JSON, and show them as a small table in `docs/agent-testing.md` or in ADAPTERS.md (`scripts/gen_adapters_md.py`).

## Acceptance criteria

- [ ] Every case has a category, and the file's docstring explains the categories.
- [ ] At least two prompts per toolset and three `no-tool` prompts exist, and none of them names a tool.
- [ ] `make agent ... CATEGORY=<name>` runs only that category.
- [ ] The results file records per-category passed and total counts, and `make adapters-md` still works with older result files that have no categories.
- [ ] `make test` and `make lint` pass. The agent lane never runs in `make test`.
- [ ] You ran the lane at least once with a real harness and attached the per-category result in the pull request. If you have no credentials, say so and a maintainer will run it.

## Notes

Report every trial, as the existing doc asks. A few trials on one day is an observation about one model, not a stable rate.

Comment below to claim this.
