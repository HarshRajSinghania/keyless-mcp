---
title: "Add a Frankfurter adapter for currency exchange rates"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:finance"]
---

Frankfurter serves the European Central Bank's daily reference rates, current and historical, with no key. Currency conversion is something models do with stale numbers, so a live source helps.

## API

- Docs: https://frankfurter.dev/
- Base URL: `https://api.frankfurter.dev/v1`
- It works without a key, token or account.
- Suggested adapter name: `frankfurter`, in the `finance` toolset.

## Proposed tools

### `frankfurter_get_rates(base: str = "EUR", symbols: str | None = None, date: str = "latest")`

Get exchange rates for a base currency, optionally limited to some symbols and for a past date.

### `frankfurter_get_time_series(start_date: str, end_date: str, base: str = "EUR", symbols: str | None = None)`

Get daily rates over a date range.

### `frankfurter_list_currencies()`

List the supported currency codes and their names.

## Example

```text
GET https://api.frankfurter.dev/v1/latest?base=EUR&symbols=USD,GBP
```

Fields worth returning: `amount`, `base`, `date` and `rates`. A time series has `start_date`, `end_date` and `rates` keyed by date. `/currencies` is an object of code to name.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=frankfurter TOOLSET=finance`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an unknown base (`base=ZZZ`) returns a 404 with `{"message":"not found"}`.
- [ ] `make record ADAPTER=frankfurter` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Rates exist for working days only. Asking for a Saturday returned the previous Friday's date in `date`, so tell the agent which date the rate is for.
- Validate currency codes as three uppercase letters and dates as `YYYY-MM-DD` before you call.
- Keep time series short. Cap the range.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
