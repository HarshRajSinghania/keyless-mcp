---
title: "Add a National Weather Service adapter for US forecasts and alerts"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:geo"]
---

The US National Weather Service publishes forecasts and active alerts for free. Open-Meteo covers the whole world, and this adds the official US forecast text and severe-weather alerts, which are what people usually want to quote.

## API

- Docs: https://www.weather.gov/documentation/services-web-api
- Base URL: `https://api.weather.gov`
- It works without a key, token or account.
- Suggested adapter name: `nws`, in the `geo` toolset.

## Proposed tools

### `nws_get_forecast(latitude: float, longitude: float)`

Get the multi-day forecast for a US location. Returns each period's name, temperature, wind, short forecast and detailed forecast.

### `nws_get_active_alerts(state: str)`

List active watches, warnings and advisories for a US state or territory given its two-letter code, with event type, severity, headline and affected area.

## Example

```text
GET https://api.weather.gov/points/39.7456,-97.0892 then the URL in `properties.forecast`
```

Fields worth returning: The `/points/{lat},{lon}` response has `properties.gridId`, `gridX`, `gridY` and `forecast` (a URL). The forecast response has `properties.periods[]` with `name`, `startTime`, `isDaytime`, `temperature`, `temperatureUnit`, `windSpeed`, `windDirection`, `shortForecast`, `detailedForecast` and `probabilityOfPrecipitation.value`. Alerts come back as a GeoJSON `features[]` list.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=nws TOOLSET=geo`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a point outside the US (`/points/48.8566,2.3522`) returns a 404 titled `Data Unavailable For Requested Point`. Turn it into an `InvalidInput` that says the service covers the US only.
- [ ] `make record ADAPTER=nws` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- A forecast takes two requests: one for the point and one for the forecast URL it returns. Both need a cassette.
- Coordinates with more than four decimal places get a 301 redirect to the four-decimal URL. Round before you build the URL, so the cassette is keyed by the address you mean.
- The alerts endpoint rejected a `limit` parameter with a 400 when this issue was written. Trim the list in the adapter instead.
- Alert text can be long. Use `truncate`.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
