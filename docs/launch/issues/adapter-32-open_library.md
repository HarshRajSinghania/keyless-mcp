---
title: "Add an Open Library adapter to search books and look up ISBNs"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:reference"]
---

Open Library is a free catalog of books from the Internet Archive. An agent can use it to find a book by title or author, check when a work was first published or look up an ISBN.

## API

- Docs: https://openlibrary.org/developers/api
- Base URL: `https://openlibrary.org`
- It works without a key, token or account.
- Suggested adapter name: `open_library`, in the `reference` toolset.

## Proposed tools

### `open_library_search_books(query: str, limit: int = 5)`

Search books by title, author or keywords. Returns the work key, title, authors, first publish year and number of editions.

### `open_library_get_work(work_id: str)`

Get one work by its id such as `OL45804W`: title, description and subjects.

### `open_library_get_book_by_isbn(isbn: str)`

Look up an edition by ISBN-10 or ISBN-13: title, publishers, publish date and page count.

## Example

```text
GET https://openlibrary.org/search.json?q=the+hobbit&limit=2&fields=key,title,author_name,first_publish_year,edition_count
```

Fields worth returning: Search returns `numFound` and `docs[]` with `key`, `title`, `author_name` (a list), `first_publish_year` and `edition_count`. A work has `title`, `key` and `authors` as keys only, such as `/authors/OL34184A`. The `isbn` field is also available in search.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=open_library TOOLSET=reference`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/works/OL0W.json` returns a 404 with `{"error": "notfound", "key": "/works/OL0W"}`.
- [ ] `make record ADAPTER=open_library` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The `fields` parameter keeps search results small.
- A work lists authors only by key. Either leave the names out for the work lookup or make one extra request, and say which in the description.
- Open Library has API usage guidelines about identifying yourself and request rates. Read them.
- Descriptions can be a string or an object with a `value`. Handle both.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
