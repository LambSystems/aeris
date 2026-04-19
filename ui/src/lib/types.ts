export interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DetectedObject {
  name: string;
  confidence: number;
  distance?: number;
  reachable?: boolean;
  bbox: BBox;
}

export interface ScanFrameResponse {
  objects: DetectedObject[];
  source: string;
  frame_width: number;
  frame_height: number;
}

export interface CastnetData {
  site_id?: string;
  location?: string;
  ozone_ppb?: number;
  sulfate_ug_m3?: number;
  nitrate_ug_m3?: number;
  co_ppb?: number;
  measurement_date?: string;
}

export interface WeatherData {
  temperature_c?: number | null;
  relative_humidity?: number | null;
  precipitation_mm?: number | null;
  rain_mm?: number | null;
  weather_code?: number | null;
  wind_speed_kmh?: number | null;
  wind_gusts_kmh?: number | null;
  source?: string;
}

export interface AirQualityData {
  pm2_5_ug_m3?: number | null;
  pm10_ug_m3?: number | null;
  ozone_ug_m3?: number | null;
  uv_index?: number | null;
  [k: string]: number | string | null | undefined;
}

export interface WeatherAlert {
  event?: string;
  headline?: string;
  severity?: string;
  [k: string]: unknown;
}

export interface FixedContextResponse {
  location?: { latitude?: number; longitude?: number; name?: string };
  castnet?: CastnetData;
  weather?: WeatherData;
  air_quality?: AirQualityData;
  weather_alerts?: WeatherAlert[];
  risk_flags?: string[];
  summary?: string;
  source_status?: Record<string, string>;
}

export interface SustainabilityRequest {
  latitude: number;
  longitude: number;
  detection: {
    object_class: string;
    confidence: number;
    frame_id: string;
    timestamp: string;
    bbox: BBox;
  };
}

export interface SustainabilityResponse {
  object_detected: string;
  confidence: number;
  context: string;
  action: string;
  environment_summary: string;
  risk_flags: string[];
  castnet_site?: string;
  decision_source?: string;
}
