---
title: "Run the offline test suite on Windows in CI"
labels: ["help wanted", "hacktoberfest", "area:ci"]
---

## Context

CI (`.github/workflows/ci.yml`) runs on `ubuntu-24.04` only, and CONTRIBUTING.md tells Windows users to use WSL because nothing has been tried on native Windows. Some Windows users will run keyless-mcp from `uvx` without ever touching the repository, so the package itself should work there too.

Places that will probably break:

- `m3_tests/core/test_transport.py` starts the server with `"PATH": "/usr/bin:/bin"`, a Unix path.
- The `Makefile` and `scripts/m3` assume a Unix shell and `.venv/bin/python`. On Windows the interpreter is `.venv\Scripts\python.exe`.
- Cassettes are JSON files compared byte for byte, so line endings matter. A `.gitattributes` with `eol=lf` for `*.json` would keep them stable.

## Proposed approach

- Add a `windows-latest` job that runs the same offline suite without `make`: `uv sync --locked`, install the matching `sf-m3-cli` (the existing job shows how to read the version from the lock), `m3 setup --python .venv\Scripts\python.exe`, then `m3 ci test` with the same `-m "not live and not agent"` filter.
- Fix what fails, preferring small changes in test support code over special cases in the server.
- Add `.gitattributes` if line endings turn out to matter.
- Pin new actions to commit SHAs, as the other workflows do.

## Acceptance criteria

- [ ] A Windows job runs on every pull request and passes.
- [ ] Any test you have to skip on Windows has a documented reason in the code.
- [ ] `uvx --from . keyless-mcp --list-tools` works on the runner, which proves the package starts.
- [ ] CONTRIBUTING.md says what is supported on Windows after your change.
- [ ] The Linux job is unchanged and still green.

## Notes

If you do not have a Windows machine, you can still do this by iterating on the CI job in your fork.

Comment below to claim this.
