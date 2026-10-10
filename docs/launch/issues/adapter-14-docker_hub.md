---
title: "Add a Docker Hub adapter for image details and tags"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:dev"]
---

Docker Hub's public API shows how popular an image is, when it was last updated and which tags exist. Agents that write Dockerfiles often pin an image tag from memory, and this gives them a way to check.

## API

- Docs: https://docs.docker.com/reference/api/hub/latest/
- Base URL: `https://hub.docker.com/v2`
- It works without a key, token or account.
- Suggested adapter name: `docker_hub`, in the `dev` toolset.

## Proposed tools

### `docker_hub_get_repository(name: str, namespace: str = "library")`

Get an image repository's description, star count, pull count and last update. Official images use the `library` namespace.

### `docker_hub_list_tags(name: str, namespace: str = "library", page_size: int = 10)`

List the most recently updated tags of an image, with the architectures each one supports.

## Example

```text
GET https://hub.docker.com/v2/repositories/library/nginx
```

Fields worth returning: The repository has `name`, `namespace`, `description`, `star_count`, `pull_count`, `last_updated` and `is_private`. The tags endpoint returns `count`, `next` and `results[]`, where each result has an `images[]` list with `architecture`, `os`, `digest` and `size`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=docker_hub TOOLSET=dev`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/repositories/library/zzznotreal` returns a 404 with `object not found`.
- [ ] `make record ADAPTER=docker_hub` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Each tag lists an image per architecture, which makes the response heavy. Collapse them to a list of architecture names.
- Use only the public, anonymous endpoints. This adapter never logs in.
- Check the Docker Hub rate limit docs and keep `rate_limit_per_minute` low.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
