---
title: "Add an endoflife.date adapter for software support and end-of-life dates"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:dev"]
---

endoflife.date tracks release cycles and end-of-life dates for hundreds of products, from Python to Ubuntu. "Is Python 3.9 still supported?" is a question models get wrong, because the answer changes with the calendar.

## API

- Docs: https://endoflife.date/docs/api/
- Base URL: `https://endoflife.date/api`
- It works without a key, token or account.
- Suggested adapter name: `endoflife`, in the `dev` toolset.

## Proposed tools

### `endoflife_get_product(product: str)`

List a product's release cycles with the latest version of each, its release date, end-of-life date and whether it is an LTS. Add an `eol_passed` flag computed from today's date.

### `endoflife_list_products()`

List the product names the service tracks, for when the agent does not know the slug.

## Example

```text
GET https://endoflife.date/api/python.json
```

Fields worth returning: A list of cycles, each with `cycle`, `releaseDate`, `eol`, `latest`, `latestReleaseDate`, `lts` and `support`. `/api/all.json` is a list of product slugs.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=endoflife TOOLSET=dev`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/api/notaproduct.json` returns a 404 with an HTML page.
- [ ] `make record ADAPTER=endoflife` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- `eol` and `support` can be a date string or a boolean, depending on the product. Handle both.
- The service also has a newer `/api/v1/` layout. The docs describe the options. Pick one and note it in `adapter.yaml`.
- Cap the number of cycles returned, since some products have dozens.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
