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
  decision_source: "agentic_gemini" | "agentic_openai" | "fallback_policy";
  actions: ActionRecommendation[];
  explanation: string;
  missing_insights: string[];
}

export interface AnalyzeSceneRequest {
  fixed_context?: FixedContext;
  dynamic_context: DynamicContext;
  provider?: "gemini" | "openai" | "template";
}

export interface AnalysisJobResponse {
  job_id: string;
  status: "pending" | "complete" | "failed";
  recommendations?: RecommendationOutput | null;
  error?: string | null;
}

export interface LatestAnalysisResponse {
  has_result: boolean;
  job?: AnalysisJobResponse | null;
}

export interface ExplanationRequest {
  fixed_context: FixedContext;
  dynamic_context: DynamicContext;
  actions: ActionRecommendation[];
  missing_insights: string[];
  provider?: "gemini" | "openai" | "template";
}

export interface ExplanationOutput {
  explanation: string;
  provider: "gemini" | "openai" | "template";
  fallback_used: boolean;
}

export interface DemoRunResponse {
  fixed_context: FixedContext;
  dynamic_context: DynamicContext;
  recommendations: RecommendationOutput;
}
