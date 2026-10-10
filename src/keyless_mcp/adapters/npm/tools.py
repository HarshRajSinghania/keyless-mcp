"""npm tools. The registry document for a package is huge (every version's metadata and the
README), so only the handful of fields an agent needs are kept."""

import re
from typing import Annotated, Any
from urllib.parse import quote

from pydantic import Field

from keyless_mcp.core import AdapterHttp, InvalidInput, ToolRegistry, UpstreamError, truncate

REGISTRY_URL = "https://registry.npmjs.org"
WEB_URL = "https://www.npmjs.com/package"
MAX_SIZE = 25

# npm names: optional @scope/, then URL-safe characters; at most 214 characters in total.
NAME_RE = re.compile(r"^(@[A-Za-z0-9~_-][A-Za-z0-9._~-]*/)?[A-Za-z0-9~_-][A-Za-z0-9._~-]*$")
MAX_KEYWORDS = 10
MAX_MAINTAINERS = 10
MAX_DIST_TAGS = 10


def check_name(name: str) -> str:
    clean = name.strip()
    if len(clean) > 214 or not NAME_RE.match(clean):
        raise InvalidInput(
            f"{name!r} is not a valid npm package name. Examples: 'lodash', '@types/node'."
        )
    return clean


def _license(value: Any) -> str | None:
    if isinstance(value, dict):  # legacy {"type": "MIT", "url": ...}
        value = value.get("type")
    return value if isinstance(value, str) and value else None


def _repository(value: Any) -> str | None:
    """Normalise 'git+https://github.com/x/y.git' or 'github:x/y' to a browsable https URL."""
    url = value.get("url") if isinstance(value, dict) else value
    if not isinstance(url, str) or not url:
        return None
    url = re.sub(r"^git\+", "", url)
    url = re.sub(r"^(git|ssh)://(git@)?", "https://", url)
    url = re.sub(r"^git@([^:]+):", r"https://\1/", url)
    if url.startswith("github:"):
        url = "https://github.com/" + url.removeprefix("github:")
    return re.sub(r"\.git$", "", url)


def _person_name(person: Any) -> str | None:
    if isinstance(person, dict):
        return person.get("name")
    return person if isinstance(person, str) else None


def describe_package(doc: dict[str, Any]) -> dict[str, Any]:
    name = doc["name"]
    tags = doc.get("dist-tags") or {}
    latest = tags["latest"]
    manifest = doc["versions"][latest]
    times = doc.get("time") or {}
    maintainers = doc.get("maintainers") or manifest.get("maintainers") or []
    return {
        "name": name,
        "latest_version": latest,
        "description": truncate(manifest.get("description") or doc.get("description"), 300),
        "license": _license(manifest.get("license") or doc.get("license")),
        "homepage": manifest.get("homepage") or doc.get("homepage"),
        "repository": _repository(manifest.get("repository") or doc.get("repository")),
        "author": _person_name(manifest.get("author") or doc.get("author")),
        "keywords": (manifest.get("keywords") or doc.get("keywords") or [])[:MAX_KEYWORDS],
        "maintainers_count": len(maintainers),
        "maintainers": [m for m in map(_person_name, maintainers) if m][:MAX_MAINTAINERS],
        "last_published": times.get(latest) or times.get("modified"),
        "first_published": times.get("created"),
        "version_count": len(doc["versions"]),
        "dependency_count": len(manifest.get("dependencies") or {}),
        "dist_tags": dict(list(tags.items())[:MAX_DIST_TAGS]),
        "deprecated": truncate(manifest["deprecated"], 300) if manifest.get("deprecated") else None,
        "url": f"{WEB_URL}/{name}",
    }


def register(tools: ToolRegistry, http: AdapterHttp) -> None:
    @tools.tool(title="Get npm package")
    async def npm_get_package(
        name: Annotated[
            str,
            Field(
                description="npm package name, e.g. 'express', 'left-pad' or a scoped name such "
                "as '@types/node'. Case-sensitive for legacy names."
            ),
        ],
    ) -> dict[str, Any]:
        """Get the essentials of an npm package: latest version, description, license,
        repository and homepage, number of maintainers (and their names), time of the last
        publish, number of versions, dependency count and any deprecation notice. Use
        npm_search to find a package name first."""
        clean = check_name(name)
        try:
            doc = await http.get_json(f"{REGISTRY_URL}/{quote(clean, safe='@')}")
        except UpstreamError as exc:
            if exc.status == 404:
                raise InvalidInput(
                    f"No npm package named {clean!r}. Use npm_search to find the right name."
                ) from None
            raise
        return describe_package(doc)

    @tools.tool(title="Search npm packages")
    async def npm_search(
        query: Annotated[
            str,
            Field(
                description="Search terms, e.g. 'markdown parser' or 'react date picker'. "
                "Supports qualifiers such as 'author:sindresorhus' or 'keywords:cli'."
            ),
        ],
        size: Annotated[
            int, Field(description=f"How many packages to return, 1 to {MAX_SIZE}. Default 10.")
        ] = 10,
    ) -> dict[str, Any]:
        """Search the npm registry by keyword. Returns matching packages ranked by npm's
        relevance score with name, version, description, publisher, last-publish date,
        weekly downloads and npm page link. Use npm_get_package for full details."""
        if not query.strip():
            raise InvalidInput("query must not be empty.")
        if not 1 <= size <= MAX_SIZE:
            raise InvalidInput(f"size must be between 1 and {MAX_SIZE}.")
        data = await http.get_json(
            f"{REGISTRY_URL}/-/v1/search", {"text": query.strip(), "size": size}
        )
        results = []
        for item in data["objects"]:
            package = item["package"]
            results.append(
                {
                    "name": package["name"],
                    "version": package.get("version"),
                    "description": truncate(package.get("description"), 200),
                    "keywords": (package.get("keywords") or [])[:MAX_KEYWORDS],
                    "publisher": (package.get("publisher") or {}).get("username"),
                    "last_published": package.get("date"),
                    "weekly_downloads": (item.get("downloads") or {}).get("weekly"),
                    "url": f"{WEB_URL}/{package['name']}",
                }
            )
        return {
            "query": query.strip(),
            "total": data["total"],
            "returned": len(results),
            "packages": results,
        }
