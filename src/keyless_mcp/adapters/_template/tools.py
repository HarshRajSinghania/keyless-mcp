"""ADAPTER_TITLE tools. TODO: replace the example tool below with real ones."""

from typing import Annotated, Any

from pydantic import Field

from keyless_mcp.core import AdapterHttp, InvalidInput, ToolRegistry, truncate

BASE_URL = "https://api.example.com"  # TODO keep in sync with adapter.yaml
MAX_LIMIT = 20


def register(tools: ToolRegistry, http: AdapterHttp) -> None:
    """Called once at startup. Register every tool of this adapter here."""

    # Tool names must be <adapter>_<verb> in snake_case. The docstring is the tool description
    # an agent reads to decide when to call it, so say what it returns, not how it works.
    @tools.tool(title="Search ADAPTER_TITLE")
    async def ADAPTER_NAME_search(
        query: Annotated[
            str, Field(description="Free-text search terms, e.g. 'climate'. Must not be empty.")
        ],
        limit: Annotated[
            int, Field(description=f"Maximum results to return, 1 to {MAX_LIMIT}. Default 5.")
        ] = 5,
    ) -> dict[str, Any]:
        """Search ADAPTER_TITLE. Returns a compact list of matches with title and url."""
        # Validate input yourself and raise InvalidInput: the agent sees the message and can retry.
        if not query.strip():
            raise InvalidInput("query must not be empty.")
        if not 1 <= limit <= MAX_LIMIT:
            raise InvalidInput(f"limit must be between 1 and {MAX_LIMIT}.")
        # All HTTP goes through `http`. Upstream failures (4xx/5xx, timeouts, bad JSON) raise
        # UpstreamError for you; do not catch them unless you can give a better message.
        data = await http.get_json(f"{BASE_URL}/search", {"q": query, "limit": limit})
        # Return compact, structured data. Trim long text and include source URLs.
        return {
            "query": query,
            "results": [
                {"title": truncate(item["title"], 200), "url": item["url"]}
                for item in data.get("items", [])
            ],
        }
