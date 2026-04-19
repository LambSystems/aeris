import type {
  FixedContextResponse,
  ScanFrameResponse,
  SustainabilityRequest,
  SustainabilityResponse,
} from "./types";

// Read API base from env, default to relative (works behind proxy).
// Stored only here so the rest of the app stays clean.
const API_BASE: string =
  (import.meta.env.VITE_AERIS_API_BASE as string | undefined)?.replace(/\/$/, "") ??
  "";

export function getApiBase(): string {
  return API_BASE || window.location.origin;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} ${res.status}`);
  return (await res.json()) as T;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${path} ${res.status}`);
  return (await res.json()) as T;
}

export async function scanFrame(blob: Blob): Promise<ScanFrameResponse> {
  // Backend accepts JSON with base64 image. Convert blob -> base64 data URL.
  const dataUrl = await blobToDataUrl(blob);
  return postJson<ScanFrameResponse>("/scan-frame", { image: dataUrl });
}

export async function getFixedContext(
  latitude: number,
  longitude: number,
): Promise<FixedContextResponse> {
  const qs = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
  });
  return getJson<FixedContextResponse>(`/context/fixed?${qs.toString()}`);
}

export async function detectSustainability(
  payload: SustainabilityRequest,
): Promise<SustainabilityResponse> {
  return postJson<SustainabilityResponse>("/sustainability/detect", payload);
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result as string);
    r.onerror = reject;
    r.readAsDataURL(blob);
  });
}
