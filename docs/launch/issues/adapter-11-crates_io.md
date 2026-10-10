---
title: "Add a crates.io adapter for Rust packages"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:dev"]
---

crates.io is the Rust package registry. The npm and PyPI adapters already let an agent check a package before recommending it, and this does the same for Rust crates.

## API

- Docs: https://crates.io/data-access
- Base URL: `https://crates.io/api/v1`
- It works without a key, token or account.
- Suggested adapter name: `crates_io`, in the `dev` toolset.

## Proposed tools

### `crates_io_get_crate(name: str)`

Get a crate's latest version, description, download counts, repository, documentation link and its five most recent versions.

### `crates_io_search(query: str, per_page: int = 5)`

Search crates by keyword. Returns name, latest version, description and download counts.

## Example

```text
GET https://crates.io/api/v1/crates?q=serde&per_page=2
```

Fields worth returning: Search returns `meta.total` and `crates[]` with `id`, `name`, `downloads`, `recent_downloads`, `default_version` and `num_versions`. The crate endpoint returns `crate` (with `name`, `max_version`, `downloads`, `repository`, `description`), `versions[]`, `keywords` and `categories`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=crates_io TOOLSET=dev`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/crates/zzzznotacrate12345` returns a 404 with `crate ... does not exist` in an `errors` list.
- [ ] `make record ADAPTER=crates_io` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The crate endpoint for `serde` is about 440 KB, because it lists every version. Return only the top fields and the latest few versions.
- The license is on the version objects and not on `crate`.
- The crates.io data access policy asks for a User-Agent that identifies you and for a modest request rate. Read it before you choose `rate_limit_per_minute`.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
