---
title: "Add a Packagist adapter for PHP packages"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:dev"]
---

Packagist is the main registry for PHP Composer packages. With it, an agent can check a package's latest version, license and PHP requirement before it suggests `composer require`.

## API

- Docs: https://packagist.org/apidoc
- Base URL: `https://packagist.org`
- It works without a key, token or account.
- Suggested adapter name: `packagist`, in the `dev` toolset.

## Proposed tools

### `packagist_search(query: str, per_page: int = 5)`

Search packages by keyword. Returns name, description, repository URL, download count and favers.

### `packagist_get_package(vendor: str, package: str)`

Get a package's latest version with its license, PHP requirement, release date and the next few versions.

## Example

```text
GET https://packagist.org/search.json?q=monolog&per_page=1
```

Fields worth returning: Search has `total` and `results[]` with `name`, `description`, `url`, `repository`, `downloads` and `favers`. Package metadata comes from `https://repo.packagist.org/p2/monolog/monolog.json`, where `packages['monolog/monolog']` is a list of versions with `version`, `license`, `require` and `time`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=packagist TOOLSET=dev`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `https://repo.packagist.org/p2/zzz/notreal.json` returns a 404 with a short text body.
- [ ] `make record ADAPTER=packagist` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Two hosts are involved: `packagist.org` for search and `repo.packagist.org` for metadata. Put one in `base_url` and use the full URL for the other.
- The metadata for `monolog` is about 85 KB, with 91 versions listed newest first. Return the first few.
- Many version entries repeat fields. The p2 format is documented as minified, so check how it behaves before relying on a field being present.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
