---
title: "Add an xkcd adapter for comic lookups"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:fun"]
---

xkcd publishes a small JSON file for every comic. An agent can use it to find the latest comic, fetch one by number, or pick a random one and explain the joke from the alt text.

## API

- Docs: https://xkcd.com/json.html
- Base URL: `https://xkcd.com`
- It works without a key, token or account.
- Suggested adapter name: `xkcd`, in the `fun` toolset.

## Proposed tools

### `xkcd_get_comic(number: int | None = None)`

Get a comic by number, or the latest one if no number is given. Returns number, title, alt text, image URL, date and a link to the page.

### `xkcd_get_random_comic()`

Get a random comic. The API has no random endpoint, so read the latest number first and pick one up to it.

## Example

```text
GET https://xkcd.com/info.0.json
```

Fields worth returning: `num`, `title`, `safe_title`, `alt`, `img`, `year`, `month`, `day`, `link`, `news` and `transcript` (often empty).

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=xkcd TOOLSET=fun`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/999999/info.0.json` returns a 404 with an HTML page. Comic number 404 does not exist either, which is the joke.
- [ ] `make record ADAPTER=xkcd` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Build the date from `year`, `month` and `day`, which are strings.
- Return the image URL and do not copy images. The comics are published under CC BY-NC 2.5, so link to them and keep the repository free of copies.
- For the random tool, make the random choice easy to test, for example by injecting the chooser.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
