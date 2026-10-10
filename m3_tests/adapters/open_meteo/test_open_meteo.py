"""Open-Meteo adapter: catalog, happy paths and error paths, replayed from cassettes."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from keyless_mcp.adapters.open_meteo.tools import weather_label
from m3_tests._support.results import result_text

pytestmark = pytest.mark.m3(suite_name="open_meteo")


def test_lists_both_open_meteo_tools_with_documented_inputs(connect) -> None:
    """The catalog has open_meteo_forecast(latitude, longitude, days) and open_meteo_geocode."""
    with connect("open_meteo") as client:
        tools = {t.name: t for t in client.list_all_tools() if t.name.startswith("open_meteo_")}
    assert set(tools) == {"open_meteo_forecast", "open_meteo_geocode"}
    forecast = tools["open_meteo_forecast"].input_schema
    assert list(forecast["required"]) == ["latitude", "longitude"]
    assert forecast["properties"]["days"]["default"] == 3
    geocode = tools["open_meteo_geocode"].input_schema
    assert list(geocode["required"]) == ["name"]
    assert geocode["properties"]["count"]["default"] == 5


def test_forecast_returns_three_consecutive_days_for_berlin(connect) -> None:
    """Berlin (52.52, 13.41) is in Europe/Berlin; each day has sane temperatures and a label."""
    with connect("open_meteo") as client:
        result = client.call_tool(
            "open_meteo_forecast", {"latitude": 52.52, "longitude": 13.41, "days": 3}
        )
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["timezone"] == "Europe/Berlin"
    assert data["temperature_unit"] == "°C"
    assert data["returned"] == len(data["days"]) == 3
    assert data["latitude"] == pytest.approx(52.52, abs=0.2)
    assert data["longitude"] == pytest.approx(13.41, abs=0.2)
    first = date.fromisoformat(data["days"][0]["date"])
    for offset, day in enumerate(data["days"]):
        assert day["date"] == (first + timedelta(days=offset)).isoformat()
        assert -40 < day["temp_min"] <= day["temp_max"] < 50
        assert day["precipitation_mm"] >= 0
        assert day["weather"] == weather_label(day["weather_code"])
        assert not day["weather"].startswith("Unknown")


def test_forecast_uses_the_local_timezone_of_the_southern_hemisphere(connect) -> None:
    """Sydney (-33.87, 151.21) is in Australia/Sydney; one day is returned for days=1."""
    with connect("open_meteo") as client:
        result = client.call_tool(
            "open_meteo_forecast", {"latitude": -33.87, "longitude": 151.21, "days": 1}
        )
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["timezone"] == "Australia/Sydney"
    assert data["returned"] == 1
    assert data["latitude"] == pytest.approx(-33.87, abs=0.2)


def test_geocode_finds_berlin_germany_first(connect) -> None:
    """Berlin, Germany is the best match for 'Berlin' with its documented coordinates."""
    with connect("open_meteo") as client:
        result = client.call_tool("open_meteo_geocode", {"name": "Berlin", "count": 2})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["returned"] == len(data["places"]) == 2
    top = data["places"][0]
    assert top["name"] == "Berlin"
    assert top["country"] == "Germany"
    assert top["country_code"] == "DE"
    assert top["latitude"] == pytest.approx(52.52, abs=0.1)
    assert top["longitude"] == pytest.approx(13.41, abs=0.1)
    assert top["timezone"] == "Europe/Berlin"
    assert top["population"] > 3_000_000


def test_geocode_with_no_match_returns_an_empty_list_not_an_error(connect) -> None:
    """An unknown place name is a normal empty result (the API omits 'results')."""
    with connect("open_meteo") as client:
        result = client.call_tool("open_meteo_geocode", {"name": "Zzzqqxx"})
    assert result.is_error is False, result_text(result)
    assert result.structured_content["returned"] == 0
    assert list(result.structured_content["places"]) == []


@pytest.mark.parametrize(
    ("code", "label"),
    [
        (0, "Clear sky"),
        (3, "Overcast"),
        (61, "Slight rain"),
        (71, "Slight snow fall"),
        (95, "Thunderstorm"),
        (99, "Thunderstorm with heavy hail"),
        (1234, "Unknown (code 1234)"),
    ],
)
def test_weather_codes_map_to_the_wmo_labels(code, label) -> None:
    """The WMO interpretation table from the Open-Meteo docs."""
    assert weather_label(code) == label


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        ("open_meteo_forecast", {"latitude": 95, "longitude": 0}, "latitude must be between"),
        ("open_meteo_forecast", {"latitude": 0, "longitude": 181}, "longitude must be"),
        ("open_meteo_forecast", {"latitude": 0, "longitude": 0, "days": 17}, "days must be"),
        ("open_meteo_geocode", {"name": " "}, "name must not be empty"),
        ("open_meteo_geocode", {"name": "x", "count": 11}, "count must be between 1 and 10"),
    ],
)
def test_invalid_input_is_rejected_before_any_request(connect, tool, arguments, message) -> None:
    """Out-of-range arguments are is_error results with a fix-it message; no cassette needed."""
    with connect("open_meteo") as client:
        result = client.call_tool(tool, arguments)
    assert result.is_error is True
    assert message in result_text(result)


@pytest.mark.live
def test_live_forecast_hits_the_real_api(connect) -> None:
    """Smoke test against the real Open-Meteo API (excluded from PR CI)."""
    with connect("open_meteo", mode="live") as client:
        result = client.call_tool(
            "open_meteo_forecast", {"latitude": 52.52, "longitude": 13.41, "days": 1}
        )
    assert result.is_error is False, result_text(result)
    assert result.structured_content["returned"] == 1
