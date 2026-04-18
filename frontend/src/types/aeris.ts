export type RiskLevel = "low" | "medium" | "high";
export type RiskMode = "protect_plants_and_sensitive_equipment" | "general_outdoor_protection";
export type ActionType = "protect_first" | "move_to_storage" | "cover_if_time_allows" | "low_priority";

export interface PollutionProfile {
  ozone_risk: RiskLevel;
  deposition_risk: RiskLevel;
}

export interface FixedContext {
  location: string;
  castnet_site: string;
  pollution_profile: PollutionProfile;
  risk_mode: RiskMode;
  summary: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface SceneObject {
  name: string;
  confidence: number;
  distance: number;
  reachable: boolean;
  bbox?: BoundingBox | null;
}

export interface DynamicContext {
  objects: SceneObject[];
  source: string;
}

export interface ActionRecommendation {
  rank: number;
  action: ActionType;
  target: string;
  score: number;
  reason_tags: string[];
  reason: string;
}

export interface RecommendationOutput {
  actions: ActionRecommendation[];
  explanation: string;
  missing_insights: string[];
}

export interface DemoRunResponse {
  fixed_context: FixedContext;
  dynamic_context: DynamicContext;
  recommendations: RecommendationOutput;
}

