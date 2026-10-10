"""Adapter discovery, ``adapter.yaml`` validation and tool registration.

An adapter is a subpackage of ``keyless_mcp.adapters`` that has an ``adapter.yaml`` and a
``tools`` module exposing ``register(tools, http)``. Packages starting with ``_`` (the template)
are skipped. See ``docs/adapter-contract.md``.
"""

from __future__ import annotations

import functools
import importlib
import inspect
import logging
import pkgutil
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

import yaml
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

import keyless_mcp.adapters as adapters_pkg

from .errors import AdapterError, UpstreamError
from .http import HttpClient

TOOLSETS = ("science", "dev", "geo", "news")
REQUIRED_FIELDS = (
    "name",
    "title",
    "description",
    "toolset",
    "base_url",
    "docs_url",
    "rate_limit_per_minute",
    "author",
)
NAME_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
PUBLIC_READ_ONLY = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True
)
LOGGER = logging.getLogger("keyless_mcp")
_F = TypeVar("_F", bound=Callable[..., Any])
# AttributeError covers ``None.get(...)`` / ``list.get(...)`` on a response of the wrong type.
_SHAPE_ERRORS = (KeyError, TypeError, IndexError, AttributeError)


@dataclass(frozen=True)
class AdapterSpec:
    """Validated contents of an adapter's ``adapter.yaml``."""

    name: str
    title: str
    description: str
    toolset: str
    base_url: str
    docs_url: str
    rate_limit_per_minute: int
    author: str

    @classmethod
    def from_file(cls, path: Path, *, expected_name: str | None = None) -> AdapterSpec:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise AdapterError(f"{path}: cannot read adapter.yaml ({exc})") from exc
        return cls.from_mapping(data, source=str(path), expected_name=expected_name)

    @classmethod
    def from_mapping(
        cls, data: Any, *, source: str = "adapter.yaml", expected_name: str | None = None
    ) -> AdapterSpec:
        if not isinstance(data, dict):
            raise AdapterError(f"{source}: must be a YAML mapping")
        missing = [f for f in REQUIRED_FIELDS if data.get(f) in (None, "")]
        if missing:
            raise AdapterError(f"{source}: missing required field(s): {', '.join(missing)}")
        unknown = sorted(set(data) - set(REQUIRED_FIELDS))
        if unknown:
            raise AdapterError(f"{source}: unknown field(s): {', '.join(unknown)}")
        for text_field in REQUIRED_FIELDS:
            if text_field != "rate_limit_per_minute" and not isinstance(data[text_field], str):
                raise AdapterError(f"{source}: {text_field} must be a string")
        rate = data["rate_limit_per_minute"]
        if isinstance(rate, bool) or not isinstance(rate, int) or rate <= 0:
            raise AdapterError(f"{source}: rate_limit_per_minute must be a positive integer")
        if not NAME_RE.match(data["name"]):
            raise AdapterError(f"{source}: name {data['name']!r} must be lowercase snake_case")
        if expected_name is not None and data["name"] != expected_name:
            raise AdapterError(
                f"{source}: name {data['name']!r} must match its directory {expected_name!r}"
            )
        if data["toolset"] not in TOOLSETS:
            raise AdapterError(
                f"{source}: toolset {data['toolset']!r} is not one of: {', '.join(TOOLSETS)}"
            )
        for url_field in ("base_url", "docs_url"):
            if not data[url_field].startswith(("http://", "https://")):
                raise AdapterError(f"{source}: {url_field} must be an http(s) URL")
        return cls(**{f: data[f] for f in REQUIRED_FIELDS})


@dataclass(frozen=True)
class LoadedAdapter:
    """An adapter that has registered its tools on a server."""

    spec: AdapterSpec
    tool_names: tuple[str, ...]


def discover_adapters() -> list[AdapterSpec]:
    """All adapters shipped in ``keyless_mcp.adapters``, sorted by name."""
    specs = []
    for module in pkgutil.iter_modules(adapters_pkg.__path__):
        if not module.ispkg or module.name.startswith("_"):
            continue
        directory = Path(adapters_pkg.__path__[0]) / module.name
        yaml_path = directory / "adapter.yaml"
        if yaml_path.is_file():
            specs.append(AdapterSpec.from_file(yaml_path, expected_name=module.name))
    return sorted(specs, key=lambda s: s.name)


