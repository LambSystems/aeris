import type { DemoRunResponse } from "./types/aeris";

export const mockDemoResponse: DemoRunResponse = {
  fixed_context: {
    location: "Outdoor Garden Demo",
    castnet_site: "Demo CASTNET Profile",
    pollution_profile: {
      ozone_risk: "high",
      deposition_risk: "medium",
    },
    risk_mode: "protect_plants_and_sensitive_equipment",
    summary: "Elevated ozone and environmental exposure conditions for outdoor plants and sensitive equipment.",
  },
  dynamic_context: {
    source: "frontend_mock",
    objects: [
      {
        name: "seed_tray",
        confidence: 0.94,
        distance: 1,
        reachable: true,
        bbox: { x: 92, y: 112, width: 190, height: 126 },
      },
      {
        name: "battery_pack",
        confidence: 0.89,
        distance: 1.6,
        reachable: true,
        bbox: { x: 338, y: 158, width: 126, height: 82 },
      },
      {
        name: "metal_tool",
        confidence: 0.84,
        distance: 2.1,
        reachable: true,
        bbox: { x: 508, y: 244, width: 142, height: 48 },
      },
      {
        name: "tarp",
        confidence: 0.82,
        distance: 1.3,
        reachable: true,
        bbox: { x: 560, y: 82, width: 170, height: 112 },
      },
      {
        name: "storage_bin",
        confidence: 0.78,
        distance: 1.8,
        reachable: true,
        bbox: { x: 728, y: 198, width: 150, height: 118 },
      },
    ],
  },
  recommendations: {
    decision_source: "fallback_policy",
    actions: [
      {
        rank: 1,
        action: "protect_first",
        target: "seed_tray",
        score: 10.97,
        reason_tags: ["plant_sensitive", "high_ozone_context", "reachable", "nearby"],
        reason: "Plant-sensitive resource under elevated ozone context.",
      },
      {
        rank: 2,
        action: "move_to_storage",
        target: "battery_pack",
        score: 9.36,
        reason_tags: ["sensitive_equipment", "high_ozone_context", "reachable"],
        reason: "Sensitive equipment should be moved out of exposure.",
      },
      {
        rank: 3,
        action: "cover_if_time_allows",
        target: "tarp",
        score: 8.97,
        reason_tags: ["protection_enabler", "high_ozone_context", "reachable", "nearby"],
        reason: "Protection-enabling item can reduce exposure for nearby resources.",
      },
    ],
    explanation:
      "CASTNET-derived context indicates protect plants and sensitive equipment. Aeris ranks seed tray first because plant-sensitive resource under elevated ozone context. Next, battery pack should be move to storage because sensitive equipment should be moved out of exposure. Tarp is also relevant as a cover if time allows action.",
    missing_insights: [],
  },
};
