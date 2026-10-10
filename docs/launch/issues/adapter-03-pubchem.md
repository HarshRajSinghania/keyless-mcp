---
title: "Add a PubChem adapter to look up chemical compounds by name"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:science"]
---

PubChem is the NIH's open chemistry database. Given a name like aspirin or caffeine, an agent can get a formula, molecular weight and structure string from it instead of recalling them from memory, which is where models make quiet mistakes.

## API

- Docs: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
- Base URL: `https://pubchem.ncbi.nlm.nih.gov/rest/pug`
- It works without a key, token or account.
- Suggested adapter name: `pubchem`, in the `science` toolset.

## Proposed tools

### `pubchem_get_compound(name: str)`

Look up a compound by name. Returns its PubChem CID, molecular formula, molecular weight, IUPAC name, SMILES string and a link to its PubChem page.

### `pubchem_get_synonyms(name: str, limit: int = 10)`

List other names and registry numbers (such as the CAS number) for a compound.

## Example

```text
GET https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/property/MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES/JSON
```

Fields worth returning: `PropertyTable.Properties[0]` with `CID`, `MolecularFormula`, `MolecularWeight`, `IUPACName` and a SMILES field. The synonyms call returns `InformationList.Information[0].Synonym`, a list of strings.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=pubchem TOOLSET=science`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: an unknown name returns a 404 whose body has `Fault.Code` set to `PUGREST.NotFound` and the message `No CID found`.
- [ ] `make record ADAPTER=pubchem` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The request above asked for `CanonicalSMILES`, but the response key was `ConnectivitySMILES`. Print the real response before you map field names.
- The synonym list for common compounds is long. Cap it with `limit`.
- PubChem has a usage policy that limits request rates. Read it and put your `rate_limit_per_minute` under it.
- Names go into the URL path, so they need encoding.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
