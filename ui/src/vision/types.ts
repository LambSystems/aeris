import type { ScanFrameResponse } from "@/lib/types";

export type VisionProviderSource = "browser_yolo" | "backend_yolo";

export interface VisionProvider {
  readonly source: VisionProviderSource;
  detect(blob: Blob): Promise<ScanFrameResponse>;
  dispose?(): Promise<void> | void;
}

