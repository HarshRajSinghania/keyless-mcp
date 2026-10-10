---
title: "Add a RubyGems adapter for gem lookups"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:dev"]
---

RubyGems is the Ruby package registry. An agent that can look up a gem's latest version, license and source repository can answer dependency questions for Ruby projects.

## API

- Docs: https://guides.rubygems.org/rubygems-org-api/
- Base URL: `https://rubygems.org/api/v1`
- It works without a key, token or account.
- Suggested adapter name: `rubygems`, in the `dev` toolset.

## Proposed tools

### `rubygems_get_gem(name: str)`

Get a gem's latest version, authors, summary, license, total downloads, publish date and project links.

### `rubygems_search(query: str, limit: int = 5)`

Search gems by name or keyword. Returns name, latest version, summary and download count.

## Example

```text
GET https://rubygems.org/api/v1/gems/rails.json
```

Fields worth returning: `name`, `version`, `version_created_at`, `downloads`, `version_downloads`, `authors`, `info`, `licenses`, `yanked`, and a `metadata` object with `source_code_uri`, `changelog_uri` and `documentation_uri`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=rubygems TOOLSET=dev`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/gems/zzzznotagem.json` returns a 404 with the plain-text body `This rubygem could not be found.`
- [ ] `make record ADAPTER=rubygems` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The 404 body is text, not JSON. The shared client raises `UpstreamError` with the status before anything parses it, so catch status 404 and raise `InvalidInput`.
- The search endpoint (`/search.json?query=rails`) returns a list of gem objects with the same fields as the lookup. Return the first `limit` of them yourself.
- `info` can be long. Use `truncate`.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
