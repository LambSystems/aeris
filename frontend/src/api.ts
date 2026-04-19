import { mockDemoResponse } from "./mock";
import type {
  AnalysisJobResponse,
  AnalyzeSceneRequest,
  DemoRunResponse,
  DynamicContext,
  LatestAnalysisResponse,
  YoloConfigResponse,
} from "./types/aeris";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface ScanFrameOptions {
  frame?: Blob;
  imageWidth?: number;
  imageHeight?: number;
  confidenceThreshold?: number;
  imageSize?: number;
}

export async function runDemo(scene: "demo" | "after_move" = "demo"): Promise<DemoRunResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/demo/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ scene }),
    });

    if (!response.ok) {
      throw new Error(`Aeris API returned ${response.status}`);
    }

    return (await response.json()) as DemoRunResponse;
  } catch (error) {
    console.warn("Using frontend mock data because the backend is unavailable.", error);
    return scene === "after_move"
      ? {
          ...mockDemoResponse,
          dynamic_context: {
            ...mockDemoResponse.dynamic_context,
            source: "frontend_mock_after_move",
            objects: mockDemoResponse.dynamic_context.objects.filter((object) => object.name !== "battery_pack"),
          },
          recommendations: {
            ...mockDemoResponse.recommendations,
            explanation:
              "Scene updated. The battery pack is no longer visible, so Aeris keeps the seed tray as the first protection target and elevates protection-enabling items like the tarp.",
          },
        }
      : mockDemoResponse;
  }
}

export async function scanFrame(options: ScanFrameOptions = {}): Promise<DynamicContext> {
  const body = new FormData();

  if (options.frame) {
    body.append("frame", options.frame);
  }
  if (options.imageWidth) {
    body.append("image_width", String(options.imageWidth));
  }
  if (options.imageHeight) {
    body.append("image_height", String(options.imageHeight));
  }
  if (options.confidenceThreshold !== undefined) {
    body.append("confidence_threshold", String(options.confidenceThreshold));
  }
  if (options.imageSize !== undefined) {
    body.append("image_size", String(options.imageSize));
  }

  const response = await fetch(`${API_BASE_URL}/scan-frame`, {
    method: "POST",
    body: options.frame ? body : undefined,
  });

  if (!response.ok) {
    throw new Error(`Aeris scan API returned ${response.status}`);
  }

  return (await response.json()) as DynamicContext;
}

export async function getYoloConfig(): Promise<YoloConfigResponse> {
  const response = await fetch(`${API_BASE_URL}/scan-frame/config`);

  if (!response.ok) {
    throw new Error(`Aeris YOLO config API returned ${response.status}`);
  }

  return (await response.json()) as YoloConfigResponse;
}

export async function analyzeScene(request: AnalyzeSceneRequest): Promise<AnalysisJobResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze-scene`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Aeris analysis API returned ${response.status}`);
  }

  return (await response.json()) as AnalysisJobResponse;
}

export async function getAnalysisJob(jobId: string): Promise<AnalysisJobResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/${jobId}`);

  if (!response.ok) {
    throw new Error(`Aeris analysis job API returned ${response.status}`);
  }

  return (await response.json()) as AnalysisJobResponse;
}

export async function getLatestAnalysis(): Promise<LatestAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/latest`);

  if (!response.ok) {
    throw new Error(`Aeris latest analysis API returned ${response.status}`);
  }

  return (await response.json()) as LatestAnalysisResponse;
}
