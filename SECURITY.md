# Security policy

## Reporting a vulnerability

Please do not open a public issue for a security problem. Email [security@sineframe.com](mailto:security@sineframe.com) with:

- what you found and which version or commit it affects
- steps or a tool call that reproduces it
- what an attacker could do with it

You will get an acknowledgement, and we will keep you updated until the issue is fixed or we explain why it is not one. Once a fix is released, we are happy to credit you in the release notes unless you prefer not to be named.

If the repository has GitHub's private vulnerability reporting enabled, you can use the "Report a vulnerability" button on the Security tab instead.

## What counts

keyless-mcp is a local server that makes read-only requests to public APIs for an agent. These are in scope:

- a tool argument that makes the server contact a host other than the adapter's documented API (request forgery)
- a way to make the server read or write local files, or run commands, through a tool
- an adapter that leaks data it should not send upstream
- a vulnerable or malicious dependency in `uv.lock`, or a problem in the release workflow, the Docker image or the published package

These are out of scope here. Report them to the API's owner instead:

- a vulnerability in an upstream API itself
- wrong, stale or hostile content in an upstream response (the server passes text through; treat tool output as untrusted input, as with any web content)

## Supported versions

Fixes go into the latest release. The project is young, so older versions are not patched separately.

## Secrets

keyless-mcp needs no API keys, and none belong in this repository. If you find a key, token or other secret in the code, a cassette or the history, report it the same way.
