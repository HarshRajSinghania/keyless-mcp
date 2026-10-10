---
title: "Add a DEV Community adapter for articles"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:news"]
---

DEV is a community blog platform with articles on programming, tooling and careers. Its read-only API needs no key, and an agent can use it to find write-ups on a technology or to read one.

## API

- Docs: https://developers.forem.com/api
- Base URL: `https://dev.to/api`
- It works without a key, token or account.
- Suggested adapter name: `devto`, in the `news` toolset.

## Proposed tools

### `devto_list_articles(tag: str | None = None, username: str | None = None, per_page: int = 5, page: int = 1)`

List recent articles, optionally for one tag or author. Returns id, title, description, URL, author, publish date, reaction and comment counts.

### `devto_get_article(article_id: int)`

Get one article by id, with its body text truncated to a readable length.

## Example

```text
GET https://dev.to/api/articles?per_page=2&tag=mcp
```

Fields worth returning: Each article has `id`, `title`, `description`, `url`, `published_timestamp`, `comments_count`, `public_reactions_count`, `readable_publish_date` and `language`. The single-article endpoint adds `body_markdown` and `body_html`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=devto TOOLSET=news`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/articles/1` returns a 404 with `{"error":"not found","status":404}`.
- [ ] `make record ADAPTER=devto` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The docs describe an API version selected by an `Accept` header. The shared client cannot send custom headers, so use the default version and check that it returns what you need.
- Use `truncate` on the body. Articles can be very long.
- Content belongs to its authors. Return the link with every result.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
