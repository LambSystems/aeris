// Human-readable label helpers.

export function formatObjectName(raw: string): string {
  if (!raw) return "Unknown object";
  return raw
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

const RISK_LABELS: Record<string, string> = {
  castnet_elevated_nitrate: "Elevated nitrate",
  castnet_elevated_ozone: "Elevated ozone",
  castnet_elevated_sulfate: "Elevated sulfate",
  weather_alert_active: "Active weather alert",
  high_uv: "High UV",
  high_pm25: "High PM2.5",
  high_pm10: "High PM10",
  rain_active: "Rain in area",
  high_wind: "High winds",
};

export function formatRiskFlag(flag: string): string {
  if (RISK_LABELS[flag]) return RISK_LABELS[flag];
  return flag
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatConfidence(c: number): string {
  return `${Math.round(c * 100)}%`;
}

export function formatNumber(
  v: number | undefined | null,
  digits = 1,
  unit = "",
): string {
  if (v === undefined || v === null || Number.isNaN(v)) return "—";
  return `${v.toFixed(digits)}${unit ? ` ${unit}` : ""}`;
}
