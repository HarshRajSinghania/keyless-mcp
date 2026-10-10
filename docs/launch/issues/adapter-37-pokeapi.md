---
title: "Add a PokeAPI adapter for Pokemon facts"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:fun"]
---

PokeAPI is a free, well-documented database of Pokemon, and it is a pleasant first API to wrap. It also gives agents exact stats and type matchups to quote.

## API

- Docs: https://pokeapi.co/docs/v2
- Base URL: `https://pokeapi.co/api/v2`
- It works without a key, token or account.
- Suggested adapter name: `pokeapi`, in the `fun` toolset.

## Proposed tools

### `pokeapi_get_pokemon(name_or_id: str)`

Get a Pokemon by name or number: id, types, abilities, base stats, height in metres and weight in kilograms.

### `pokeapi_get_type(name: str)`

Get a type's damage relations: which types it is strong against, weak against and immune to.

## Example

```text
GET https://pokeapi.co/api/v2/pokemon/ditto
```

Fields worth returning: A Pokemon has `id`, `name`, `base_experience`, `height` (decimetres), `weight` (hectograms), `abilities[]`, `types[]`, `stats[]` and `moves[]`. A type has `damage_relations` with lists such as `no_damage_to`, `half_damage_to` and `double_damage_from`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=pokeapi TOOLSET=fun`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/pokemon/notapokemon` returns a 404 with `Not Found`.
- [ ] `make record ADAPTER=pokeapi` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The Pokemon response for `ditto` is about 38 KB, mostly `moves`, `game_indices` and `sprites`. Drop those.
- Convert units: the API's height is in decimetres and weight in hectograms.
- Lowercase the name before the request. The API expects lowercase names.
- PokeAPI asks users to cache responses locally. A small in-memory cache is welcome if you want one.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
