---
title: "Add a Hugging Face Hub adapter to search models and datasets"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:dev"]
---

The Hub hosts most open models and datasets. An agent that can search it can answer "which small summarization models are popular?" with real download counts instead of a remembered list.

## API

- Docs: https://huggingface.co/docs/hub/api
- Base URL: `https://huggingface.co/api`
- It works without a key, token or account.
- Suggested adapter name: `huggingface`, in the `dev` toolset.

## Proposed tools

### `huggingface_search_models(query: str, limit: int = 5)`

Search public models by name. Returns id, task (`pipeline_tag`), library, downloads, likes and creation date.

### `huggingface_get_model(model_id: str)`

Get one model by id such as `google-bert/bert-base-uncased`, with its task, library, tags (capped), downloads and likes.

### `huggingface_search_datasets(query: str, limit: int = 5)`

Search public datasets by name. Returns id, author, downloads, likes and last modified date.

## Example

```text
GET https://huggingface.co/api/models?search=bert&limit=2
```

Fields worth returning: `id`, `downloads`, `likes`, `pipeline_tag`, `library_name`, `tags`, `createdAt`, `trendingScore` and `private`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=huggingface TOOLSET=dev`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a model id that does not exist (`/models/zzz/notreal`) returns HTTP 401 with `Invalid username or password.`, and a search with no matches returns an empty list.
- [ ] `make record ADAPTER=huggingface` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The 401 is misleading. For lookups without a token it means the model does not exist, or it is private or gated. Translate it into a clear `InvalidInput`.
- Model ids contain a slash. Check that the id reaches the API as expected.
- Cap `tags`, which can run to dozens of entries.
- Never accept an access token. Gated models are out of scope.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
