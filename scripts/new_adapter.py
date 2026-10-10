#!/usr/bin/env python3
"""Scaffold a new adapter: ``python scripts/new_adapter.py NAME [--toolset dev]``.

Copies ``src/keyless_mcp/adapters/_template`` to ``adapters/NAME`` and creates
``m3_tests/adapters/NAME/test_NAME.py`` from ``scripts/templates/test_adapter.py.tmpl``.
Standard library only, so it runs without installing anything.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "src" / "keyless_mcp" / "adapters" / "_template"
TEST_TEMPLATE = ROOT / "scripts" / "templates" / "test_adapter.py.tmpl"
TOOLSETS = ("science", "dev", "geo", "news", "finance", "reference", "fun")
NAME_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def fail(message: str) -> None:
    sys.exit(f"new_adapter: {message}")


def fill(text: str, name: str, toolset: str) -> str:
    title = name.replace("_", " ").title()
    return (
        text.replace("ADAPTER_NAME", name)
        .replace("ADAPTER_TITLE", title)
        .replace("ADAPTER_TOOLSET", toolset)
    )


def scaffold(name: str, toolset: str, root: Path = ROOT) -> tuple[Path, Path]:
    adapter_dir = root / "src" / "keyless_mcp" / "adapters" / name
    test_dir = root / "m3_tests" / "adapters" / name
    if adapter_dir.exists() or test_dir.exists():
        fail(
            f"adapter {name!r} already exists ({adapter_dir if adapter_dir.exists() else test_dir})"
        )
    adapter_dir.mkdir(parents=True)
    for source in TEMPLATE.iterdir():
        if source.is_file():
            (adapter_dir / source.name).write_text(
                fill(source.read_text(encoding="utf-8"), name, toolset), encoding="utf-8"
            )
    (test_dir / "cassettes").mkdir(parents=True)
    (test_dir / "__init__.py").touch()
    test_file = test_dir / f"test_{name}.py"
    test_file.write_text(
        fill(TEST_TEMPLATE.read_text(encoding="utf-8"), name, toolset), encoding="utf-8"
    )
    return adapter_dir, test_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a new keyless-mcp adapter.")
    parser.add_argument("name", help="adapter name: lowercase snake_case, e.g. open_meteo")
    parser.add_argument("--toolset", default="dev", help=f"one of: {', '.join(TOOLSETS)}")
    args = parser.parse_args()
    if not NAME_RE.match(args.name):
        fail(f"invalid name {args.name!r}: use lowercase snake_case such as 'open_meteo'")
    if args.toolset not in TOOLSETS:
        fail(f"invalid toolset {args.toolset!r}: choose one of {', '.join(TOOLSETS)}")
    adapter_dir, test_file = scaffold(args.name, args.toolset)

    def rel(path: Path) -> Path:
        return path.relative_to(ROOT)

    print(f"Created {rel(adapter_dir)}/ and {rel(test_file)}\n")
    print("Next steps:")
    print(
        f"  1. Edit {rel(adapter_dir)}/adapter.yaml (description, base_url, docs_url, rate limit)."
    )
    print(f"  2. Replace the example tool in {rel(adapter_dir)}/tools.py with real ones.")
    print(f"  3. Fill in the TODOs in {rel(test_file)}.")
    print(f"  4. make record ADAPTER={args.name}   # record cassettes from the real API")
    print("  5. make test && make lint")
    print("Contract: docs/adapter-contract.md")


if __name__ == "__main__":
    main()
