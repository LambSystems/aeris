from app.context.schemas import AirQualityContext, EnvironmentalFixedContext, WeatherContext
from app.sustainability.schemas import CASTNETReading


def build_risk_flags(
    castnet: CASTNETReading,
    weather: WeatherContext | None,
    air_quality: AirQualityContext | None,
    active_alert_count: int,
) -> list[str]:
    flags: list[str] = []

    if castnet.ozone_ppb >= 70:
        flags.append("castnet_high_ozone")
    elif castnet.ozone_ppb >= 50:
        flags.append("castnet_moderate_ozone")

    if castnet.sulfate_ug_m3 >= 2.0:
        flags.append("castnet_elevated_sulfate")
    if castnet.nitrate_ug_m3 >= 2.0:
        flags.append("castnet_elevated_nitrate")

    if weather:
        precipitation = max(weather.precipitation_mm or 0.0, weather.rain_mm or 0.0)
        if precipitation > 0:
            flags.append("rain_can_move_pollutants_to_stormwater")
        if weather.wind_gusts_kmh is not None and weather.wind_gusts_kmh >= 30:
            flags.append("wind_can_spread_litter")
        elif weather.wind_speed_kmh is not None and weather.wind_speed_kmh >= 20:
            flags.append("wind_can_spread_litter")

    if air_quality:
        if air_quality.pm2_5_ug_m3 is not None and air_quality.pm2_5_ug_m3 >= 12:
            flags.append("particle_pollution_context")
        if air_quality.ozone_ug_m3 is not None and air_quality.ozone_ug_m3 >= 100:
            flags.append("modeled_ozone_elevated")
        if air_quality.uv_index is not None and air_quality.uv_index >= 6:
            flags.append("high_uv_plastic_degradation_context")

    if active_alert_count > 0:
        flags.append("weather_alert_active")

    return sorted(set(flags))


def build_summary(context: EnvironmentalFixedContext) -> str:
    pieces = [
        f"Nearest CASTNET context is {context.castnet.location}",
        f"ozone {context.castnet.ozone_ppb:.1f} ppb",
        f"sulfate {context.castnet.sulfate_ug_m3:.2f} ug/m3",
        f"nitrate {context.castnet.nitrate_ug_m3:.2f} ug/m3",
    ]
    if context.weather and context.weather.wind_gusts_kmh is not None:
        pieces.append(f"wind gusts {context.weather.wind_gusts_kmh:.1f} km/h")
    if context.air_quality and context.air_quality.pm2_5_ug_m3 is not None:
        pieces.append(f"PM2.5 {context.air_quality.pm2_5_ug_m3:.1f} ug/m3")
    if context.risk_flags:
        pieces.append(f"active risk flags: {', '.join(context.risk_flags)}")
    return "; ".join(pieces) + "."
