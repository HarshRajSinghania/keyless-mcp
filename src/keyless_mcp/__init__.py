"""keyless-mcp: one MCP server wrapping free, no-auth public APIs."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("keyless-mcp")
except PackageNotFoundError:  # pragma: no cover - running from an uninstalled checkout
    __version__ = "0.0.0"

REPO_URL = "https://github.com/sineframe/keyless-mcp"
USER_AGENT = f"keyless-mcp/{__version__} (+{REPO_URL})"
