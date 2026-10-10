---
title: "Add a Hacker News search adapter (Algolia)"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:news"]
---

The existing `hackernews` adapter reads the live front page and single items. Algolia's index adds full-text search over the whole history of stories and comments, so an agent can find what Hacker News said about a topic years ago.

## API

- Docs: https://hn.algolia.com/api
- Base URL: `https://hn.algolia.com/api/v1`
- It works without a key, token or account.
- Suggested adapter name: `hn_algolia`, in the `news` toolset.

## Proposed tools

### `hn_algolia_search(query: str, tags: str = "story", sort_by_date: bool = False, hits_per_page: int = 10)`

Search Hacker News stories or comments. `tags` filters by type, such as `story`, `comment` or `ask_hn`. Returns title, URL, author, points, comment count, date and the discussion link for each hit.

### `hn_algolia_front_page(hits_per_page: int = 10)`

Return the stories currently on the front page, using the `front_page` tag.

## Example

```text
GET https://hn.algolia.com/api/v1/search?query=mcp&tags=story&hitsPerPage=2
```

Fields worth returning: `nbHits`, `nbPages` and `hits[]` with `objectID`, `title`, `url`, `author`, `points`, `num_comments`, `created_at` and `story_id`. Comment hits also carry `comment_text`. `search_by_date` replaces relevance order with newest first.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=hn_algolia TOOLSET=news`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `hits_per_page=0` or an empty query with no tags should raise `InvalidInput`.
- [ ] `make record ADAPTER=hn_algolia` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Drop `_highlightResult`, which roughly doubles the size of each hit.
- The discussion link is `https://news.ycombinator.com/item?id=<objectID>`.
- Comment text is HTML. Use `strip_html` and `truncate` from `keyless_mcp.core`.
- Look at `adapters/hackernews/tools.py` for how the existing adapter shapes a story, and keep the field names consistent.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
