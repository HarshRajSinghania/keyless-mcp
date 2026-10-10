---
title: "Add a ClinicalTrials.gov adapter to search registered studies"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:science"]
---

ClinicalTrials.gov is the US registry of clinical studies. An agent can use it to answer "are there recruiting trials for this condition?" with real study records and NCT ids.

## API

- Docs: https://clinicaltrials.gov/data-api/api
- Base URL: `https://clinicaltrials.gov/api/v2`
- It works without a key, token or account.
- Suggested adapter name: `clinicaltrials`, in the `science` toolset.

## Proposed tools

### `clinicaltrials_search_studies(condition: str | None = None, term: str | None = None, status: str | None = None, page_size: int = 5)`

Search studies by condition or free-text term, optionally filtered by status such as `RECRUITING`. Returns NCT id, title, status and phases for each study.

### `clinicaltrials_get_study(nct_id: str)`

Fetch one study by NCT id with its title, status, phases, brief summary, conditions and sponsor.

## Example

```text
GET https://clinicaltrials.gov/api/v2/studies?query.cond=diabetes&pageSize=2&fields=NCTId,BriefTitle,OverallStatus,Phase
```

Fields worth returning: `studies[]` with nested modules: `protocolSection.identificationModule.nctId` and `briefTitle`, `protocolSection.statusModule.overallStatus`, `protocolSection.designModule.phases`. There is also a `nextPageToken`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=clinicaltrials TOOLSET=science`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a malformed id (`NCT00000000x`) returns a 400 saying the parameter has an incorrect format, and a well-formed unknown id (`NCT99999999`) returns a 404.
- [ ] `make record ADAPTER=clinicaltrials` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- Use the `fields` parameter. Without it a study is a very large nested document.
- Validate the id against `NCT` plus eight digits before you call the API, so the agent gets a clear message.
- Say in the tool descriptions that these are registry records and not medical advice.
- The `status` filter is `filter.overallStatus` in the query string.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
