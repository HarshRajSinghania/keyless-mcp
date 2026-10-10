---
title: "Add a Zippopotam.us adapter for postal codes worldwide"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:geo"]
---

Zippopotam.us maps a postal code to place names and coordinates in dozens of countries, and a place back to its postal codes. It is a quick way for an agent to turn "90210" or "SW1A" into a city and a latitude and longitude.

## API

- Docs: https://zippopotam.us/
- Base URL: `https://api.zippopotam.us`
- It works without a key, token or account.
- Suggested adapter name: `zippopotam`, in the `geo` toolset.

## Proposed tools

### `zippopotam_lookup_postcode(country_code: str, postcode: str)`

Look up a postal code in a country (two-letter code such as `us`, `gb`, `de`). Returns the places, state or region and coordinates.

### `zippopotam_lookup_place(country_code: str, state: str, place: str)`

Find the postal codes of a place, for example `us`, `ma`, `belmont`.

## Example

```text
GET https://api.zippopotam.us/us/90210
```

Fields worth returning: `country`, `country abbreviation`, `post code` and `places[]` with `place name`, `longitude`, `latitude`, `state` and `state abbreviation`. Several keys contain spaces.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=zippopotam TOOLSET=geo`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an unknown code (`/us/00000`) returns a 404 with the body `{}`.
- [ ] `make record ADAPTER=zippopotam` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Coordinates are strings. Convert them.
- Not every country is supported. Check the docs for the list and say in the tool description that coverage varies.
- The place lookup (`/us/ma/belmont`) returns a `places` list in which each entry is a postal code with its own fields. Record it and write the test against what comes back.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
