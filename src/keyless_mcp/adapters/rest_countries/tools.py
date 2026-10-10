"""Country tools.

The REST Countries API (restcountries.com) now needs an API key, so this adapter reads the
World Bank country and indicator APIs instead: keyless, official and stable. They provide name,
ISO codes, capital, region, income group, coordinates and population. They do not provide
currencies or languages, so those are not offered. The flag emoji is derived from the ISO code.
"""

import re
import unicodedata
from typing import Annotated, Any

from pydantic import Field

from keyless_mcp.core import AdapterHttp, InvalidInput, ToolRegistry, UpstreamError

API_URL = "https://api.worldbank.org/v2"
WEB_URL = "https://data.worldbank.org/country"
POPULATION_INDICATOR = "SP.POP.TOTL"
MAX_MATCHES = 3
CODE_RE = re.compile(r"^[A-Za-z]{2,3}$")

# Everyday names that differ from the World Bank's names ("Korea, Rep.", "Russian Federation").
ALIASES = {
    "south korea": "KR",
    "republic of korea": "KR",
    "north korea": "KP",
    "russia": "RU",
    "iran": "IR",
    "vietnam": "VN",
    "turkey": "TR",
    "czech republic": "CZ",
    "slovakia": "SK",
    "kyrgyzstan": "KG",
    "laos": "LA",
    "syria": "SY",
    "ivory coast": "CI",
    "cape verde": "CV",
    "swaziland": "SZ",
    "macedonia": "MK",
    "burma": "MM",
    "macau": "MO",
    "palestine": "PS",
    "east timor": "TL",
    "usa": "US",
    "united states of america": "US",
    "america": "US",
    "uk": "GB",
    "britain": "GB",
    "great britain": "GB",
    "england": "GB",
    "uae": "AE",
    "drc": "CD",
    "dr congo": "CD",
    "holland": "NL",
}


def flag_emoji(iso2: str) -> str | None:
    """Flag emoji from a two-letter code (regional indicator symbols), e.g. 'JP' -> a flag."""
    if len(iso2) == 2 and iso2.isascii() and iso2.isalpha():
        return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso2.upper())
    return None


def normalise(text: str) -> str:
    """Lowercase, strip accents and punctuation: "Côte d'Ivoire" -> "cote d ivoire"."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", plain.lower()).split())


INVALID_PARAMETER = "120"  # message id the API uses for an unknown country code


def _message(data: Any) -> dict[str, Any] | None:
    """The error message of a World Bank response, which is ``[{"message": [{...}]}]``."""
    if isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get("message"):
        return data[0]["message"][0]
    return None


def _rows(data: Any) -> list[dict[str, Any]]:
    """Rows of a World Bank response, which is ``[paging, rows]`` (rows is null when empty)."""
    if isinstance(data, list) and len(data) == 2 and (data[1] is None or isinstance(data[1], list)):
        return data[1] or []
    message = _message(data)
    if message is not None:
        raise UpstreamError(
            f"rest_countries: the World Bank API answered: {message.get('value', 'unknown error')}"
        )
    raise UpstreamError("rest_countries: unexpected response shape from the World Bank API")


def _is_country(row: dict[str, Any]) -> bool:
    """The country list also holds aggregates such as 'World' or 'Euro area'."""
    return row["region"]["id"] != "NA"


def _number(text: str | None) -> float | None:
    try:
        return float(text) if text else None
    except ValueError:
        return None


async def _populations(http: AdapterHttp, iso3_codes: list[str]) -> dict[str, tuple[int, str]]:
    """Latest known population and its year for each ISO3 code, in one request."""
    if not iso3_codes:
        return {}
    data = await http.get_json(
        f"{API_URL}/country/{';'.join(iso3_codes)}/indicator/{POPULATION_INDICATOR}",
        {"format": "json", "mrnev": 1, "per_page": len(iso3_codes)},
    )
    return {
        row["countryiso3code"]: (int(row["value"]), row["date"])
        for row in _rows(data)
        if row.get("value") is not None
    }


def _describe(row: dict[str, Any], population: tuple[int, str] | None) -> dict[str, Any]:
    iso2 = row["iso2Code"]
    return {
        "name": row["name"],
        "iso2": iso2,
        "iso3": row["id"],
        "capital": row.get("capitalCity") or None,
        "region": row["region"]["value"],
        "income_level": row["incomeLevel"]["value"],
        "latitude": _number(row.get("latitude")),
        "longitude": _number(row.get("longitude")),
        "population": population[0] if population else None,
        "population_year": population[1] if population else None,
        "flag": flag_emoji(iso2),
        "url": f"{WEB_URL}/{iso2}",
    }


def find_countries(countries: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Best matches for a name, ordered by how exact the match is, then alphabetically."""
    text = normalise(query)
    alias = ALIASES.get(text)
    tiers: list[list[dict[str, Any]]] = [[], [], [], []]
    tokens = set(text.split())
    for row in countries:
        name = normalise(row["name"])
        if alias is not None:
            if row["iso2Code"] == alias:
                tiers[0].append(row)
        elif text in (row["iso2Code"].lower(), row["id"].lower()) or name == text:
            tiers[0].append(row)
        elif tokens and tokens <= set(name.split()):
            tiers[1].append(row)
        elif len(text) >= 3 and text in name:
            tiers[2].append(row)
    return [row for tier in tiers for row in sorted(tier, key=lambda r: r["name"])]


