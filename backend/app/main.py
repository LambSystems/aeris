from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cv.yolo_service import scan_demo_frame
from app.data import load_demo_context, load_scene
from app.policy import rank_recommendations
from app.schemas import (
    DemoRunRequest,
    DemoRunResponse,
    DynamicContext,
    FixedContext,
    HealthResponse,
    RecommendationOutput,
    RecommendationRequest,
)


app = FastAPI(
    title="Aeris API",
    description="Backend API for CASTNET-driven outdoor resource protection recommendations.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True, service="aeris-api")


@app.get("/context/demo", response_model=FixedContext)
def get_demo_context() -> FixedContext:
    return load_demo_context()


@app.get("/scene/demo", response_model=DynamicContext)
def get_demo_scene() -> DynamicContext:
    return load_scene("demo")


@app.get("/scene/demo-after-move", response_model=DynamicContext)
def get_demo_scene_after_move() -> DynamicContext:
    return load_scene("after_move")


@app.post("/recommend", response_model=RecommendationOutput)
def recommend(request: RecommendationRequest) -> RecommendationOutput:
    return rank_recommendations(request.fixed_context, request.dynamic_context)


@app.post("/demo/run", response_model=DemoRunResponse)
def run_demo(request: Optional[DemoRunRequest] = None) -> DemoRunResponse:
    scene_key = request.scene if request else "demo"
    fixed_context = load_demo_context()
    dynamic_context = load_scene(scene_key)
    recommendations = rank_recommendations(fixed_context, dynamic_context)

    return DemoRunResponse(
        fixed_context=fixed_context,
        dynamic_context=dynamic_context,
        recommendations=recommendations,
    )


@app.post("/scan", response_model=DynamicContext)
def scan_scene() -> DynamicContext:
    return scan_demo_frame()

