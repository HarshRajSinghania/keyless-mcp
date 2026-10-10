---
title: "Add a Wikidata adapter to search entities and read their facts"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:reference"]
---

Wikidata is the structured database behind Wikipedia. The `wikipedia` adapter returns article text, and this one returns ids and facts, which is what an agent needs to link two systems or check a date of birth.

## API

- Docs: https://www.wikidata.org/wiki/Wikidata:Data_access
- Base URL: `https://www.wikidata.org/w/api.php`
- It works without a key, token or account.
- Suggested adapter name: `wikidata`, in the `reference` toolset.

## Proposed tools

### `wikidata_search_entities(query: str, language: str = "en", limit: int = 5)`

Search items by label. Returns the Q-id, label, description and URL of each match.

### `wikidata_get_entity(entity_id: str, language: str = "en")`

Get one item by Q-id with its label, description and link to the matching Wikipedia article.

## Example

```text
GET https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Douglas+Adams&language=en&format=json&limit=2
```

Fields worth returning: Search returns `search[]` with `id`, `label`, `description`, `concepturi`, `url` and `match`. An entity lookup (`action=wbgetentities&ids=Q42&props=labels|descriptions|sitelinks`) returns `entities.Q42` with `descriptions.en.value` and `sitelinks.enwiki.title`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=wikidata TOOLSET=reference`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an unknown id (`ids=Qzzz`) returns HTTP 200 with an `error` object whose `code` is `no-such-entity`, so the adapter has to check for it.
- [ ] `make record ADAPTER=wikidata` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Labels came back empty for `Q42` with `languages=en`, because many labels now sit under the `mul` language. Adding `languagefallback=1` returned the label. Test the lookup you write.
- Do not return the full `claims` object, which is enormous. If you add statements, pick a few by property id and keep the list short.
- Wikimedia asks clients to identify themselves in the User-Agent, which the shared client does.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
