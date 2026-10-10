---
title: "Add an opt-in response cache to the shared HTTP client"
labels: ["help wanted", "hacktoberfest", "area:core"]
---

## Context

Every tool call goes to the upstream API, even when an agent asks the same question twice in a row. The `world_bank` adapter works around that by hand: it keeps the country list in a list inside `adapters/world_bank/tools.py` (search for `countries_cache`). Several upstream APIs ask clients to cache, including PokeAPI and the Nominatim usage policy, and nearly every adapter would benefit.

The shared client lives in `src/keyless_mcp/core/http.py`. `HttpClient.fetch` is the single place where a request becomes a response, so a cache belongs there.

## Proposed approach

- Add a small in-memory cache inside `HttpClient`, keyed the same way cassettes are keyed (method, canonical URL, body). `cassette.canonical_url` already sorts query parameters.
- Cache successful GET responses only. Never cache errors, and never cache POST.
- Make it opt in per adapter with an optional `cache_ttl_seconds` field in `adapter.yaml`. The default is no caching, so existing adapters behave exactly as they do now. That means `AdapterSpec` in `core/adapters.py` needs an optional field, and `docs/adapter-contract.md` and the template in `src/keyless_mcp/adapters/_template/adapter.yaml` need a line about it.
- Bound the cache (an LRU of a few hundred entries is plenty) so a long session cannot grow without limit.
- Check the cache before the rate limiter, so a hit does not use up a request slot.
- Record and replay modes bypass the cache. A cassette must always reflect a real request.

## Acceptance criteria

- [ ] A second identical GET inside the TTL makes no upstream request. Show this with `httpx.MockTransport`: `HttpClient` already accepts a `transport` argument.
- [ ] After the TTL, the request goes upstream again (inject a clock, as `RateLimiter` does).
- [ ] Errors are not cached, and POST requests are not cached.
- [ ] Replay and record modes never read from or write to the cache.
- [ ] The cache is bounded, with a test for eviction.
- [ ] `docs/adapter-contract.md` documents `cache_ttl_seconds`, and the scaffold template mentions it.
- [ ] `make test` and `make lint` pass.
- [ ] Optional: switch `world_bank` to the new field and delete its hand-written cache.

## Notes

Tests for the core live in `m3_tests/core/`. Look at `test_http.py` for how the client is exercised without the network.

Comment below to claim this. If you want to discuss the design first, open a discussion and link it here.
