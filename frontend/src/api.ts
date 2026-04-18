import { mockDemoResponse } from "./mock";
import type { DemoRunResponse } from "./types/aeris";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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