def parse_toolsets(value: str | Iterable[str] | None) -> set[str] | None:
    """Normalise ``--toolsets``/``KEYLESS_MCP_TOOLSETS`` input. ``None`` or empty means all."""
    if value is None:
        return None
    items = value.split(",") if isinstance(value, str) else list(value)
    chosen = {item.strip().lower() for item in items if item.strip()}
    if not chosen:
        return None
    unknown = sorted(chosen - set(TOOLSETS))
    if unknown:
        raise ValueError(
            f"unknown toolset(s): {', '.join(unknown)}. Valid toolsets: {', '.join(TOOLSETS)}"
        )
    return chosen


class ToolRegistry:
    """What ``register()`` receives: registers one adapter's tools and enforces naming."""

    def __init__(self, mcp: MCPServer, adapter: str) -> None:
        self._mcp = mcp
        self._adapter = adapter
        self.names: list[str] = []

    def tool(
        self,
        name: str | None = None,
        *,
        title: str | None = None,
        description: str | None = None,
        annotations: ToolAnnotations = PUBLIC_READ_ONLY,
    ) -> Callable[[_F], _F]:
        """Decorator registering a function as an MCP tool named ``<adapter>_<verb>``.

        The tool name defaults to the function name and the description to its docstring. Tools
        are annotated read-only/open-world by default because every adapter wraps a public API.
        """

        def decorator(fn: _F) -> _F:
            tool_name = name or fn.__name__
            if not (tool_name.startswith(f"{self._adapter}_") and NAME_RE.match(tool_name)):
                raise AdapterError(
                    f"adapters/{self._adapter}: tool {tool_name!r} must be snake_case and start "
                    f"with '{self._adapter}_'"
                )
            if not (description or inspect.getdoc(fn)):
                raise AdapterError(f"tool {tool_name!r} needs a description (docstring)")
            if tool_name in self.names:
                raise AdapterError(f"adapters/{self._adapter}: duplicate tool {tool_name!r}")
            self._mcp.add_tool(
                self._guard(fn, tool_name),
                name=tool_name,
                title=title,
                description=description,
                annotations=annotations,
            )
            self.names.append(tool_name)
            return fn

        return decorator

    def _guard(self, fn: _F, tool_name: str) -> Callable[..., Any]:
        """Wrap a tool so a surprise in an upstream response becomes a readable error result.

        Adapters index into parsed JSON (``data["items"][0]["name"]``). When the API changes shape
        that raises ``KeyError``, ``TypeError``, ``IndexError`` or ``AttributeError``, which would
        otherwise reach the agent as an opaque failure. The same exceptions also come from adapter
        bugs, so the message says so and the full traceback is logged to stderr. The wrapper keeps
        the signature and annotations, so the MCP input schema is unchanged.
        """
        adapter = self._adapter

        def unexpected(exc: Exception) -> UpstreamError:
            if isinstance(exc, KeyError):
                detail = f"missing {exc.args[0]!r}" if exc.args else "missing key"
            else:
                detail = f"{type(exc).__name__}: {exc}"
            # stderr is safe for the stdio transport; stdout carries the MCP protocol.
            LOGGER.warning(
                "%s: unexpected %s in tool %s", adapter, type(exc).__name__, tool_name, exc_info=exc
            )
            return UpstreamError(
                f"{adapter}: upstream response had an unexpected shape ({detail}) while running "
                f"{tool_name}, or the adapter has a bug. The API may have changed; please report "
                "this."
            )

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_guarded(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await fn(*args, **kwargs)
                except _SHAPE_ERRORS as exc:
                    raise unexpected(exc) from exc

            return async_guarded

        @functools.wraps(fn)
        def guarded(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            except _SHAPE_ERRORS as exc:
                raise unexpected(exc) from exc

        return guarded


def register_adapters(
    mcp: MCPServer, http: HttpClient, toolsets: set[str] | None = None
) -> list[LoadedAdapter]:
    """Register every discovered adapter in the selected toolsets (all if ``toolsets`` is None)."""
    loaded = []
    for spec in discover_adapters():
        if toolsets is not None and spec.toolset not in toolsets:
            continue
        module = importlib.import_module(f"keyless_mcp.adapters.{spec.name}.tools")
        register = getattr(module, "register", None)
        if not callable(register):
            raise AdapterError(f"adapters/{spec.name}/tools.py must define register(tools, http)")
        registry = ToolRegistry(mcp, spec.name)
        register(registry, http.for_adapter(spec.name, spec.rate_limit_per_minute))
        if not registry.names:
            raise AdapterError(f"adapters/{spec.name}: register() added no tools")
        loaded.append(LoadedAdapter(spec, tuple(registry.names)))
    return loaded
