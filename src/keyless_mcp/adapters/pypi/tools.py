"""PyPI tools: package metadata (latest release) and metadata of one specific release."""

import re
from typing import Annotated, Any
from urllib.parse import quote

from pydantic import Field

from keyless_mcp.core import AdapterHttp, InvalidInput, ToolRegistry, UpstreamError, truncate

API_URL = "https://pypi.org/pypi"
PROJECT_URL = "https://pypi.org/project"

# PEP 508 project names: letters, digits, '.', '_' and '-', starting and ending with a letter/digit.
NAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")
# PEP 440 versions plus local labels: 1.0, 2.1.0rc1, 1!2.0, 1.0.post1, 1.0+local.1.
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+!-]*$")
MAX_DEPENDENCIES = 25
MAX_FILES = 10
MAX_PROJECT_URLS = 10


def check_name(name: str) -> str:
    clean = name.strip()
    if not NAME_RE.match(clean):
        raise InvalidInput(
            f"{name!r} is not a valid PyPI package name. Use letters, digits, '.', '_' or '-', "
            "e.g. 'requests' or 'scikit-learn'."
        )
    return clean


def _license(info: dict[str, Any]) -> str | None:
    """The license as an SPDX expression or short name; some packages paste a whole license text
    into the free-form field, in which case the trove classifier is the better answer."""
    expression = (info.get("license_expression") or "").strip()
    if expression:
        return expression
    free_text = (info.get("license") or "").strip()
    if free_text and len(free_text) <= 100 and "\n" not in free_text:
        return free_text
    for classifier in info.get("classifiers") or []:
        if classifier.startswith("License :: ") and classifier != "License :: OSI Approved":
            return classifier.rsplit(" :: ", 1)[-1]
    return truncate(free_text, 100) or None


def _first_upload(files: list[dict[str, Any]]) -> str | None:
    times = [f["upload_time_iso_8601"] for f in files if f.get("upload_time_iso_8601")]
    return min(times) if times else None


def describe(data: dict[str, Any], *, detailed: bool) -> dict[str, Any]:
    info = data["info"]
    files = data.get("urls") or []
    name, version = info["name"], info["version"]
    result: dict[str, Any] = {
        "name": name,
        "version": version,
        "summary": truncate(info.get("summary"), 300),
        "license": _license(info),
        "requires_python": info.get("requires_python"),
        "author": info.get("author") or None,
        "release_date": _first_upload(files),
        "yanked": bool(info.get("yanked")),
        "project_urls": dict(list((info.get("project_urls") or {}).items())[:MAX_PROJECT_URLS]),
        "url": f"{PROJECT_URL}/{name}/{version}/" if detailed else f"{PROJECT_URL}/{name}/",
    }
    if info.get("yanked_reason"):
        result["yanked_reason"] = truncate(info["yanked_reason"], 300)
    if "releases" in data:  # only on the package endpoint
        result["release_count"] = len(data["releases"])
    dependencies = info.get("requires_dist") or []
    result["dependencies"] = dependencies[:MAX_DEPENDENCIES]
    result["dependencies_omitted"] = max(0, len(dependencies) - MAX_DEPENDENCIES)
    if detailed:
        result["files"] = [
            {
                "filename": f["filename"],
                "type": f.get("packagetype"),
                "python_version": f.get("python_version"),
                "size_bytes": f.get("size"),
                "uploaded": f.get("upload_time_iso_8601"),
                "url": f.get("url"),
            }
            for f in files[:MAX_FILES]
        ]
        result["files_omitted"] = max(0, len(files) - MAX_FILES)
    return result


def register(tools: ToolRegistry, http: AdapterHttp) -> None:
    @tools.tool(title="Get PyPI package")
    async def pypi_get_package(
        name: Annotated[
            str,
            Field(
                description="PyPI package name, e.g. 'requests', 'numpy' or 'scikit-learn'. "
                "Case-insensitive; '-', '_' and '.' are interchangeable."
            ),
        ],
    ) -> dict[str, Any]:
        """Get the latest release of a Python package from PyPI: version, one-line summary,
        license, required Python versions, project links (homepage, source, docs), release date,
        total number of releases and its dependencies. Use pypi_get_release for an older
        version."""
        clean = check_name(name)
        try:
            data = await http.get_json(f"{API_URL}/{quote(clean)}/json")
        except UpstreamError as exc:
            if exc.status == 404:
                raise InvalidInput(
                    f"No PyPI package named {clean!r}. Check the spelling."
                ) from None
            raise
        return describe(data, detailed=False)

    @tools.tool(title="Get PyPI release")
    async def pypi_get_release(
        name: Annotated[
            str, Field(description="PyPI package name, e.g. 'requests'. Case-insensitive.")
        ],
        version: Annotated[
            str,
            Field(
                description="Exact release version, e.g. '2.31.0' or '1.0.0rc1'. "
                "Use pypi_get_package to see the latest version."
            ),
        ],
    ) -> dict[str, Any]:
        """Get one specific release of a Python package: summary, license, required Python
        versions, dependencies, whether it was yanked, upload date and its downloadable files
        (wheels and source archives with size and URL)."""
        clean = check_name(name)
        ver = version.strip()
        if not VERSION_RE.match(ver):
            raise InvalidInput(f"{version!r} is not a valid version. Example: '2.31.0'.")
        try:
            data = await http.get_json(f"{API_URL}/{quote(clean)}/{quote(ver)}/json")
        except UpstreamError as exc:
            if exc.status == 404:
                raise InvalidInput(
                    f"No release {ver!r} of PyPI package {clean!r} (the package or that version "
                    "does not exist). Use pypi_get_package to see the latest version."
                ) from None
            raise
        return describe(data, detailed=True)
