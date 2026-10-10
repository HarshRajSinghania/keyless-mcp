#!/usr/bin/env python3
"""Check that the release metadata agrees with itself (stdlib only, no network).

    python scripts/check_release.py              # CI: consistency checks
    python scripts/check_release.py --tag v0.1.0 # release: also the tag, README and readme field

Always checked: ``pyproject.toml`` version equals ``server.json`` version, every ``packages[]``
version, and the tag of the OCI image identifier; the PyPI identifier is the project name; the
OCI image lives under ghcr.io/sineframe. With ``--tag`` (the release workflow) it also requires
the git tag to be ``v<version>``, ``pyproject.toml`` to declare ``readme``, and that README to
contain ``mcp-name: <server.json name>``: the MCP Registry verifies a PyPI package by finding
that string in the package description, so a missing marker would fail the publish after PyPI
already has the release.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def problems_for(tag: str | None) -> list[str]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    version = project["version"]
    found: list[str] = []

    if server.get("version") != version:
        found.append(f"server.json version {server.get('version')!r} != pyproject {version!r}")
    for package in server.get("packages", []):
        kind, identifier = package.get("registryType"), package.get("identifier", "")
        if kind == "pypi":
            if identifier != project["name"]:
                found.append(f"server.json pypi identifier {identifier!r} != {project['name']!r}")
            if package.get("version") != version:
                found.append(f"server.json pypi version {package.get('version')!r} != {version!r}")
        elif kind == "oci":
            image, _, image_tag = identifier.rpartition(":")
            if not image.startswith("ghcr.io/sineframe/"):
                found.append(f"server.json oci image {identifier!r} not under ghcr.io/sineframe/")
            if image_tag != version:
                found.append(f"server.json oci tag {image_tag!r} != version {version!r}")

    if tag is not None:
        if tag != f"v{version}":
            found.append(f"git tag {tag!r} must be v{version} (pyproject version)")
        readme = project.get("readme")
        marker = f"mcp-name: {server.get('name')}"
        if not readme:
            found.append("pyproject.toml has no `readme`, so PyPI has no description to verify")
        else:
            readme_path = ROOT / (readme if isinstance(readme, str) else readme["file"])
            readme_text = readme_path.read_text(encoding="utf-8")
            if marker not in readme_text:
                found.append(f"README is missing `<!-- {marker} -->` (needed by the MCP Registry)")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Check release metadata consistency.")
    parser.add_argument("--tag", help="the git tag being released, for example v0.1.0")
    args = parser.parse_args()
    try:
        found = problems_for(args.tag)
    except (OSError, KeyError, ValueError) as exc:
        found = [f"cannot read release metadata: {exc!r}"]
    if found:
        print("release metadata problems:")
        for item in found:
            print(f"  - {item}")
        return 1
    print("release metadata is consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
