---
title: "Add a deps.dev adapter for package versions, licenses and dependencies"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:dev"]
---

deps.dev, from Google, covers npm, PyPI, Go, Maven, Cargo and NuGet in one API. Where the existing adapters each cover one registry, this one answers "what license is this version, and what does it depend on?" across all of them.

## API

- Docs: https://docs.deps.dev/api/v3/
- Base URL: `https://api.deps.dev/v3`
- It works without a key, token or account.
- Suggested adapter name: `deps_dev`, in the `dev` toolset.

## Proposed tools

### `deps_dev_get_version(system: str, name: str, version: str)`

Get one package version: publish date, licenses, whether it is deprecated, advisory ids and links.

### `deps_dev_get_package(system: str, name: str)`

List a package's most recent versions and mark the default one.

### `deps_dev_get_dependencies(system: str, name: str, version: str)`

List the resolved dependency graph of a version, with each node's relation (self, direct or indirect).

## Example

```text
GET https://api.deps.dev/v3/systems/npm/packages/react/versions/18.2.0
```

Fields worth returning: A version has `versionKey`, `publishedAt`, `isDefault`, `isDeprecated`, `licenses`, `advisoryKeys`, `links[]` and `relatedProjects`. The `:dependencies` call returns `nodes[]` with `versionKey` and `relation`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=deps_dev TOOLSET=dev`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/systems/npm/packages/zzznotreal-pkg-1234` returns a 404 with the text `package not found`.
- [ ] `make record ADAPTER=deps_dev` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Scoped npm names must be encoded: `@types/node` becomes `%40types%2Fnode`. The API accepted that form when this issue was written.
- The package endpoint for `react` is about 580 KB and lists versions oldest first. Return only the last few.
- The dependency call is addressed as `.../versions/18.2.0:dependencies`. Check that the shared client keeps the colon intact in a cassette.
- Accept `system` case-insensitively and validate it against the list in the docs.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
