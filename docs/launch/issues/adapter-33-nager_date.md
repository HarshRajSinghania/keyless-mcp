---
title: "Add a Nager.Date adapter for public holidays"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:reference"]
---

Nager.Date lists public holidays for around a hundred countries. "When is the next bank holiday in Germany?" depends on today's date and on the country, which makes it a good question to hand to a tool.

## API

- Docs: https://date.nager.at/Api
- Base URL: `https://date.nager.at/api/v3`
- It works without a key, token or account.
- Suggested adapter name: `nager_date`, in the `reference` toolset.

## Proposed tools

### `nager_date_public_holidays(country_code: str, year: int)`

List a country's public holidays for a year, with the local and English names and whether each applies nationwide.

### `nager_date_next_holidays(country_code: str)`

List the next upcoming public holidays in a country.

### `nager_date_list_countries()`

List the supported countries and their two-letter codes.

## Example

```text
GET https://date.nager.at/api/v3/PublicHolidays/2026/DE
```

Fields worth returning: A list of holidays with `date`, `localName`, `name`, `countryCode`, `fixed`, `global`, `counties` (null or a list of regions) and `types` (such as `Public` or `Bank`).

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=nager_date TOOLSET=reference`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/PublicHolidays/2026/ZZ` returns a 404 with `Unknown country code`.
- [ ] `make record ADAPTER=nager_date` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- When `global` is false the holiday applies only to the regions in `counties`. Keep both fields so the agent does not claim a regional day is national.
- Validate the year range against the docs.
- The countries list is short and stable. Cache it for the life of the process.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
