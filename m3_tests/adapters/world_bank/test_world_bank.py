"""World Bank adapter: catalog, happy paths and error paths, replayed from cassettes."""

from __future__ import annotations

import anyio
import pytest

from keyless_mcp.adapters.world_bank.tools import flag_emoji, register
from keyless_mcp.core import ToolRegistry
from m3_tests._support.results import result_text

pytestmark = pytest.mark.m3(suite_name="world_bank")

JAPAN_FLAG = "\U0001f1ef\U0001f1f5"  # regional indicators J + P


def test_lists_both_country_tools_with_documented_inputs(connect) -> None:
    """The catalog has world_bank_country_search(name) and world_bank_country_by_code(code)."""
    with connect("world_bank") as client:
        tools = {t.name: t for t in client.list_all_tools() if t.name.startswith("world_bank_")}
    assert set(tools) == {"world_bank_country_search", "world_bank_country_by_code"}
    assert list(tools["world_bank_country_search"].input_schema["required"]) == ["name"]
    assert list(tools["world_bank_country_by_code"].input_schema["required"]) == ["code"]


def test_get_japan_returns_capital_region_population_and_flag(connect) -> None:
    """Japan: capital Tokyo, ISO JP/JPN, East Asia & Pacific, roughly 120 million people."""
    with connect("world_bank") as client:
        result = client.call_tool("world_bank_country_search", {"name": "Japan"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["total_matches"] == data["returned"] == 1
    japan = data["countries"][0]
    assert japan["name"] == "Japan"
    assert (japan["iso2"], japan["iso3"]) == ("JP", "JPN")
    assert japan["capital"] == "Tokyo"
    assert japan["region"] == "East Asia & Pacific"
    assert japan["income_level"] == "High income"
    assert 100_000_000 < japan["population"] < 140_000_000
    assert japan["population_year"].isdigit()
    assert japan["flag"] == JAPAN_FLAG
    assert japan["latitude"] == pytest.approx(35.67, abs=1)
    assert japan["longitude"] == pytest.approx(139.77, abs=1)
    assert japan["url"] == "https://data.worldbank.org/country/JP"


def test_get_partial_name_returns_every_match_alphabetically(connect) -> None:
    """'korea' matches both North and South Korea, each with its own population."""
    with connect("world_bank") as client:
        result = client.call_tool("world_bank_country_search", {"name": "korea"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["total_matches"] == 2
    north, south = data["countries"]
    assert (north["iso3"], south["iso3"]) == ("PRK", "KOR")
    assert south["capital"] == "Seoul"
    assert north["capital"] == "Pyongyang"
    assert south["population"] > north["population"] > 20_000_000


def test_get_understands_everyday_names_that_differ_from_official_ones(connect) -> None:
    """'South Korea' is listed by the World Bank as 'Korea, Rep.'; the alias finds it."""
    with connect("world_bank") as client:
        result = client.call_tool("world_bank_country_search", {"name": "South Korea"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["total_matches"] == 1
    assert data["countries"][0]["iso2"] == "KR"
    assert data["countries"][0]["capital"] == "Seoul"


def test_by_code_accepts_a_three_letter_code(connect) -> None:
    """DEU is Germany: capital Berlin, Europe & Central Asia, about 80 to 90 million people."""
    with connect("world_bank") as client:
        result = client.call_tool("world_bank_country_by_code", {"code": "DEU"})
    assert result.is_error is False, result_text(result)
    germany = result.structured_content
    assert germany["name"] == "Germany"
    assert germany["iso2"] == "DE"
    assert germany["capital"] == "Berlin"
    assert germany["region"] == "Europe & Central Asia"
    assert 80_000_000 < germany["population"] < 90_000_000
    assert germany["flag"] == "\U0001f1e9\U0001f1ea"


def test_by_code_is_case_insensitive_and_accepts_two_letters(connect) -> None:
    """'jp' resolves to Japan."""
    with connect("world_bank") as client:
        result = client.call_tool("world_bank_country_by_code", {"code": "jp"})
    assert result.is_error is False, result_text(result)
    assert result.structured_content["name"] == "Japan"
    assert result.structured_content["flag"] == JAPAN_FLAG


def test_get_reports_a_name_that_matches_nothing(connect) -> None:
    """An unknown country is an is_error result that suggests how to phrase the query."""
    with connect("world_bank") as client:
        result = client.call_tool("world_bank_country_search", {"name": "Atlantis"})
    assert result.is_error is True
    text = result_text(result)
    assert "No country matches 'Atlantis'" in text
    assert "ISO code" in text


def test_by_code_reports_an_unknown_code(connect) -> None:
    """The API answers an unknown code with a message; it becomes a readable is_error result."""
    with connect("world_bank") as client:
        result = client.call_tool("world_bank_country_by_code", {"code": "ZZ"})
    assert result.is_error is True
    assert "No country has the ISO code 'ZZ'" in result_text(result)


def test_by_code_rejects_world_bank_aggregates_such_as_the_world(connect) -> None:
    """WLD is a valid World Bank code but is not a country."""
    with connect("world_bank") as client:
        result = client.call_tool("world_bank_country_by_code", {"code": "WLD"})
    assert result.is_error is True
    assert "No country has the ISO code 'WLD'" in result_text(result)


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        ("world_bank_country_search", {"name": "  "}, "name must not be empty"),
        ("world_bank_country_by_code", {"code": "J"}, "not an ISO country code"),
        ("world_bank_country_by_code", {"code": "../x"}, "not an ISO country code"),
        ("world_bank_country_by_code", {"code": "JAPN"}, "not an ISO country code"),
    ],
)
def test_invalid_input_is_rejected_before_any_request(connect, tool, arguments, message) -> None:
    """Bad arguments are is_error results with a fix-it message; no cassette is needed."""
    with connect("world_bank") as client:
        result = client.call_tool(tool, arguments)
    assert result.is_error is True
    assert message in result_text(result)


def test_flag_emoji_is_built_from_regional_indicator_symbols() -> None:
    """Two ASCII letters become two regional indicator symbols; anything else has no flag."""
    assert flag_emoji("JP") == JAPAN_FLAG
    assert flag_emoji("jp") == JAPAN_FLAG
    assert flag_emoji("JPN") is None
    assert flag_emoji("1A") is None


def test_the_country_list_is_downloaded_once_per_process() -> None:
    """Repeated name lookups reuse the list; only the (small) population request repeats."""
    row = {
        "id": "JPN",
        "iso2Code": "JP",
        "name": "Japan",
        "region": {"id": "EAS", "value": "East Asia & Pacific"},
        "incomeLevel": {"value": "High income"},
        "capitalCity": "Tokyo",
        "latitude": "35.67",
        "longitude": "139.77",
    }
    population = {"countryiso3code": "JPN", "date": "2024", "value": 123_000_000}
    requests: list[str] = []

    class StubHttp:
        async def get_json(self, url, params=None):
            requests.append(url)
            return [{}, [population] if "indicator" in url else [row]]

    class StubServer:
        tools: dict = {}

        def add_tool(self, fn, *, name, **_kwargs) -> None:
            self.tools[name] = fn

    server = StubServer()
    register(ToolRegistry(server, "world_bank"), StubHttp())  # type: ignore[arg-type]
    search = server.tools["world_bank_country_search"]

    async def lookups() -> list[dict]:
        return [await search(name="Japan"), await search(name="jp")]

    first, second = anyio.run(lookups)
    assert first["countries"][0]["population"] == 123_000_000
    assert second["countries"][0]["population"] == 123_000_000
    list_requests = [u for u in requests if u.endswith("/country")]
    assert len(list_requests) == 1, requests
    assert len(requests) == 3, "one list download plus one population request per lookup"


@pytest.mark.live
def test_live_by_code_hits_the_real_api(connect) -> None:
    """Smoke test against the real World Bank API (excluded from PR CI)."""
    with connect("world_bank", mode="live") as client:
        result = client.call_tool("world_bank_country_by_code", {"code": "DE"})
    assert result.is_error is False, result_text(result)
    assert result.structured_content["capital"] == "Berlin"
