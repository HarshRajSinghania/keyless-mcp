---
title: "Add a Nominatim adapter for address search and reverse geocoding"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:geo"]
---

Nominatim geocodes with OpenStreetMap data. The Open-Meteo adapter can already turn a city name into coordinates, and Nominatim adds street addresses, landmarks and the reverse direction: coordinates to an address.

## API

- Docs: https://nominatim.org/release-docs/latest/api/Overview/
- Base URL: `https://nominatim.openstreetmap.org`
- It works without a key, token or account.
- Suggested adapter name: `nominatim`, in the `geo` toolset.

## Proposed tools

### `nominatim_search(query: str, limit: int = 3, country_codes: str | None = None)`

Find places and addresses by free text. Returns the display name, latitude, longitude, category, type and bounding box of each match. `country_codes` limits results to comma-separated ISO codes.

### `nominatim_reverse(latitude: float, longitude: float)`

Find the address or place at a coordinate.

## Example

```text
GET https://nominatim.openstreetmap.org/search?q=Eiffel+Tower&format=json&limit=1
```

Fields worth returning: A list of places with `place_id`, `lat` and `lon` (both strings), `display_name`, `name`, `class`, `type`, `importance`, `boundingbox` and a `licence` string. Reverse geocoding with `format=jsonv2` returns one object with similar fields.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=nominatim TOOLSET=geo`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a search with no match (`q=zzzzqqqnowhere`) returns an empty list, which the tool should report as no results, and out-of-range coordinates should raise `InvalidInput`.
- [ ] `make record ADAPTER=nominatim` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Nominatim's usage policy for the public server requires an identifying User-Agent, allows at most about one request per second and forbids bulk use. Set `rate_limit_per_minute` accordingly (30 is safe) and read the policy.
- `lat` and `lon` are strings. Convert them to floats.
- The data is ODbL. Include the attribution text in the result.
- Use `format=jsonv2` for reverse lookups, and check how the field names differ from the search response.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
