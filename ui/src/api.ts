import type { DynamicContext, FixedContext, LocationState, SceneObject, SustainabilityAdvice } from "./types";

const DEFAULT_API_BASE_URL =
  typeof window === "undefined" ? "http://localhost:8000" : `${window.location.protocol}//${window.location.hostname}:8000`;
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status}: ${body.slice(0, 240)}`);
  }

  return (await response.json()) as T;
}

export async function getHealth(): Promise<{ ok: boolean; service: string }> {
  return requestJson("/health");
}

export async function getFixedContext(location: LocationState): Promise<FixedContext> {
  const params = new URLSearchParams({
    latitude: String(location.latitude),
    longitude: String(location.longitude),
  });
  return requestJson(`/context/fixed?${params.toString()}`);
}

export async function scanFrame(blob: Blob): Promise<DynamicContext> {
  const body = new FormData();
  body.append("file", blob, "frame.jpg");
  return requestJson("/scan-frame", {
    method: "POST",
    body,
  });
}

export async function getAdvice(location: LocationState, object: SceneObject): Promise<SustainabilityAdvice> {
  return requestJson("/sustainability/detect", {
    method: "POST",
    body: JSON.stringify({
      latitude: location.latitude,
      longitude: location.longitude,
      detection: {
        object_class: object.name,
        confidence: object.confidence,
        frame_id: `frame_${Date.now()}`,
        timestamp: new Date().toISOString(),
        bbox: object.bbox,
      },
    }),
  });
}

export function apiBaseUrl(): string {
  return API_BASE_URL;
}
