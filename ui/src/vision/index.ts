import { createBackendVisionProvider } from "./backendVisionProvider";
import { createBrowserYoloProvider } from "./browserYoloProvider";
import type { VisionProvider } from "./types";

export async function createPreferredVisionProvider(): Promise<VisionProvider> {
  const preferred = import.meta.env.VITE_VISION_PROVIDER ?? "browser-only";
  if (preferred === "backend") {
    return createBackendVisionProvider();
  }

  try {
    return await createBrowserYoloProvider();
  } catch (error) {
    console.error("Browser YOLO unavailable.", error);
    if (preferred === "browser-only") {
      throw error;
    }
    console.warn("Falling back to backend YOLO.");
    return createBackendVisionProvider();
  }
}

export type { VisionProviderSource } from "./types";
