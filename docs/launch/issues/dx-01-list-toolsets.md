---
title: "Improve the --toolsets experience: --list-toolsets and better errors"
labels: ["help wanted", "hacktoberfest", "area:dx"]
---

## Context

`--toolsets dev,geo` works, but a newcomer cannot see what the toolsets contain without reading the README. A typo gives this message and exits with status 1:

```text
keyless-mcp: unknown toolset(s): nope. Valid toolsets: science, dev, geo, news, finance, reference, fun
```

The parsing is in `parse_toolsets` in `src/keyless_mcp/core/adapters.py`, and the flags are in `src/keyless_mcp/__main__.py`. A one-line description of each toolset already exists in `TOOLSET_BLURBS` in `scripts/gen_adapters_md.py`, but only the script can see it.

## Proposed approach

- Add `--list-toolsets`. It prints each toolset with its one-line description, its adapters and the number of tools, then exits. Move the descriptions into `keyless_mcp.core` so the server and `gen_adapters_md.py` share one copy.
- Suggest the nearest name on a typo ("did you mean `dev`?"). `difflib.get_close_matches` is enough.
- Let `--list-tools` say which toolsets are active when a filter is set.
- Accept `all` as an explicit value, so `KEYLESS_MCP_TOOLSETS=all` reads clearly.
- Mention the new flag in `--help` and in the README's "Choosing toolsets" section.

## Acceptance criteria

- [ ] `keyless-mcp --list-toolsets` prints every toolset with a description, adapters and tool count, and exits 0.
- [ ] A typo such as `--toolsets dve` prints a "did you mean `dev`?" hint and exits 1.
- [ ] `--toolsets all` and `KEYLESS_MCP_TOOLSETS=all` serve everything.
- [ ] Tests in `m3_tests/core/test_toolsets.py` cover the three behaviours (its `cli` helper runs the real command).
- [ ] `scripts/gen_adapters_md.py --check` still passes, with the descriptions coming from the shared location.
- [ ] `make test` and `make lint` pass.

## Notes

When new toolsets are added later (the adapter backlog uses `finance`, `reference` and `fun`), this list should pick them up with no extra edits beyond the one definition.

Comment below to claim this.
