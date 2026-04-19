export type BoundingBox = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type SceneObject = {
  name: string;
  confidence: number;
  distance: number;
  reachable: boolean;
  bbox: BoundingBox | null;
};

export type DynamicContext = {
  objects: SceneObject[];
  source: string;
  frame_width: number | null;
  frame_height: number | null;
};

export type FixedContext = {
  location: {
    latitude: number;
    longitude: number;
    label: string;
    source: string;
  };
  castnet: {
    site_id: string;
    location: string;
    ozone_ppb: number;
    sulfate_ug_m3: number;
    nitrate_ug_m3: number;
    co_ppb: number;
    measurement_date: string;
  };
  weather: {
    temperature_c: number | null;
    relative_humidity: number | null;
    precipitation_mm: number | null;
    rain_mm: number | null;
    weather_code: number | null;
    wind_speed_kmh: number | null;
    wind_gusts_kmh: number | null;
    source: string;
  } | null;
  air_quality: {
    pm10_ug_m3: number | null;
    pm2_5_ug_m3: number | null;
    carbon_monoxide_ug_m3: number | null;
    nitrogen_dioxide_ug_m3: number | null;
    sulphur_dioxide_ug_m3: number | null;
    ozone_ug_m3: number | null;
    uv_index: number | null;
    source: string;
  } | null;
  weather_alerts: Array<{
    event: string;
    severity: string | null;
    urgency: string | null;
    headline: string | null;
  }>;
  risk_flags: string[];
  summary: string;
  source_status: Record<string, string>;
};

export type SustainabilityAdvice = {
  object_detected: string;
  confidence: number;
  context: string;
  action: string;
  environment_summary: string | null;
  risk_flags: string[];
  castnet_site: string | null;
};

export type LocationState = {
  latitude: number;
  longitude: number;
  label: string;
  source: "browser_gps" | "demo_default";
};
