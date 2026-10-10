# Contributing to keyless-mcp

The most useful contribution is a new adapter: a small wrapper around a free public API that needs no key. You do not need to know MCP internals. The scaffold writes most of the boilerplate, and the tests tell you what is missing.

If something else is on your mind, such as a bug, a docs fix or an idea for the core, open an issue or start a [discussion](https://github.com/sineframe/keyless-mcp/discussions). Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## What you need

Three tools: `git`, `make` and [uv](https://docs.astral.sh/uv/). uv installs Python 3.12 and every dependency for you, so you do not need a Python setup of your own.

```sh
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows, use WSL. The Makefile assumes a Unix shell, and native Windows is not tested yet.

## Five-minute setup

```sh
git clone https://github.com/sineframe/keyless-mcp
cd keyless-mcp
make setup
make test
```

`make setup` creates `.venv`, installs the locked dependencies, and sets up and checks the M3 test tooling. `make test` runs the whole suite offline against recorded responses. It needs no network and no API keys, and takes about 35 seconds. A green run ends with a line like `196 passed`.

Run `make` on its own to list every command:

```text
make setup        Install everything (Python 3.12 venv, dependencies, M3 SDK) and check it works
make test         Run all tests offline (replays cassettes; no network, no API keys)
make test-live    Run the live smoke tests against the real APIs (needs network)
make agent        Real-agent tool-selection tests (costs tokens)
make record       Re-record an adapter's cassettes from the real API: make record ADAPTER=arxiv
make new-adapter  Scaffold an adapter: make new-adapter NAME=open_meteo TOOLSET=geo
make adapters-md  Regenerate ADAPTERS.md from the adapters and docs/results/agent-*-latest.json
make lint         Check code style (ruff check + ruff format --check)
make fmt          Auto-fix lint issues and format the code
make ui           Open the M3 results viewer for saved runs
make run          Start the server on stdio
make tools        List every registered tool with its toolset
```

To try the server itself, `make tools` lists what it serves, and `make run` starts it on stdio.

## Adding an adapter

1. Pick an API. Take one from the [good first issue](https://github.com/sineframe/keyless-mcp/labels/good%20first%20issue) list, or propose your own with the "New adapter" issue form. Comment on the issue to claim it, and link the issue from your pull request.

2. Scaffold it. The name is lowercase snake_case, and the toolset is the one your issue names (`science`, `dev`, `geo`, `news`, `finance`, `reference` or `fun`):

   ```sh
   make new-adapter NAME=open_meteo TOOLSET=geo
   ```

   This creates `src/keyless_mcp/adapters/<name>/` (with `adapter.yaml` and `tools.py`) and `m3_tests/adapters/<name>/test_<name>.py`, then prints the next steps.

3. Describe the API in `adapter.yaml`: title, one-sentence description, base URL, docs URL, the documented rate limit per minute, and your GitHub handle.

4. Write the tools in `tools.py`. Replace the example tool with real ones. Each tool needs a name of the form `<adapter>_<verb>`, a docstring that says what it returns and when to use it, and a description with an example value on every parameter. Agents choose tools from these sentences, so spend time on them. Return a small dict, trim long text with `truncate`, and include source URLs. All requests go through the `http` handle, never `httpx` or `requests`. [docs/adapter-contract.md](docs/adapter-contract.md) has the full rules and a worked example.

5. Write the tests in `m3_tests/adapters/<name>/test_<name>.py`. Replace every TODO. You need a catalog test, a happy path per tool that asserts real content, an error path (bad input, and an unknown id if the API has one), and a `live` smoke test. Take expected values from the API's documentation, not from whatever the server returns.

6. Record the cassettes:

   ```sh
   make record ADAPTER=open_meteo
   ```

   This runs your tests against the real API and saves each request and response as a JSON file in `m3_tests/adapters/<name>/cassettes/`. The old cassettes are replaced only if every test passed, so a failed run cannot leave you with a half-recorded set. Choose queries with short answers so the files stay small, and read them before committing. Request headers are never stored.

7. Check everything:

   ```sh
   make test
   make fmt
   make lint
   make adapters-md
   ```

   `make test` replays the cassettes offline and also runs the catalog contract, which checks your `adapter.yaml`, your descriptions and that you have a test file and at least one cassette. `make fmt` fixes formatting. `make adapters-md` regenerates [ADAPTERS.md](ADAPTERS.md), which you commit with your change. Until you do, `make test` fails with `test_adapters_md_is_up_to_date`, and CI fails the same way. Do not edit ADAPTERS.md by hand.

8. Commit and open a pull request. Subjects follow conventional commits, for example `feat(adapters): add crossref adapter`. The pull request template has a short checklist.

## Reading a test report

M3 runs the real server, calls each tool through an MCP client and records every call. When `make test` ends it prints a line like `M3 feedback: .m3/reports/run-.../feedback.json`. That file lists each test and its outcome.

To see the calls themselves, run:

```sh
make ui
```

It starts a local viewer and prints its address (`UI: http://127.0.0.1:...`). Open it to browse your saved runs and the tool calls in each one. CI uploads the same reports as an `m3-reports` artifact on every pull request, so you can download it and read `feedback.json` when a failure does not reproduce on your machine.

To run one adapter's tests while you work:

```sh
KEYLESS_MCP_HTTP_MODE=replay scripts/m3 test --python .venv/bin/python -- m3_tests/adapters/osv -q
```

If a test fails with `no cassette for GET <url>`, the test made a request nobody recorded. Run `make record ADAPTER=<name>` again after changing a test's arguments.

`make test-live` runs the smoke tests against the real APIs. Use it to check that an upstream still behaves, not as part of a pull request.

The agent tests (`make agent`) check that a real model picks the right tool from a plain-English prompt. They cost model tokens and need credentials, so you can skip them. If you add an adapter and want to add a prompt for it, [docs/agent-testing.md](docs/agent-testing.md) explains how.

## Rules

- One adapter claim at a time. Finish or release one before you claim another, so others can pick up the rest. If you cannot finish, say so on the issue.
- Keyless APIs only. If the API needs a key, a token or an account to work, it does not belong in this repository, even if the key is free.
- Read the API's terms of use and respect them. Some APIs forbid automated use, require attribution or ban certain content. Say what you checked in the pull request.
- Respect rate limits. Put the documented limit in `adapter.yaml`, rounded down. Tests never touch the network, and `make record` should make as few requests as it can.
- No secrets, keys or personal data in code, cassettes or fixtures.
- Keep tool results compact. Agents read every byte, so trim large payloads and cap list lengths.
- Do not change the core (`src/keyless_mcp/core/`) in an adapter pull request unless the issue asks for it. If the core is in your way, open an issue first.

By contributing you agree that your work is licensed under the [Apache License 2.0](LICENSE).

## What happens after you open a pull request

A maintainer replies within two days, usually with a review or a question. CI runs these checks, all offline and with no secrets:

- `ruff check` and `ruff format --check`
- ADAPTERS.md is up to date
- `scripts/check_release.py` (version numbers agree across `pyproject.toml` and `server.json`)
- every M3 test in replay mode, plus `scripts/check_feature_results.py`, which fails if an adapter's tests never drove the server

The same commands run locally as `make lint` and `make test`, so a green local run should mean a green CI run. If CI fails on something you cannot reproduce, say so in the pull request.

Once your adapter merges, you are added to the author column in ADAPTERS.md (from `author` in `adapter.yaml`), to the contributors list in the README, and to the release notes.
