---
title: "Add a pagination helper to the core for adapters that need more than one page"
labels: ["help wanted", "hacktoberfest", "area:core"]
---

## Context

Adapters read a single page today. APIs page in different ways: an offset and a count (arXiv takes `start` and `max_results`), a page number, a `next` URL, or an opaque cursor. When a tool needs more results than one page holds, each author would otherwise write their own loop, with their own bugs and no cap on how much comes back. Agents pay for every byte of a result, so a cap matters as much as the loop.

## Proposed approach

- Add `src/keyless_mcp/core/pagination.py` with one async helper, for example `paginate(fetch_page, *, limit, max_pages)`. `fetch_page` is a coroutine the adapter supplies. It takes a position and returns `(items, next_position)`, where `next_position` is `None` at the end.
- The helper stops at `limit` items or `max_pages` pages, whichever comes first, and returns the items plus a `truncated` flag so the tool can tell the agent there is more.
- Hard maximums apply even if the caller asks for more, to protect the agent's context window.
- Export it from `keyless_mcp.core` and document it in `docs/adapter-contract.md` with a short example for each of the three common styles.
- Use it in one existing adapter that benefits, and keep that adapter's behaviour and tests unchanged where they pass today.

## Acceptance criteria

- [ ] Unit tests cover offset, page-number and next-URL styles with a fake `fetch_page`, including the last page and an empty first page.
- [ ] The `limit` and `max_pages` caps are tested, and `truncated` is set correctly.
- [ ] No test touches the network.
- [ ] The adapter contract documents the helper, and the example in the docs runs as written.
- [ ] `make test` and `make lint` pass.

## Notes

Resist adding a class hierarchy. A single function and a clear docstring is easier for first-time contributors to use.

Comment below to claim this.
