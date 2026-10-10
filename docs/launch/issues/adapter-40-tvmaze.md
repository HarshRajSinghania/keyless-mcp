---
title: "Add a TVMaze adapter for TV shows and schedules"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:fun"]
---

TVmaze is a free TV database. An agent can look up a show's premiere date, status and rating, or ask what is airing in a country on a given day.

## API

- Docs: https://www.tvmaze.com/api
- Base URL: `https://api.tvmaze.com`
- It works without a key, token or account.
- Suggested adapter name: `tvmaze`, in the `fun` toolset.

## Proposed tools

### `tvmaze_search_shows(query: str, limit: int = 5)`

Search shows by name. Returns id, name, type, language, genres, status, premiere date, rating and official site.

### `tvmaze_get_show(show_id: int)`

Get one show by TVmaze id, with its summary as plain text.

### `tvmaze_get_schedule(country: str = "US", date: str | None = None)`

List the episodes airing in a country on a date (today by default), with show name, season, number and air time.

## Example

```text
GET https://api.tvmaze.com/search/shows?q=severance
```

Fields worth returning: Search returns a list of `{score, show}`. A show has `id`, `url`, `name`, `type`, `language`, `genres`, `status`, `runtime`, `premiered`, `ended`, `officialSite`, `rating.average` and `summary`. The schedule is a list of episodes.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=tvmaze TOOLSET=fun`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/shows/99999999` returns a 404 with `{"name":"Not Found","message":"","code":0,"status":404}`.
- [ ] `make record ADAPTER=tvmaze` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- `summary` is HTML. Use `strip_html`.
- TVmaze documents a rate limit per IP address, and its data comes with a license that asks for attribution. Read the API page, set `rate_limit_per_minute` below the limit, and say in the tool description where the data comes from.
- The schedule for a busy day is long. Cap the number of episodes returned.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
