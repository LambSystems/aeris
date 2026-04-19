import { createBackendVisionProvider } from "./backendVisionProvider";
import { createBrowserYoloProvider } from "./browserYoloProvider";
import type { VisionProvider } from "./types";

export async function createPreferredVisionProvider(): Promise<VisionProvider> {
  const preferred = import.meta.env.VITE_VISION_PROVIDER ?? "browser";
  if (preferred !== "backend") {
    try {
      return await createBrowserYoloProvider();
    } catch (error) {
      console.warn("Browser YOLO unavailable; falling back to backend YOLO.", error);
    }
  }
  return createBackendVisionProvider();
}

export type { VisionProviderSource } from "./types";

