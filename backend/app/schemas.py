from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]
RiskMode = Literal["protect_plants_and_sensitive_equipment", "general_outdoor_protection"]
ActionType = Literal["protect_first", "move_to_storage", "cover_if_time_allows", "low_priority"]
AnalysisStatus = Literal["pending", "complete", "failed"]
DecisionProvider = Literal["gemini", "openai", "anthropic", "template"]
DecisionSource = Literal[
    "agentic_gemini",
    "agentic_openai",
    "agentic_anthropic",
    "fallback_policy",
]


class PollutionProfile(BaseModel):
    ozone_risk: RiskLevel
    deposition_risk: RiskLevel


class FixedContext(BaseModel):
    location: str
    castnet_site: str
    pollution_profile: PollutionProfile
    risk_mode: RiskMode
    summary: str


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class SceneObject(BaseModel):
    name: str
    confidence: float = Field(ge=0, le=1)
    distance: float = Field(ge=0)
    reachable: bool = True
    bbox: BoundingBox | None = None


class DynamicContext(BaseModel):
    """Normalized scene snapshot consumed by agent analysis."""

    objects: list[SceneObject]
    source: str = "fixture"
    frame_width: int | None = None
    frame_height: int | None = None


class RecommendationRequest(BaseModel):
    fixed_context: FixedContext
    dynamic_context: DynamicContext


class ActionRecommendation(BaseModel):
    rank: int
    action: ActionType
    target: str
    score: float | None = None
    reason_tags: list[str]
    reason: str


class RecommendationOutput(BaseModel):
    decision_source: DecisionSource = "fallback_policy"
    actions: list[ActionRecommendation]
    explanation: str
    missing_insights: list[str] = []


class AnalyzeSceneRequest(BaseModel):
    fixed_context: FixedContext | None = None
    dynamic_context: DynamicContext
    provider: DecisionProvider = "gemini"


class AnalysisJobResponse(BaseModel):
    job_id: str
    status: AnalysisStatus
    recommendations: RecommendationOutput | None = None
    error: str | None = None


class LatestAnalysisResponse(BaseModel):
    has_result: bool
    job: AnalysisJobResponse | None = None


class ExplanationRequest(BaseModel):
    fixed_context: FixedContext
    dynamic_context: DynamicContext
    actions: list[ActionRecommendation]
    missing_insights: list[str] = []
    provider: DecisionProvider = "gemini"


class ExplanationOutput(BaseModel):
    explanation: str
    provider: DecisionProvider
    fallback_used: bool = False


class DemoRunRequest(BaseModel):
    scene: Literal["demo", "after_move"] = "demo"
    use_llm: bool = False


class DemoRunResponse(BaseModel):
    fixed_context: FixedContext
    dynamic_context: DynamicContext
    recommendations: RecommendationOutput


class HealthResponse(BaseModel):
    ok: bool
    service: str
