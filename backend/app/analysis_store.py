from threading import Lock
from uuid import uuid4

from app.agent_decision import generate_agentic_recommendations
from app.schemas import (
    AnalysisJobResponse,
    AnalyzeSceneRequest,
    FixedContext,
    LatestAnalysisResponse,
)


_jobs: dict[str, AnalysisJobResponse] = {}
_latest_completed_job_id: str | None = None
_lock = Lock()


def create_analysis_job(request: AnalyzeSceneRequest, fixed_context: FixedContext) -> AnalysisJobResponse:
    job = AnalysisJobResponse(job_id=str(uuid4()), status="pending")
    with _lock:
        _jobs[job.job_id] = job

    return job


def run_analysis_job(job_id: str, request: AnalyzeSceneRequest, fixed_context: FixedContext) -> None:
    global _latest_completed_job_id

    try:
        recommendations = generate_agentic_recommendations(
            fixed_context=fixed_context,
            dynamic_context=request.dynamic_context,
            provider=request.provider,
        )
        completed = AnalysisJobResponse(
            job_id=job_id,
            status="complete",
            recommendations=recommendations,
        )
        with _lock:
            _jobs[job_id] = completed
            _latest_completed_job_id = job_id
    except Exception as error:
        failed = AnalysisJobResponse(
            job_id=job_id,
            status="failed",
            error=str(error),
        )
        with _lock:
            _jobs[job_id] = failed


def get_analysis_job(job_id: str) -> AnalysisJobResponse | None:
    with _lock:
        return _jobs.get(job_id)


def get_latest_analysis() -> LatestAnalysisResponse:
    with _lock:
        if _latest_completed_job_id is None:
            return LatestAnalysisResponse(has_result=False)
        return LatestAnalysisResponse(has_result=True, job=_jobs[_latest_completed_job_id])

