---
title: "Add a Bank of Canada Valet adapter for rates and series"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:finance"]
---

The Bank of Canada's Valet API serves its published series: exchange rates, interest rates and indices. It is a clean, keyless source for the Canadian dollar and for central bank rates.

## API

- Docs: https://www.bankofcanada.ca/valet/docs
- Base URL: `https://www.bankofcanada.ca/valet`
- It works without a key, token or account.
- Suggested adapter name: `bank_of_canada`, in the `finance` toolset.

## Proposed tools

### `bank_of_canada_get_observations(series: str = "FXUSDCAD", recent: int = 5)`

Get the most recent observations of a series, with its label and description.

### `bank_of_canada_search_series(query: str, limit: int = 10)`

Find series by words in their name or description, so the agent can discover the right series id.

## Example

```text
GET https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=2
```

Fields worth returning: `seriesDetail` (with `label` and `description`) and `observations[]`, each with `d` for the date and the series id holding `{"v": "1.4271"}`. `/lists/series/json` returns a `series` object keyed by id with `label` and `description`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=bank_of_canada TOOLSET=finance`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an unknown series (`/observations/NOTASERIES/json`) returns a 404 with a JSON message that names the series.
- [ ] `make record ADAPTER=bank_of_canada` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The series list is large. Fetch it once, keep it in memory, and filter it. `adapters/world_bank/tools.py` caches its country list the same way.
- Values are strings. Convert them.
- The response includes a link to the Bank's terms. Read them and quote the link in the tool description.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
