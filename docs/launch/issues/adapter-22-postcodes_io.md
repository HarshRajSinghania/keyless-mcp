---
title: "Add a Postcodes.io adapter for UK postcodes"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:geo"]
---

Postcodes.io serves open UK postcode data: coordinates, region, local authority and more. It suits questions about a UK postcode and the reverse, finding the postcode nearest a point.

## API

- Docs: https://postcodes.io/docs
- Base URL: `https://api.postcodes.io`
- It works without a key, token or account.
- Suggested adapter name: `postcodes_io`, in the `geo` toolset.

## Proposed tools

### `postcodes_io_lookup(postcode: str)`

Look up a UK postcode. Returns coordinates, country, region, district and constituency-style area fields.

### `postcodes_io_nearest(latitude: float, longitude: float, limit: int = 3)`

Find the postcodes nearest a coordinate in the UK.

## Example

```text
GET https://api.postcodes.io/postcodes/SW1A2AA
```

Fields worth returning: `status` and `result` with `postcode`, `quality`, `country`, `region`, `longitude`, `latitude`, `european_electoral_region` and several area codes. The nearest-postcode call returns `result` as a list.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=postcodes_io TOOLSET=geo`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: `/postcodes/ZZ99ZZ` returns a 404 with `{"status":404,"error":"Postcode not found"}`.
- [ ] `make record ADAPTER=postcodes_io` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- UK only. Say so in the tool descriptions.
- Strip spaces and uppercase the postcode before you build the URL, so `sw1a 2aa` and `SW1A2AA` share a cassette.
- The result has many fields. Return a short, useful subset.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
