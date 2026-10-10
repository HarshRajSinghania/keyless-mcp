---
title: "Add a Wayback Machine adapter to find archived snapshots of a URL"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:reference"]
---

The Wayback Machine keeps snapshots of web pages going back to the 1990s. An agent that can list captures of a URL can answer "what did this page say in 2020?" by pointing to the archived copy.

## API

- Docs: https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server
- Base URL: `https://web.archive.org/cdx/search/cdx`
- It works without a key, token or account.
- Suggested adapter name: `wayback_cdx`, in the `reference` toolset.

## Proposed tools

### `wayback_cdx_list_snapshots(url: str, limit: int = 5, from_year: int | None = None, to_year: int | None = None)`

List captures of a URL. Returns the timestamp, status code, MIME type and a ready-to-open archive link for each. Only successful (200) captures are returned.

### `wayback_cdx_closest_snapshot(url: str, timestamp: str)`

Find the capture closest to a date given as `YYYYMMDD` or `YYYYMMDDhhmmss`.

## Example

```text
GET https://web.archive.org/cdx/search/cdx?url=example.com&limit=2&output=json
```

Fields worth returning: With `output=json` the response is a list of lists. The first row is a header: `urlkey`, `timestamp`, `original`, `mimetype`, `statuscode`, `digest`, `length`. Build the link as `https://web.archive.org/web/<timestamp>/<original>`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=wayback_cdx TOOLSET=reference`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a URL with no captures returns an empty list (`[]`), which the tool should report as no snapshots, and a malformed URL or timestamp should raise `InvalidInput`.
- [ ] `make record ADAPTER=wayback_cdx` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Skip the header row.
- Add `filter=statuscode:200`. A `closest` query for `example.com` returned a revisit record with status `-`.
- Use `closest=<timestamp>&sort=closest&limit=1` for the closest-snapshot tool.
- The older `archive.org/wayback/available` endpoint returned an empty `archived_snapshots` object for `example.com` when this issue was written, so do not build on it.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
