import { scanFrame } from "@/lib/api";
import type { VisionProvider } from "./types";

export function createBackendVisionProvider(): VisionProvider {
  return {
    source: "backend_yolo",
    detect: scanFrame,
  };
}

