---
title: "Retry GET requests with backoff on 429 and 5xx responses"
labels: ["help wanted", "hacktoberfest", "area:core"]
---

## Context

`HttpClient._send` in `src/keyless_mcp/core/http.py` makes one attempt. If an upstream answers 429 or a short-lived 502, 503 or 504, the agent gets an error and has to retry by itself, and most agents give up. Public APIs hiccup often enough that one quiet retry would make the tools feel noticeably more reliable.

## Proposed approach

- Retry GET requests up to two more times when the response is 429, 502, 503 or 504, and when the connection fails before any response arrives.
- If the response has a `Retry-After` header in seconds, wait that long, capped at a few seconds so a tool call never stalls the agent. Otherwise use exponential backoff with jitter, starting around half a second.
- Keep the total time inside the client's timeout budget, and apply the rate limiter to each attempt.
- Do not retry POST by default. `osv` uses `post_json` for a read-only query, so decide whether `post_json` needs an opt-in flag, and say what you chose.
- When retries run out, the `UpstreamError` message should say how many attempts were made.
- In record mode, write the final response only, not the failed attempts.

## Acceptance criteria

- [ ] A 503 followed by a 200 returns the 200 and makes exactly two requests (use `httpx.MockTransport`).
- [ ] A persistent 503 raises `UpstreamError` after three attempts, with the attempt count in the message.
- [ ] A 429 with `Retry-After: 2` waits two seconds (inject the sleep function, as `RateLimiter` does) and then retries.
- [ ] 404 and other 4xx responses are not retried.
- [ ] POST is not retried unless you add an explicit opt-in, and a test covers whichever rule you pick.
- [ ] No test sleeps for real.
- [ ] `make test` and `make lint` pass.

## Notes

`m3_tests/core/test_http.py` and `test_error_mapping.py` show how the client is tested today.

Comment below to claim this.
