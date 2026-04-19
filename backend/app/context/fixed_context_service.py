import time

from app.context.risk_flags import build_risk_flags, build_summary
from app.context.schemas import EnvironmentalFixedContext, LocationContext
from app.context.weather_service import load_air_quality, load_weather, load_weather_alerts
from app.sustainability.castnet_service import load_castnet


DEFAULT_LATITUDE = 40.9478
DEFAULT_LONGITUDE = -90.3712
DEFAULT_LOCATION_LABEL = "Galesburg, IL"
DEFAULT_TTL_SECONDS = 600

_cache: dict[str, tuple[float, EnvironmentalFixedContext]] = {}


def load_fixed_context(
    latitude: float | None = None,
    longitude: float | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> EnvironmentalFixedContext:
    lat = latitude if latitude is not None else DEFAULT_LATITUDE
    lon = longitude if longitude is not None else DEFAULT_LONGITUDE
    cache_key = _cache_key(lat, lon)
    now = time.time()

    cached = _cache.get(cache_key)
    if cached and now - cached[0] < ttl_seconds:
        return cached[1]

    source_status: dict[str, str] = {}
    castnet = load_castnet()
    source_status["castnet"] = "ok"

    weather = None
    try:
        weather = load_weather(lat, lon)
        source_status["weather"] = "ok"
    except Exception as error:
        source_status["weather"] = f"fallback:{type(error).__name__}"

    air_quality = None
    try:
        air_quality = load_air_quality(lat, lon)
        source_status["air_quality"] = "ok"
    except Exception as error:
        source_status["air_quality"] = f"fallback:{type(error).__name__}"

    weather_alerts = []
    try:
        weather_alerts = load_weather_alerts(lat, lon)
        source_status["weather_alerts"] = "ok"
    except Exception as error:
        source_status["weather_alerts"] = f"fallback:{type(error).__name__}"

    context = EnvironmentalFixedContext(
        location=LocationContext(
            latitude=lat,
            longitude=lon,
            label=DEFAULT_LOCATION_LABEL if latitude is None or longitude is None else f"{lat:.4f},{lon:.4f}",
            source="default_demo_location" if latitude is None or longitude is None else "browser_gps",
        ),
        castnet=castnet,
        weather=weather,
        air_quality=air_quality,
        weather_alerts=weather_alerts,
        risk_flags=build_risk_flags(castnet, weather, air_quality, len(weather_alerts)),
        summary="",
        source_status=source_status,
    )
    context = context.model_copy(update={"summary": build_summary(context)})
    _cache[cache_key] = (now, context)
    return context


def _cache_key(latitude: float, longitude: float) -> str:
    return f"{latitude:.2f}:{longitude:.2f}"
