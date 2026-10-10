---
title: "Add a NASA JPL Small-Body adapter for asteroid close approaches"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:science"]
---

JPL's Solar System Dynamics group publishes asteroid and comet data without a key. An agent can answer "which asteroids pass close to Earth this month?" and "what is known about 433 Eros?" with current numbers.

## API

- Docs: https://ssd-api.jpl.nasa.gov/doc/
- Base URL: `https://ssd-api.jpl.nasa.gov`
- It works without a key, token or account.
- Suggested adapter name: `jpl_small_bodies`, in the `science` toolset.

## Proposed tools

### `jpl_small_bodies_close_approaches(date_min: str, date_max: str, max_distance_au: float = 0.05, limit: int = 10)`

List close approaches of asteroids and comets to Earth in a date window. Returns the designation, approach time, distance in au, relative velocity in km/s and absolute magnitude.

### `jpl_small_bodies_get_object(designation: str)`

Look up one object by number, name or designation (`433`, `Eros`). Returns its full name, whether it is a near-Earth object or potentially hazardous, its orbit class and key orbital elements.

## Example

```text
GET https://ssd-api.jpl.nasa.gov/cad.api?dist-max=0.05&date-min=2026-10-01&date-max=2026-12-31&limit=2
```

Fields worth returning: The close-approach response has `count`, `total`, a `fields` list (`des`, `orbit_id`, `jd`, `cd`, `dist`, `dist_min`, `dist_max`, `v_rel`, `v_inf`, `t_sigma_f`, `h`) and `data`, a list of rows. The object lookup (`/sbdb.api?sstr=433`) has `object.fullname`, `object.neo`, `object.pha`, `object.orbit_class.name` and `orbit.elements`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=jpl_small_bodies TOOLSET=science`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an unknown object (`sstr=zzznotanasteroid`) answers with a JSON message `specified object was not found` and no `object` field, so check for it.
- [ ] `make record ADAPTER=jpl_small_bodies` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- `data` rows are plain lists in the order of `fields`. Zip them into dicts before returning.
- `dist` is in astronomical units and `v_rel` in km/s, according to the API docs. Say so in the result keys or the description.
- Validate the two dates as `YYYY-MM-DD` before calling the API.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
