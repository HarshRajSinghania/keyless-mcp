---
title: "Add a US Census Geocoder adapter for addresses and geographies"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:geo"]
---

The Census Bureau's geocoder turns a US street address into coordinates, and a coordinate into the state, county and census tract it falls in. That second part is hard to get from other free geocoders.

## API

- Docs: https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html
- Base URL: `https://geocoding.geo.census.gov/geocoder`
- It works without a key, token or account.
- Suggested adapter name: `us_census_geocoder`, in the `geo` toolset.

## Proposed tools

### `us_census_geocoder_geocode_address(address: str)`

Geocode a one-line US address. Returns the matched address, latitude, longitude and the matched TIGER line id.

### `us_census_geocoder_geographies_for_point(latitude: float, longitude: float)`

Find the state, county and census tract that contain a US coordinate.

## Example

```text
GET https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address=1600+Pennsylvania+Ave+NW+Washington+DC&benchmark=Public_AR_Current&format=json
```

Fields worth returning: `result.addressMatches[]` with `matchedAddress`, `coordinates` (`x` is longitude, `y` is latitude), `tigerLine` and `addressComponents`. The geographies call returns `result.geographies` with groups such as `States`, with `NAME` and `GEOID` fields.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=us_census_geocoder TOOLSET=geo`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an address that matches nothing (`zzzz nowhere`) returns 200 with an empty `addressMatches` list, which the adapter should report as no match.
- [ ] `make record ADAPTER=us_census_geocoder` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- `benchmark=Public_AR_Current` is required. The geographies call also needs `vintage=Current_Current`.
- In the point query, `x` is longitude and `y` is latitude. It is easy to swap them.
- Geography records carry many fields. Return the name and id of each level only.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
