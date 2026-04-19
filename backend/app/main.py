from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.analysis_store import create_analysis_job, get_analysis_job, get_latest_analysis, run_analysis_job
from app.cv.yolo_service import scan_demo_frame
from app.data import load_demo_context, load_scene
from app.fallback_policy import build_fallback_recommendations
from app.schemas import (
    AnalysisJobResponse,
    AnalyzeSceneRequest,
    DemoRunRequest,
    DemoRunResponse,
    DynamicContext,
    FixedContext,
    HealthResponse,
    LatestAnalysisResponse,
    RecommendationOutput,
    RecommendationRequest,
)
from app.sustainability.adviser import get_sustainability_advice
from app.sustainability.castnet_mock import load_mock_castnet
from app.sustainability.schemas import DetectionRequest, SustainabilityAdvice


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


@app.post("/scan-frame", response_model=DynamicContext)
def scan_frame() -> DynamicContext:
    return scan_demo_frame()


@app.post("/analyze-scene", response_model=AnalysisJobResponse)
def analyze_scene(request: AnalyzeSceneRequest, background_tasks: BackgroundTasks) -> AnalysisJobResponse:
    fixed_context = request.fixed_context or load_demo_context()
    job = create_analysis_job(request, fixed_context)
    background_tasks.add_task(run_analysis_job, job.job_id, request, fixed_context)
    return job


@app.get("/analysis/latest", response_model=LatestAnalysisResponse)
def latest_analysis() -> LatestAnalysisResponse:
    return get_latest_analysis()


@app.get("/analysis/{job_id}", response_model=AnalysisJobResponse)
def analysis_job(job_id: str) -> AnalysisJobResponse:
    job = get_analysis_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return job


@app.post("/recommend", response_model=RecommendationOutput)
def recommend(request: RecommendationRequest) -> RecommendationOutput:
    return build_fallback_recommendations(request.fixed_context, request.dynamic_context)


@app.post("/demo/run", response_model=DemoRunResponse)
def run_demo(request: Optional[DemoRunRequest] = None) -> DemoRunResponse:
    scene_key = request.scene if request else "demo"
    fixed_context = load_demo_context()
    dynamic_context = load_scene(scene_key)
    recommendations = build_fallback_recommendations(fixed_context, dynamic_context)

    return DemoRunResponse(
        fixed_context=fixed_context,
        dynamic_context=dynamic_context,
        recommendations=recommendations,
    )


@app.post("/scan", response_model=DynamicContext)
def scan_scene() -> DynamicContext:
    return scan_demo_frame()


@app.post("/sustainability/detect", response_model=SustainabilityAdvice)
def sustainability_detect(request: DetectionRequest) -> SustainabilityAdvice:
    castnet = load_mock_castnet()
    return get_sustainability_advice(request.detection, castnet)
