---
title: "Score each adapter's quality in the contract test"
labels: ["help wanted", "hacktoberfest", "area:testing"]
---

## Context

`m3_tests/catalog/test_contract.py` checks that every tool and parameter has a description, that a test file exists and that there is at least one cassette. It cannot tell a good description from a lazy one. Agents choose tools from those sentences, so quality matters, and reviewers currently judge it by eye.

## Proposed approach

Write a small scoring function, in `scripts/adapter_score.py` or a module under `m3_tests/_support/`, that gives each adapter a score from 0 to 100 from checks anyone can read:

- tool descriptions are at least a full sentence and say what the tool returns
- each parameter description has an example value or states its limits
- `adapter.yaml` has a one-sentence description and a docs URL that is not a placeholder
- the adapter's test file has an error-path test (an assertion on `is_error is True`) and a `live` smoke test
- the cassettes are small, with a size limit per file
- `rate_limit_per_minute` is set to something other than the scaffold default

Print a table of scores at the end of `make test`, and fail the contract test if an adapter scores below a threshold. Document the rubric in `docs/adapter-contract.md` so contributors know what is measured before they submit.

## Acceptance criteria

- [ ] The scoring code is deterministic, offline, and has its own tests with a good adapter and a bad one.
- [ ] Each of the eight existing adapters passes the threshold. If one does not, either improve it in the same pull request or explain why the rubric should change.
- [ ] A freshly scaffolded, unedited adapter scores below the threshold, so TODOs left in the scaffold are caught.
- [ ] The rubric is in `docs/adapter-contract.md`, and the failure message tells the contributor what to fix.
- [ ] Optional: show the score in ADAPTERS.md through `scripts/gen_adapters_md.py`.
- [ ] `make test` and `make lint` pass.

## Notes

Prefer checks that catch real problems over checks that can be satisfied by padding. A description should not pass just because it is long.

Comment below to claim this.
