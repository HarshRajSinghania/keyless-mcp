---
title: "Add a GitHub adapter for public repository facts (unauthenticated)"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:dev"]
---

Public GitHub data works without a token, within a limit of 60 requests an hour per IP. That is enough for an agent to answer "how active is this repository?" or "what is the latest release of uv?" The adapter must never ask for a token. If the limit runs out, it should say so plainly.

## API

- Docs: https://docs.github.com/en/rest
- Base URL: `https://api.github.com`
- It works without a key, token or account.
- Suggested adapter name: `github`, in the `dev` toolset.

## Proposed tools

### `github_get_repo(owner: str, repo: str)`

Get a public repository's description, stars, forks, open issue count, main language, license, topics, last push date and URL.

### `github_search_repositories(query: str, per_page: int = 5)`

Search public repositories with GitHub's search syntax, for example `mcp server language:python`.

### `github_get_latest_release(owner: str, repo: str)`

Get a repository's latest release: tag, name, publish date, URL and the first part of its notes.

## Example

```text
GET https://api.github.com/repos/modelcontextprotocol/python-sdk
```

Fields worth returning: `full_name`, `description`, `html_url`, `stargazers_count`, `forks_count`, `open_issues_count`, `language`, `license.spdx_id`, `topics`, `pushed_at`. Search returns `total_count` and `items[]` with the same fields.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=github TOOLSET=dev`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/repos/zzzz/notreal` returns a 404 with `Not Found`, and a repository with no releases (`octocat/Hello-World`) also returns 404 from the latest-release endpoint.
- [ ] `make record ADAPTER=github` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The rate limiter in the shared client spaces calls evenly. It cannot track an hourly budget, so pick a modest `rate_limit_per_minute` and turn a 403 or 429 into a message that mentions the 60-an-hour limit.
- Search has a tighter limit than the rest of the API. Check the rate limit page of the docs.
- Return release notes truncated, since some are very long.
- The shared client cannot send custom headers, and none are needed here.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
