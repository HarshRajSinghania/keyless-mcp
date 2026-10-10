---
title: "Add a Eurostat adapter for EU inflation figures"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:finance"]
---

Eurostat publishes official EU statistics through an open API. Starting with one dataset keeps this small: the harmonised inflation rate (HICP) by country, a figure agents are often asked about and often get wrong.

## API

- Docs: https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started
- Base URL: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0`
- It works without a key, token or account.
- Suggested adapter name: `eurostat`, in the `finance` toolset.

## Proposed tools

### `eurostat_get_inflation(country: str = "DE", months: int = 6)`

Get the annual inflation rate (HICP, all items) for a country, for the latest N months, as a list of `period` and `rate_percent`.

## Example

```text
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=DE&coicop=CP00&unit=RCH_A&lastTimePeriod=3&format=JSON&lang=EN
```

Fields worth returning: A JSON-stat document: `label`, `id`, `size`, `value` (an object keyed by position, such as `{"0": 2.3, "1": 2.6}`), and `dimension.time.category.index` (an object of period to position, such as `{"2025-10": 0}`).

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=eurostat TOOLSET=finance`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an unknown dataset code returns a 404 with an `error` list, and a country that is not an EU member should raise `InvalidInput`.
- [ ] `make record ADAPTER=eurostat` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- To read a value for a period, look up the period's position in `dimension.time.category.index` and then use it as the key in `value`.
- Positions with no data are missing from `value`, so a period can exist without a number.
- Validate `country` against the two-letter geo codes in the docs, and cap `months`.
- A follow-up issue can add other datasets. Keep the helper that reads JSON-stat reusable.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
