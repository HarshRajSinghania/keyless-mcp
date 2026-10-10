---
title: "Add a Sunrise-Sunset adapter for sun times at a location"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:geo"]
---

Sunrise, sunset and twilight times depend on place and date, and models are poor at computing them. This single-tool adapter gives an agent the actual times for any latitude and longitude.

## API

- Docs: https://sunrise-sunset.org/api
- Base URL: `https://api.sunrise-sunset.org`
- It works without a key, token or account.
- Suggested adapter name: `sunrise_sunset`, in the `geo` toolset.

## Proposed tools

### `sunrise_sunset_get_times(latitude: float, longitude: float, date: str = "today")`

Get sunrise, sunset, solar noon, day length and civil, nautical and astronomical twilight times for a place and date, in UTC.

## Example

```text
GET https://api.sunrise-sunset.org/json?lat=36.72&lng=-4.42&formatted=0
```

Fields worth returning: `status` and `results` with `sunrise`, `sunset`, `solar_noon`, `day_length` (seconds when `formatted=0`), `civil_twilight_begin`, `civil_twilight_end`, `nautical_twilight_begin`, `nautical_twilight_end`, `astronomical_twilight_begin` and `astronomical_twilight_end`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=sunrise_sunset TOOLSET=geo`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a latitude of 999 should raise `InvalidInput`. The API itself accepted `lat=999` and answered 200 with numbers.
- [ ] `make record ADAPTER=sunrise_sunset` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Validate latitude (-90 to 90) and longitude (-180 to 180) yourself, because the API does not.
- Always send `formatted=0`. Without it times come back as local-looking strings like `1:44:26 AM`, which are ambiguous.
- Check `status` in the body. The docs list values other than `OK`.
- The API has a `tzid` parameter. Decide whether to expose it, and say in the tool description that times are UTC if you do not.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
