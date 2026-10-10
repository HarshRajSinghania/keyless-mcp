# DEV post draft

Draft for the DEV Open-Source AI Challenge entries (Week 3 starts Oct 19, Week 4 starts Oct 26). The prompts are published when each week opens, so read the prompt first and adjust the opening and the "why it fits" paragraph. Lines in square brackets are for you to fill in with your own words or to delete. Nothing here is posted anywhere.

Suggested title: keyless-mcp: one MCP server for public APIs that need no key

Suggested tags: `mcp`, `opensource`, `ai`, `python` (add the challenge tag from the official prompt page)

---

## What I built

keyless-mcp is an MCP server that gives an agent 16 tools over free public APIs. It covers arXiv, Wikipedia, PyPI, npm, OSV vulnerabilities, Open-Meteo weather, World Bank country data and Hacker News. None of them needs an API key or an account, so setup is one line in your MCP client:

```sh
claude mcp add keyless -- uvx keyless-mcp
```

Configs for Claude Desktop, Cursor, VS Code and Codex are in the README. The code is Apache-2.0 and the protocol is open, so it works with any client that speaks MCP.

Here is what a call looks like. Ask whether jinja2 2.4.1 has known vulnerabilities and the agent should call `osv_query_package`, which returned 18 advisories when I tried it on 2026-10-11, including a sandbox escape (GHSA-462w-v97r-4m45) fixed in 2.10.1. A model tends to answer that kind of question from memory unless it has a tool.

[Optional: one or two sentences in your own words on why you wanted keyless tools.]

## Why no keys

A server that needs a token before it does anything is a hurdle for the person trying it, and for the person running it in CI. Public APIs without keys are plentiful, but each one has its own quirks: odd pagination, errors that arrive with a 200 status, field names that differ from the docs. Each adapter handles those so the agent gets a small, consistent result and a readable error when the upstream fails.

You can also turn on only the toolsets you want. `--toolsets dev,geo` serves the package registries, the vulnerability lookup, weather and country data, and nothing else. Fewer tools means fewer choices for the agent to get wrong.

## How it is tested

I tested every tool with [M3](https://github.com/sineframe/m3), a testing tool for MCP servers and agents. There are two layers.

The first runs on every pull request and needs no network. M3 starts the real server over stdio, calls each tool through an MCP client, and the server answers from recorded HTTP responses. That is 195 tests, and a pull request from a fork runs them too, with no secrets involved.

The second layer asks a real agent. Each prompt is a plain question that never names a tool, such as "Are there known security vulnerabilities in version 2.4.1 of the PyPI package jinja2?". The test checks which tool the agent called and whether the call succeeded. In the latest run, Codex picked the right tool on 10 of 10 prompts. That was one trial per prompt, on one day, with one model, so I treat it as a smoke check and not as a measurement. The nightly job repeats it with three trials. [Add those numbers if you have a few runs by the time you post.]

If you build MCP servers, this setup may be worth copying. A tool description is only useful if an agent picks the tool because of it, and the agent lane is how you find out.

## Help wanted

I have opened 40 small issues, each a new adapter for a different keyless API: crossref, usgs_earthquakes, github, nominatim, frankfurter, pokeapi and more. Every one comes with the docs link, proposed tool signatures, an example request and an acceptance checklist. The scaffold is one command:

```sh
git clone https://github.com/sineframe/keyless-mcp && cd keyless-mcp
make setup && make test
make new-adapter NAME=your_api TOOLSET=dev
```

There are also ten larger issues for people who want to work on the core: a response cache, retries with backoff, a health endpoint, Windows CI and a docs site.

One honest note on Hacktoberfest: this year pull requests no longer count toward rewards. What contributors get here is their name in ADAPTERS.md, in the contributors list and in the release notes.

## Links

- Repository: https://github.com/sineframe/keyless-mcp
- Good first issues: https://github.com/sineframe/keyless-mcp/labels/good%20first%20issue
- M3: https://github.com/sineframe/m3

[Optional closing line: what you would like people to do, such as try it, claim an issue, or tell you which API to add next.]
