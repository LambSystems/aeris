import type {
  FixedContextResponse,
  ScanFrameResponse,
  SustainabilityRequest,
  SustainabilityResponse,
} from "./types";

const DEFAULT_API_BASE =
  typeof window === "undefined" ? "http://localhost:8000" : `${window.location.protocol}//${window.location.hostname}:8000`;
const API_BASE: string = ((import.meta.env.VITE_AERIS_API_BASE as string | undefined) ?? DEFAULT_API_BASE).replace(/\/$/, "");

export function getApiBase(): string {
  return API_BASE;
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
  const body = new FormData();
  body.append("file", blob, "frame.jpg");
  const res = await fetch(`${API_BASE}/scan-frame`, {
    method: "POST",
    body,
  });
  if (!res.ok) throw new Error(`/scan-frame ${res.status}`);
  const result = (await res.json()) as ScanFrameResponse;
  return {
    ...result,
    objects: (result.objects ?? []).filter((object) => object.bbox),
  };
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
