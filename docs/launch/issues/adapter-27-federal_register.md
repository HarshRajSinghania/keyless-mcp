---
title: "Add a Federal Register adapter for US rules and notices"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:news"]
---

The Federal Register is the daily journal of the US government: proposed rules, final rules, notices and presidential documents. An agent can use it to find what an agency published on a subject, with links to the official text.

## API

- Docs: https://www.federalregister.gov/developers/documentation/api/v1
- Base URL: `https://www.federalregister.gov/api/v1`
- It works without a key, token or account.
- Suggested adapter name: `federal_register`, in the `news` toolset.

## Proposed tools

### `federal_register_search_documents(term: str, document_type: str | None = None, per_page: int = 5)`

Search documents by keyword, optionally by type (`RULE`, `PRORULE`, `NOTICE`, `PRESDOCU`). Returns title, type, agencies, publication date, abstract and links.

### `federal_register_get_document(document_number: str)`

Get one document by its number, such as `2024-00001`.

## Example

```text
GET https://www.federalregister.gov/api/v1/documents.json?per_page=2&conditions[term]=artificial+intelligence
```

Fields worth returning: `count`, `total_pages` and `results[]` with `title`, `type`, `abstract`, `document_number`, `html_url`, `pdf_url`, `publication_date`, `agencies` and `excerpts`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=federal_register TOOLSET=news`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/documents/0000-00000.json` returns a 404 with an HTML page.
- [ ] `make record ADAPTER=federal_register` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Filters use bracket syntax, for example `conditions[term]` and `conditions[type][]`. Check that the shared client sends them unescaped in a way the API accepts, and record the cassette to confirm.
- `excerpts` and `abstract` contain HTML. Use `strip_html`.
- These are US government works, so there is no licensing concern. Include the link anyway.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
