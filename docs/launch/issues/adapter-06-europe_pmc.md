---
title: "Add a Europe PMC adapter to search biomedical literature"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:science"]
---

Europe PMC indexes PubMed, PubMed Central full text and preprints. Medical and life-science questions get better answers when an agent can search the literature and see whether a paper is open access.

## API

- Docs: https://europepmc.org/RestfulWebService
- Base URL: `https://www.ebi.ac.uk/europepmc/webservices/rest`
- It works without a key, token or account.
- Suggested adapter name: `europe_pmc`, in the `science` toolset.

## Proposed tools

### `europe_pmc_search(query: str, page_size: int = 5)`

Search biomedical papers. Returns id, source, PMID, DOI, title, authors, journal, year, publication type, open-access flag and citation count for each hit, plus the total hit count.

### `europe_pmc_get_article(source: str, article_id: str)`

Fetch one article's full record, including its abstract, from a source code such as `MED` and an id such as `25901020`.

## Example

```text
GET https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=crispr&format=json&pageSize=2
```

Fields worth returning: `hitCount`, and in `resultList.result[]`: `id`, `source`, `pmid`, `doi`, `title`, `authorString`, `journalTitle`, `pubYear`, `pubType`, `isOpenAccess` and `citedByCount`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=europe_pmc TOOLSET=science`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a call with `page_size=0` or an empty query should raise `InvalidInput`. A query with no hits returns `hitCount: 0` and an empty list, which is not an error.
- [ ] `make record ADAPTER=europe_pmc` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The search endpoint accepts `EXT_ID:25901020 AND SRC:MED` as a query and `resultType=core` for the full record. That gives you the article lookup with no second endpoint.
- The default `resultType` is `lite`, which has no abstract.
- Use the first page only and leave the `cursorMark` paging out of this first version.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
