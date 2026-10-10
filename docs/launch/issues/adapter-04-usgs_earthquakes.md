---
title: "Add a USGS Earthquakes adapter for recent and past earthquakes"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:science"]
---

The USGS catalog lists earthquakes worldwide with magnitude, place, time and depth. A language model cannot know what shook this week, so "was there a large earthquake near Japan recently?" needs a tool.

## API

- Docs: https://earthquake.usgs.gov/fdsnws/event/1/
- Base URL: `https://earthquake.usgs.gov/fdsnws/event/1`
- It works without a key, token or account.
- Suggested adapter name: `usgs_earthquakes`, in the `science` toolset.

## Proposed tools

### `usgs_earthquakes_search(min_magnitude: float = 4.5, days: int = 7, limit: int = 10)`

List earthquakes at or above a magnitude in the last N days, newest first. Returns magnitude, place, time, depth, coordinates, tsunami flag and a link to the event page.

### `usgs_earthquakes_get_event(event_id: str)`

Fetch one event by its USGS id, for example `us6000jlqa`.

## Example

```text
GET https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=2&minmagnitude=5&orderby=time
```

Fields worth returning: `metadata.count`, and in `features[]`: `id`, `properties.mag`, `properties.place`, `properties.time`, `properties.url`, `properties.tsunami`, `properties.sig`, `properties.title`, and `geometry.coordinates` as `[longitude, latitude, depth_km]`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=usgs_earthquakes TOOLSET=science`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a bad date such as `starttime=notadate` returns a 400 with the text `Bad starttime value`, and an unknown `eventid` returns a 404.
- [ ] `make record ADAPTER=usgs_earthquakes` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- `properties.time` is milliseconds since the epoch. Convert it to an ISO timestamp. `hackernews/tools.py` has an `iso_time` helper you can copy.
- Send `orderby=time` and always send `limit`. A single query can match a very large number of events.
- The tool takes `days`, but the API wants `starttime`. Work it out from the current UTC time.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
