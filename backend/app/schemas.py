from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]
RiskMode = Literal["protect_plants_and_sensitive_equipment", "general_outdoor_protection"]
ActionType = Literal["protect_first", "move_to_storage", "cover_if_time_allows", "low_priority"]


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
    objects: list[SceneObject]
    source: str = "fixture"


class RecommendationRequest(BaseModel):
    fixed_context: FixedContext
    dynamic_context: DynamicContext


class ActionRecommendation(BaseModel):
    rank: int
    action: ActionType
    target: str
    score: float
    reason_tags: list[str]
    reason: str


class RecommendationOutput(BaseModel):
    actions: list[ActionRecommendation]
    explanation: str
    missing_insights: list[str] = []


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

