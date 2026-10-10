"""OSV tools: query vulnerabilities by package and fetch one advisory by id."""

from typing import Annotated, Any
from urllib.parse import quote

from pydantic import Field

from keyless_mcp.core import AdapterHttp, InvalidInput, ToolRegistry, UpstreamError, truncate

API_URL = "https://api.osv.dev/v1"
WEB_URL = "https://osv.dev/vulnerability"

# Ecosystem names are case-sensitive in the OSV API. Keys are lowercase for forgiving input.
ECOSYSTEMS = {
    name.lower(): name
    for name in (
        "PyPI",
        "npm",
        "crates.io",
        "Go",
        "Maven",
        "NuGet",
        "RubyGems",
        "Packagist",
        "Hex",
        "Pub",
        "Hackage",
        "CRAN",
        "Julia",
        "SwiftURL",
        "GitHub Actions",
        "Debian",
        "Alpine",
        "Ubuntu",
        "Linux",
    )
}
MAX_VULNS = 20
MAX_REFERENCES = 10


def canonical_ecosystem(value: str) -> str:
    found = ECOSYSTEMS.get(value.strip().lower())
    if found is None:
        raise InvalidInput(
            f"Unknown ecosystem {value!r}. Use one of: {', '.join(ECOSYSTEMS.values())}."
        )
    return found


def _fixed_versions(vuln: dict[str, Any], package: str | None = None) -> list[str]:
    fixed: list[str] = []
    for affected in vuln.get("affected", []):
        name = affected.get("package", {}).get("name", "")
        if package is not None and name.lower() != package.lower():
            continue
        for rng in affected.get("ranges", []):
            fixed.extend(e["fixed"] for e in rng.get("events", []) if "fixed" in e)
    return list(dict.fromkeys(fixed))


def _severity(vuln: dict[str, Any]) -> dict[str, Any]:
    label = vuln.get("database_specific", {}).get("severity")
    vectors = [s.get("score") for s in vuln.get("severity", []) if s.get("score")]
    return {"severity": label, "cvss": vectors[0] if vectors else None}


def summarise_vulnerability(vuln: dict[str, Any], package: str | None = None) -> dict[str, Any]:
    """Compact record used in query results."""
    summary = vuln.get("summary") or truncate(vuln.get("details"), 200)
    return {
        "id": vuln["id"],
        "summary": truncate(summary, 200),
        "aliases": vuln.get("aliases", []),
        **_severity(vuln),
        "published": vuln.get("published"),
        "modified": vuln.get("modified"),
        "fixed_versions": _fixed_versions(vuln, package),
        "url": f"{WEB_URL}/{vuln['id']}",
    }


def _require_vuln_list(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        raise UpstreamError("osv: unexpected response shape from /v1/query")
    return data.get("vulns", [])


def register(tools: ToolRegistry, http: AdapterHttp) -> None:
    @tools.tool(title="Query package vulnerabilities")
    async def osv_query_package(
        name: Annotated[
            str,
            Field(
                description="Package name as published in its ecosystem, e.g. 'jinja2' (PyPI), "
                "'lodash' (npm), 'serde' (crates.io), 'github.com/gin-gonic/gin' (Go)."
            ),
        ],
        ecosystem: Annotated[
            str,
            Field(
                description="Package ecosystem, e.g. 'PyPI', 'npm', 'crates.io', 'Go', 'Maven', "
                "'NuGet', 'RubyGems', 'Packagist'. Case-insensitive."
            ),
        ],
        version: Annotated[
            str | None,
            Field(
                description="Exact version to check, e.g. '2.4.1'. Omit to list vulnerabilities "
                "affecting any version of the package."
            ),
        ] = None,
    ) -> dict[str, Any]:
        """List known vulnerabilities (CVE/GHSA/PYSEC ids) for an open-source package, optionally
        for one exact version. Each entry has id, summary, severity, fixed versions and an
        osv.dev link; use osv_get_vulnerability for full details."""
        if not name.strip():
            raise InvalidInput("name must not be empty.")
        canonical = canonical_ecosystem(ecosystem)
        body: dict[str, Any] = {"package": {"name": name.strip(), "ecosystem": canonical}}
        if version is not None and version.strip():
            body["version"] = version.strip()
        data = await http.post_json(f"{API_URL}/query", body)
        vulns = _require_vuln_list(data)
        shown = vulns[:MAX_VULNS]
        return {
            "package": body["package"]["name"],
            "ecosystem": canonical,
            "version": body.get("version"),
            "total": len(vulns),
            "returned": len(shown),
            "truncated": len(vulns) > MAX_VULNS or bool(data.get("next_page_token")),
            "vulnerabilities": [summarise_vulnerability(v, body["package"]["name"]) for v in shown],
        }

    @tools.tool(title="Get vulnerability details")
    async def osv_get_vulnerability(
        vuln_id: Annotated[
            str,
            Field(
                description="OSV vulnerability id, e.g. 'GHSA-462w-v97r-4m45', 'PYSEC-2019-217', "
                "'RUSTSEC-2021-0001'. CVE ids such as 'CVE-2019-10906' also work for many records."
            ),
        ],
    ) -> dict[str, Any]:
        """Fetch one vulnerability advisory by id: summary, trimmed details, severity, aliases,
        affected packages with fixed versions, and reference links."""
        vid = vuln_id.strip()
        if not vid or any(c in vid for c in "/?# \t\n"):
            raise InvalidInput(
                f"{vuln_id!r} is not a valid vulnerability id. Example: 'GHSA-462w-v97r-4m45'."
            )
        try:
            vuln = await http.get_json(f"{API_URL}/vulns/{quote(vid)}")
        except UpstreamError as exc:
            if exc.status == 404:
                raise InvalidInput(
                    f"No OSV record found with id {vid!r}. Use osv_query_package to find ids."
                ) from None
            raise
        references = [
            {"type": r.get("type"), "url": r.get("url")} for r in vuln.get("references", [])
        ]
        return {
            "id": vuln["id"],
            "summary": vuln.get("summary"),
            "details": truncate(vuln.get("details"), 1500),
            "aliases": vuln.get("aliases", []),
            **_severity(vuln),
            "published": vuln.get("published"),
            "modified": vuln.get("modified"),
            "withdrawn": vuln.get("withdrawn"),
            "affected": [
                {
                    "package": a.get("package", {}).get("name"),
                    "ecosystem": a.get("package", {}).get("ecosystem"),
                    "fixed_versions": _fixed_versions({"affected": [a]}),
                }
                for a in vuln.get("affected", [])
            ],
            "references": references[:MAX_REFERENCES],
            "references_omitted": max(0, len(references) - MAX_REFERENCES),
            "url": f"{WEB_URL}/{vuln['id']}",
        }
