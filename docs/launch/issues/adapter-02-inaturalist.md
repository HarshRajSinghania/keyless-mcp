---
title: "Add an iNaturalist adapter to look up species and taxa"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:science"]
---

iNaturalist is a large citizen-science record of wildlife sightings, and its taxa database maps common names to scientific names, ranks and lineage. With it, a question like "what is a monarch butterfly, scientifically, and how often is it recorded?" takes one call.

## API

- Docs: https://api.inaturalist.org/v1/docs/
- Base URL: `https://api.inaturalist.org/v1`
- It works without a key, token or account.
- Suggested adapter name: `inaturalist`, in the `science` toolset.

## Proposed tools

### `inaturalist_search_taxa(query: str, per_page: int = 5)`

Search species and other taxa by common or scientific name. Returns the id, scientific name, common name, rank, observation count and Wikipedia link of each match.

### `inaturalist_get_taxon(taxon_id: int)`

Fetch one taxon by its iNaturalist id, with its observation count and Wikipedia link.

## Example

```text
GET https://api.inaturalist.org/v1/taxa?q=monarch&per_page=2
```

Fields worth returning: `total_results`, and in `results[]`: `id`, `name`, `rank`, `preferred_common_name`, `observations_count`, `wikipedia_url` and `matched_term`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=inaturalist TOOLSET=science`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: the id lookup for a taxon that does not exist (`/taxa/999999999`) returns 200 with an empty `results` list, so the adapter has to turn that into an error itself.
- [ ] `make record ADAPTER=inaturalist` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- A search for `monarch` ranks a subtribe of tiger butterflies first, and the monarch butterfly itself lower down. Return several matches with their `rank` so the agent can choose, and look in the docs for a rank filter.
- Each result carries photo objects with their own licenses. Leave photos out.
- Check the recommended-practices section of the API docs and set `rate_limit_per_minute` below it.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
