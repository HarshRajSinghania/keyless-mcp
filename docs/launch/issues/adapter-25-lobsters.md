---
title: "Add a Lobsters adapter for programming news"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:news"]
---

Lobsters is a smaller, invite-only link aggregator for programming, with tagged stories and active discussion. Its public JSON feeds need no key, and they make a good second opinion next to Hacker News.

## API

- Docs: https://lobste.rs/about
- Base URL: `https://lobste.rs`
- It works without a key, token or account.
- Suggested adapter name: `lobsters`, in the `news` toolset.

## Proposed tools

### `lobsters_list_stories(sort: str = "hottest", page: int = 1)`

List stories from the `hottest` or `newest` feed. Returns title, URL, score, comment count, tags, submitter and the discussion link.

### `lobsters_stories_by_tag(tag: str, page: int = 1)`

List recent stories with one tag, such as `python` or `security`.

## Example

```text
GET https://lobste.rs/hottest.json
```

Fields worth returning: A list of stories with `short_id`, `created_at`, `title`, `url`, `score`, `comment_count`, `tags`, `submitter_user`, `short_id_url` and `comments_url`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=lobsters TOOLSET=news`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an unknown tag (`/t/zzznotatag.json`) returns a 404 with an HTML page.
- [ ] `make record ADAPTER=lobsters` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- A page holds 25 stories. Return at most the first N the caller asks for.
- Text posts have an empty `url`. Fall back to the discussion link.
- `submitter_user` is a plain username string at the time of writing. Write the test against what the API returns when you record.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
