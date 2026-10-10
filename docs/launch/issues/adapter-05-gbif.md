---
title: "Add a GBIF adapter for species names and sightings"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:science"]
---

GBIF pools biodiversity records from museums and observation networks. Two things agents often get wrong are the currently accepted name of a species and where it has actually been recorded, and GBIF answers both.

## API

- Docs: https://techdocs.gbif.org/en/openapi/
- Base URL: `https://api.gbif.org/v1`
- It works without a key, token or account.
- Suggested adapter name: `gbif`, in the `science` toolset.

## Proposed tools

### `gbif_match_species(name: str)`

Match a scientific or common name to GBIF's taxonomic backbone. Returns the key, canonical name, rank, status, match confidence and the kingdom-to-genus lineage.

### `gbif_search_occurrences(scientific_name: str, country: str | None = None, limit: int = 5)`

List recorded sightings of a species, with date, country, coordinates and basis of record, plus the total number of records. `country` is a two-letter ISO code.

## Example

```text
GET https://api.gbif.org/v1/species/match?name=Panthera%20leo
```

Fields worth returning: For the match: `usageKey`, `scientificName`, `canonicalName`, `rank`, `status`, `confidence`, `matchType`, `kingdom`, `phylum`, `class`, `order`, `family`, `genus`. For occurrences: `count`, `endOfRecords` and `results[]`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=gbif TOOLSET=science`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a name with no match (`zzzznotaspecies`) returns HTTP 200 with `matchType` set to `NONE`, so the adapter should raise `InvalidInput` itself.
- [ ] `make record ADAPTER=gbif` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Occurrence records have dozens of fields. Return a handful (key, scientific name, country, latitude, longitude, event date, basis of record) and check the exact field names in a real response.
- Look up the maximum `limit` for the occurrence search in the docs and enforce it.
- Keep the occurrence cassette small by recording a query with `limit=2`.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
