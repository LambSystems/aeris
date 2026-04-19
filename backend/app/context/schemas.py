from pydantic import BaseModel, Field

from app.sustainability.schemas import CASTNETReading


class LocationContext(BaseModel):
    latitude: float
    longitude: float
    label: str
    source: str = "browser_gps"


class WeatherContext(BaseModel):
    temperature_c: float | None = None
    relative_humidity: float | None = None
    precipitation_mm: float | None = None
    rain_mm: float | None = None
    weather_code: int | None = None
    wind_speed_kmh: float | None = None
    wind_gusts_kmh: float | None = None
    source: str = "open_meteo"


class AirQualityContext(BaseModel):
    pm10_ug_m3: float | None = None
    pm2_5_ug_m3: float | None = None
    carbon_monoxide_ug_m3: float | None = None
    nitrogen_dioxide_ug_m3: float | None = None
    sulphur_dioxide_ug_m3: float | None = None
    ozone_ug_m3: float | None = None
    uv_index: float | None = None
    source: str = "open_meteo"


class WeatherAlert(BaseModel):
    event: str
    severity: str | None = None
    urgency: str | None = None
    headline: str | None = None


class EnvironmentalFixedContext(BaseModel):
    location: LocationContext
    castnet: CASTNETReading
    weather: WeatherContext | None = None
    air_quality: AirQualityContext | None = None
    weather_alerts: list[WeatherAlert] = []
    risk_flags: list[str] = Field(default_factory=list)
    summary: str
    source_status: dict[str, str] = Field(default_factory=dict)
