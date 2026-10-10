"""Open-Meteo tools: a daily forecast for coordinates and a geocoder that finds the coordinates."""

from typing import Annotated, Any

from pydantic import Field

from keyless_mcp.core import AdapterHttp, InvalidInput, ToolRegistry

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
MAX_DAYS = 16
MAX_COUNT = 10

# WMO weather interpretation codes as used by Open-Meteo (https://open-meteo.com/en/docs).
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def weather_label(code: int | None) -> str | None:
    """Human-readable label for a WMO weather code."""
    if code is None:
        return None
    return WEATHER_CODES.get(code, f"Unknown (code {code})")


def register(tools: ToolRegistry, http: AdapterHttp) -> None:
    @tools.tool(title="Get weather forecast")
    async def open_meteo_forecast(
        latitude: Annotated[
            float,
            Field(description="Latitude in decimal degrees, -90 to 90, e.g. 52.52 for Berlin."),
        ],
        longitude: Annotated[
            float,
            Field(description="Longitude in decimal degrees, -180 to 180, e.g. 13.41 for Berlin."),
        ],
        days: Annotated[
            int,
            Field(description=f"Forecast days starting today, 1 to {MAX_DAYS}. Default 3."),
        ] = 3,
    ) -> dict[str, Any]:
        """Get a daily weather forecast for a location: for each day the maximum and minimum
        temperature (degrees Celsius), total precipitation (mm) and the weather condition as a
        WMO code with a plain-language label. Dates use the location's local time zone. Use
        open_meteo_geocode first to turn a place name into coordinates."""
        if not -90 <= latitude <= 90:
            raise InvalidInput("latitude must be between -90 and 90.")
        if not -180 <= longitude <= 180:
            raise InvalidInput("longitude must be between -180 and 180.")
        if not 1 <= days <= MAX_DAYS:
            raise InvalidInput(f"days must be between 1 and {MAX_DAYS}.")
        data = await http.get_json(
            FORECAST_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                "timezone": "auto",
                "forecast_days": days,
            },
        )
        daily = data["daily"]
        units = data.get("daily_units") or {}
        forecast = []
        for i, date in enumerate(daily["time"]):
            code = daily["weathercode"][i]
            forecast.append(
                {
                    "date": date,
                    "temp_max": daily["temperature_2m_max"][i],
                    "temp_min": daily["temperature_2m_min"][i],
                    "precipitation_mm": daily["precipitation_sum"][i],
                    "weather_code": code,
                    "weather": weather_label(code),
                }
            )
        return {
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "elevation_m": data.get("elevation"),
            "timezone": data.get("timezone"),
            "temperature_unit": units.get("temperature_2m_max", "°C"),
            "returned": len(forecast),
            "days": forecast,
            "source": "https://open-meteo.com/",
        }

    @tools.tool(title="Find place coordinates")
    async def open_meteo_geocode(
        name: Annotated[
            str,
            Field(
                description="Place name to look up, e.g. 'Berlin', 'Springfield' or 'Kyoto'. "
                "City or town names work best; a postal code also works."
            ),
        ],
        count: Annotated[
            int,
            Field(description=f"Maximum number of matching places, 1 to {MAX_COUNT}. Default 5."),
        ] = 5,
    ) -> dict[str, Any]:
        """Find places by name and get their coordinates. Returns up to `count` matches, best
        first, each with latitude, longitude, country, region, elevation, time zone and
        population. Ambiguous names (Springfield) return several places; pick by country and
        region, then pass the coordinates to open_meteo_forecast."""
        if not name.strip():
            raise InvalidInput("name must not be empty.")
        if not 1 <= count <= MAX_COUNT:
            raise InvalidInput(f"count must be between 1 and {MAX_COUNT}.")
        params = {"name": name.strip(), "count": count, "language": "en", "format": "json"}
        data = await http.get_json(GEOCODING_URL, params)
        places = data.get("results") or []  # the key is absent when nothing matched
        return {
            "query": name.strip(),
            "returned": len(places),
            "places": [
                {
                    "name": place["name"],
                    "country": place.get("country"),
                    "country_code": place.get("country_code"),
                    "region": place.get("admin1"),
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "elevation_m": place.get("elevation"),
                    "timezone": place.get("timezone"),
                    "population": place.get("population"),
                }
                for place in places
            ],
        }
