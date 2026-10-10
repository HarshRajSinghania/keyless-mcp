---
title: "Smoke-test the Docker image as an MCP server, before and after publishing"
labels: ["help wanted", "hacktoberfest", "area:ci"]
---

## Context

The `docker` job in `.github/workflows/release.yml` builds the image, runs `--version` and `--list-tools`, checks that it does not run as root, and then pushes a multi-architecture image. It never checks that the container speaks MCP, and it never tests the image that users will actually pull from `ghcr.io`. A broken entrypoint or a missing dependency in the final stage would pass today and surface as a bug report.

The Dockerfile is not exercised on pull requests at all, so a change to it can break the release without any earlier signal.

## Proposed approach

- Write a small script in `scripts/` that starts a command as an MCP stdio server, lists the tools and checks the count. The `mcp` client is already a dependency, and `mcp.client.stdio.stdio_client` can run `docker run -i --rm <image>`.
- For the HTTP transport, run the container with `--transport http --host 0.0.0.0` and a published port, then connect to `/mcp` with the MCP client (and to `/health` if that endpoint exists by then).
- Run both checks in the release job against the locally built image before the push.
- Add a step after the push that pulls the exact tag from `ghcr.io` and repeats the checks, and runs once with `--platform linux/arm64`, which uses the QEMU setup already in the job.
- Add a PR job that builds the Dockerfile and runs the smoke test when the Dockerfile, `pyproject.toml`, `uv.lock` or `src/` changes.

## Acceptance criteria

- [ ] The script exits non-zero with a clear message when the tool count is wrong or the server does not answer.
- [ ] The release job runs the stdio and HTTP checks before it pushes.
- [ ] A post-push step checks the published image on amd64 and arm64.
- [ ] A pull request that touches the Dockerfile triggers a build and smoke test.
- [ ] The script has a test in `m3_tests/scripts/` that runs it against `uv run keyless-mcp`, so it is covered without Docker.
- [ ] Actions are pinned to commit SHAs, as in the existing workflows.

## Notes

You can develop and test most of this with `docker run` on your own machine. If you cannot test the release job itself, say so and a maintainer will run it from a branch.

Comment below to claim this.
