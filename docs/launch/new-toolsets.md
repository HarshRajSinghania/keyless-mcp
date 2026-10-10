# New toolsets for the issue backlog

The adapter issues in `docs/launch/issues/` use three toolsets that the code does not know yet:
`finance`, `reference` and `fun`. Thirteen of the 40 adapter issues need one of them. Add them
before running `docs/launch/create_issues.sh`. The script refuses to create issues while any
issue names a toolset that is missing from `TOOLSETS`, because a contributor could not scaffold
that adapter.

| Toolset | One-line description | Issues |
|---|---|---|
| `finance` | Money and economic data: exchange rates, public finance, inflation. | frankfurter, fiscaldata, bank_of_canada, eurostat |
| `reference` | Looking things up: books, holidays, words, entities, web archives. | open_library, nager_date, datamuse, wikidata, wayback_cdx |
| `fun` | Games, trivia and entertainment. | pokeapi, open_trivia_db, xkcd, tvmaze |

## What to change

The docs task changed none of these. Each place below lists the allowed toolsets:

- `src/keyless_mcp/core/adapters.py`: the `TOOLSETS` tuple. Everything else reads it.
- `scripts/new_adapter.py`: its own `TOOLSETS` tuple, which `make new-adapter` validates against.
- `scripts/gen_adapters_md.py`: `TOOLSET_BLURBS`, the sentence printed under each toolset heading in `ADAPTERS.md`. Add the one-line descriptions above, then run `make adapters-md`. Check how it handles a toolset that has no adapters yet.
- `Makefile`: the usage text of the `new-adapter` target.
- `docs/adapter-contract.md`: the `toolset` row of the `adapter.yaml` table.
- `server.json`: the `KEYLESS_MCP_TOOLSETS` description appears twice.
- `.env.example`: the comment above `KEYLESS_MCP_TOOLSETS`.
- `README.md`: the toolset table and the list in "What it is".
- `.github/ISSUE_TEMPLATE/new-adapter.yml`: the toolset dropdown.
- `m3_tests/core/test_toolsets.py`: the parametrized list of toolsets and the error-message pattern that spells out `science, dev, geo, news`.

Then run `make test`, `make lint` and `uv run python scripts/gen_adapters_md.py --check`.

## If you would rather not add them

Move each adapter into `science`, `dev`, `geo` or `news` instead. Edit the `toolset` field in
`docs/launch/issues/adapter-*.md` (the label, the "Suggested adapter name" line and the
`make new-adapter` command in the checklist). The script's toolset check passes once no
issue mentions an unknown toolset.
