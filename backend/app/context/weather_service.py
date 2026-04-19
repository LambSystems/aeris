from urllib.parse import urlencode

from app.context.http import get_json
from app.context.schemas import AirQualityContext, WeatherAlert, WeatherContext


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_GOV_ALERTS_URL = "https://api.weather.gov/alerts/active"


def load_weather(latitude: float, longitude: float) -> WeatherContext:
    params = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "precipitation",
                    "rain",
                    "weather_code",
                    "wind_speed_10m",
                    "wind_gusts_10m",
                ]
            ),
            "timezone": "auto",
        }
    )
    payload = get_json(f"{OPEN_METEO_FORECAST_URL}?{params}")
    current = payload.get("current", {})
    return WeatherContext(
        temperature_c=_float(current.get("temperature_2m")),
        relative_humidity=_float(current.get("relative_humidity_2m")),
        precipitation_mm=_float(current.get("precipitation")),
        rain_mm=_float(current.get("rain")),
        weather_code=_int(current.get("weather_code")),
        wind_speed_kmh=_float(current.get("wind_speed_10m")),
        wind_gusts_kmh=_float(current.get("wind_gusts_10m")),
    )


def load_air_quality(latitude: float, longitude: float) -> AirQualityContext:
    params = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(
                [
                    "pm10",
                    "pm2_5",
                    "carbon_monoxide",
                    "nitrogen_dioxide",
                    "sulphur_dioxide",
                    "ozone",
                    "uv_index",
                ]
            ),
            "timezone": "auto",
        }
    )
    payload = get_json(f"{OPEN_METEO_AIR_QUALITY_URL}?{params}")
    current = payload.get("current", {})
    return AirQualityContext(
        pm10_ug_m3=_float(current.get("pm10")),
        pm2_5_ug_m3=_float(current.get("pm2_5")),
        carbon_monoxide_ug_m3=_float(current.get("carbon_monoxide")),
        nitrogen_dioxide_ug_m3=_float(current.get("nitrogen_dioxide")),
        sulphur_dioxide_ug_m3=_float(current.get("sulphur_dioxide")),
        ozone_ug_m3=_float(current.get("ozone")),
        uv_index=_float(current.get("uv_index")),
    )


def load_weather_alerts(latitude: float, longitude: float) -> list[WeatherAlert]:
    params = urlencode({"point": f"{latitude:.4f},{longitude:.4f}"})
    payload = get_json(f"{WEATHER_GOV_ALERTS_URL}?{params}")
    alerts: list[WeatherAlert] = []
    for feature in payload.get("features", [])[:3]:
        properties = feature.get("properties", {})
        event = properties.get("event")
        if not event:
            continue
        alerts.append(
            WeatherAlert(
                event=str(event),
                severity=properties.get("severity"),
                urgency=properties.get("urgency"),
                headline=properties.get("headline"),
            )
        )
    return alerts


def _float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
