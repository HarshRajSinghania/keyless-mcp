---
title: "Add a /health endpoint to the HTTP transport and use it in the Docker image"
labels: ["help wanted", "hacktoberfest", "area:core"]
---

## Context

`keyless-mcp --transport http` serves MCP at `/mcp`. There is no way for a load balancer, a Docker `HEALTHCHECK` or a person with `curl` to ask whether the server is up without speaking MCP. The existing test in `m3_tests/core/test_transport.py` works around this by sending a bare GET to `/mcp` and treating an HTTP error as proof the server is alive.

`MCPServer` supports extra routes with `custom_route(path, methods=...)`. Its docstring in `mcp/server/mcpserver/server.py` uses `/health` as the example.

## Proposed approach

- In `build_server` (`src/keyless_mcp/server.py`) or in `main` for the HTTP transport, register `GET /health`. It returns JSON such as `{"status": "ok", "version": "0.1.0", "toolsets": ["dev", "geo"], "tools": 6}`.
- The handler must not call any upstream API. It reports only what the process already knows.
- Add a `HEALTHCHECK` line to the `Dockerfile`. The runtime image is `python:3.12-slim` and has no `curl`, so use a one-line `python -c` with `urllib`.
- The route exists for the HTTP transport only. Stdio has no HTTP surface.

## Acceptance criteria

- [ ] `curl http://127.0.0.1:8000/health` returns 200 and the JSON above while the server runs with `--transport http`.
- [ ] The response lists the toolsets and tool count that are actually served, so `--toolsets dev` shows `dev` only.
- [ ] A test in `m3_tests/core/test_transport.py` starts the server on a free port and checks `/health`. The startup wait in that file can use the new endpoint.
- [ ] The `Dockerfile` has a working `HEALTHCHECK` (note in the pull request how you checked it, since not everyone has Docker handy).
- [ ] The README's Streamable HTTP section mentions `/health`.
- [ ] `make test` and `make lint` pass.

## Notes

Keep the response small and stable. Operators will parse it.

Comment below to claim this.