def register(tools: ToolRegistry, http: AdapterHttp) -> None:
    @tools.tool(title="Find countries by name")
    async def rest_countries_get(
        name: Annotated[
            str,
            Field(
                description="Country name in English, e.g. 'Japan', 'South Korea', 'Germany' or "
                "'United States'. Common short names (Russia, Vietnam, UK) and ISO codes "
                "('JP', 'JPN') work too. Partial names such as 'korea' return every match."
            ),
        ],
    ) -> dict[str, Any]:
        """Look up countries by name. Returns up to 3 best matches, each with official name,
        ISO codes, capital, region, income group, coordinates, latest population (with its
        year), flag emoji and a World Bank link. Does not include currencies or languages. Use
        rest_countries_by_code when you already know the ISO code."""
        query = name.strip()
        if not query:
            raise InvalidInput("name must not be empty.")
        data = await http.get_json(f"{API_URL}/country", {"format": "json", "per_page": 400})
        listing = _rows(data)
        matches = find_countries([row for row in listing if _is_country(row)], query)
        if not matches:
            raise InvalidInput(
                f"No country matches {query!r}. Use the English name (for example 'Germany') or "
                "an ISO code such as 'DE'."
            )
        shown = matches[:MAX_MATCHES]
        populations = await _populations(http, [row["id"] for row in shown])
        return {
            "query": query,
            "total_matches": len(matches),
            "returned": len(shown),
            "countries": [_describe(row, populations.get(row["id"])) for row in shown],
        }

    @tools.tool(title="Get country by ISO code")
    async def rest_countries_by_code(
        code: Annotated[
            str,
            Field(
                description="ISO 3166-1 country code: two letters ('DE', 'JP') or three letters "
                "('DEU', 'JPN'). Case-insensitive."
            ),
        ],
    ) -> dict[str, Any]:
        """Get one country by its ISO 3166-1 alpha-2 or alpha-3 code: official name, ISO codes,
        capital, region, income group, coordinates, latest population (with its year), flag
        emoji and a World Bank link. Does not include currencies or languages."""
        clean = code.strip()
        if not CODE_RE.match(clean):
            raise InvalidInput(
                f"{code!r} is not an ISO country code. Use two letters ('DE') or three ('DEU')."
            )
        data = await http.get_json(f"{API_URL}/country/{clean.upper()}", {"format": "json"})
        message = _message(data)
        rows = [] if message and message.get("id") == INVALID_PARAMETER else _rows(data)
        if not rows or not _is_country(rows[0]):
            raise InvalidInput(f"No country has the ISO code {clean.upper()!r}. Example: 'DE'.")
        row = rows[0]
        populations = await _populations(http, [row["id"]])
        return _describe(row, populations.get(row["id"]))
