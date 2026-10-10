---
title: "Add a US Treasury FiscalData adapter for debt and exchange rates"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:finance"]
---

The US Treasury publishes open fiscal data through one API. Two datasets suit an agent well: the total public debt, updated daily, and the exchange rates the Treasury uses for reporting.

## API

- Docs: https://fiscaldata.treasury.gov/api-documentation/
- Base URL: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service`
- It works without a key, token or account.
- Suggested adapter name: `fiscaldata`, in the `finance` toolset.

## Proposed tools

### `fiscaldata_get_debt_to_penny(limit: int = 1)`

Get the most recent daily totals of US public debt: debt held by the public, intragovernmental holdings and the total, in dollars.

### `fiscaldata_get_exchange_rates(country: str | None = None, limit: int = 5)`

Get the Treasury's reporting exchange rates, newest first, optionally for one country.

## Example

```text
GET https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?page[size]=1&sort=-record_date
```

Fields worth returning: `data[]` and `meta`. Debt rows have `record_date`, `debt_held_public_amt`, `intragov_hold_amt` and `tot_pub_debt_out_amt`. Exchange rate rows (`/v1/accounting/od/rates_of_exchange`) have `record_date`, `country`, `currency`, `country_currency_desc`, `exchange_rate` and `effective_date`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=fiscaldata TOOLSET=finance`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a `limit` of 0 or 1000 should raise `InvalidInput`. For an unknown country, the API returns an empty `data` list, which the tool should report as no results.
- [ ] `make record ADAPTER=fiscaldata` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Every value arrives as a string, including the amounts. Convert numbers, and keep large debt totals as integers.
- Filters look like `filter=country:eq:Canada`, and sorting looks like `sort=-record_date`.
- The datasets are documented in a catalog. Read the field definitions before you name your result keys.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
