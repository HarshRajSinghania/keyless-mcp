---
title: "Add a Crossref adapter to look up scholarly works and DOIs"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:science"]
---

Crossref is the registry behind most DOIs for journal articles, books and conference papers. An agent that can ask it who wrote a paper, where it was published and how often it is cited can check a reference instead of guessing at one. arXiv is already covered, so this adds the published side of research.

## API

- Docs: https://api.crossref.org/swagger-ui/index.html
- Base URL: `https://api.crossref.org`
- It works without a key, token or account.
- Suggested adapter name: `crossref`, in the `science` toolset.

## Proposed tools

### `crossref_search_works(query: str, rows: int = 5)`

Search scholarly works by free text. Returns, for each match, the DOI, title, first authors, year, journal or book title, type and citation count, plus the total number of matches.

### `crossref_get_work(doi: str)`

Fetch one work by DOI with the same fields, plus the publisher and the URL of its DOI page.

## Example

```text
GET https://api.crossref.org/works?query=attention+is+all+you+need&rows=2&select=DOI,title,author,issued,container-title,is-referenced-by-count,type
```

Fields worth returning: `message.total-results`, and in `message.items[]`: `DOI`, `title` (a list), `author[]` with `given` and `family`, `issued.date-parts` (for example `[[2025]]`), `container-title` (a list), `is-referenced-by-count` and `type`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=crossref TOOLSET=science`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an unknown DOI such as `10.9999/doesnotexist` returns a 404 with the body `Resource not found.`
- [ ] `make record ADAPTER=crossref` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The `select` parameter limits which fields come back. Without it each work is several kilobytes.
- `title` and `container-title` are lists and can be empty, and `author` can be missing. Handle all three.
- Crossref asks API users to identify themselves and gives better service to those who do. The shared client's User-Agent already names this project, so read the etiquette section of the docs before you pick `rate_limit_per_minute`.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
