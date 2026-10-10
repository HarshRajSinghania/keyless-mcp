---
title: "Add a Datamuse adapter for word finding"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:reference"]
---

Datamuse finds words by meaning, sound or spelling: synonyms, rhymes, words that start with a prefix. It helps an agent with writing tasks where the exact word matters.

## API

- Docs: https://www.datamuse.com/api/
- Base URL: `https://api.datamuse.com`
- It works without a key, token or account.
- Suggested adapter name: `datamuse`, in the `reference` toolset.

## Proposed tools

### `datamuse_find_words(meaning_like: str | None = None, sounds_like: str | None = None, spelled_like: str | None = None, max_results: int = 10)`

Find words that mean something similar, sound similar or match a spelling pattern. At least one constraint is required. In `spelled_like`, `?` matches one letter and `*` matches any run.

### `datamuse_suggest(prefix: str, max_results: int = 5)`

Suggest completions for the start of a word.

## Example

```text
GET https://api.datamuse.com/words?ml=ringing+in+the+ears&max=3
```

Fields worth returning: A list of `{word, score}` objects, with `tags` for some queries. The suggest endpoint (`/sug?s=ser`) returns the same shape.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=datamuse TOOLSET=reference`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a call with no constraint should raise `InvalidInput`. A query with no matches returns an empty list.
- [ ] `make record ADAPTER=datamuse` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Map your friendly parameter names to `ml`, `sl` and `sp`. The docs list more constraints you can add later.
- The API's `max` parameter has an upper limit in the docs. Enforce it on `max_results`.
- Check the docs for the free daily request allowance and set `rate_limit_per_minute` with it in mind.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
