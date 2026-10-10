---
title: "Add a NOAA Space Weather adapter for the Kp index and alerts"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:science"]
---

NOAA's Space Weather Prediction Center publishes the planetary Kp index, which measures geomagnetic activity, along with watches and warnings. "Is there a geomagnetic storm right now?" is a common question that a model cannot answer from training data.

## API

- Docs: https://www.swpc.noaa.gov/products-and-data
- Base URL: `https://services.swpc.noaa.gov`
- It works without a key, token or account.
- Suggested adapter name: `noaa_swpc`, in the `science` toolset.

## Proposed tools

### `noaa_swpc_kp_index(limit: int = 8)`

Return the most recent planetary Kp index readings with their timestamps.

### `noaa_swpc_alerts(limit: int = 5)`

Return the most recent space weather alerts, watches and warnings, with the issue time and the message text trimmed to a readable length.

## Example

```text
GET https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json
```

Fields worth returning: The Kp file is a list of objects with `time_tag`, `Kp`, `a_running` and `station_count`. The alerts file (`/products/alerts.json`) is a list of objects with `product_id`, `issue_datetime` and `message`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=noaa_swpc TOOLSET=science`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a `limit` of 0 or 500 should raise `InvalidInput`. These are static files, so there is no query to get wrong.
- [ ] `make record ADAPTER=noaa_swpc` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Both endpoints return the whole file and take no query parameters. Trim to `limit` inside the adapter.
- Check which end of each list is the newest. When this issue was written, the Kp list started with the oldest reading and the alerts list started with the newest.
- Alert messages contain `\r\n` line breaks. Use `tidy` or `truncate` from `keyless_mcp.core`.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
