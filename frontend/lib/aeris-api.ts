/** Typed client for the Aeris FastAPI backend. */

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "")

export type HealthResponse = { ok: boolean; service: string }

export type PollutionProfile = {
  ozone_risk: string
  deposition_risk: string
}

export type FixedContext = {
  location: string
  castnet_site: string
  pollution_profile: PollutionProfile
  risk_mode: string
  summary: string
}

export type BoundingBox = { x: number; y: number; width: number; height: number }

export type SceneObject = {
  name: string
  confidence: number
  distance: number
  reachable: boolean
  bbox: BoundingBox | null
}

export type DynamicContext = {
  objects: SceneObject[]
  source: string
}

export type SustainabilityAdvice = {
  object_detected: string
  confidence: number
  context: string
  action: string
}

export type ActionRecommendation = {
  rank: number
  action: string
  target: string
  score: number | null
  reason_tags: string[]
  reason: string
}

export type RecommendationOutput = {
  decision_source: string
  actions: ActionRecommendation[]
  explanation: string
  missing_insights: string[]
}

export type AnalysisJobResponse = {
  job_id: string
  status: "pending" | "complete" | "failed"
  recommendations: RecommendationOutput | null
  error: string | null
}

export type DecisionProvider = "gemini" | "openai" | "anthropic" | "template"

async function aerisFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body && !(init.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text.slice(0, 200)}`)
  }
  return res.json() as Promise<T>
}

export async function fetchHealth(): Promise<HealthResponse> {
  return aerisFetch<HealthResponse>("/health")
}

export async function fetchDemoContext(): Promise<FixedContext> {
  return aerisFetch<FixedContext>("/context/demo")
}

/** Send a JPEG frame blob captured from the camera. Returns YOLO detections. */
export async function postScanFrame(blob: Blob): Promise<DynamicContext> {
  const body = new FormData()
  body.append("file", blob, "frame.jpg")
  return aerisFetch<DynamicContext>("/scan-frame", { method: "POST", body })
}

/** Get sustainability advice for a detected object + CASTNET context. */
export async function postSustainabilityDetect(obj: SceneObject): Promise<SustainabilityAdvice> {
  return aerisFetch<SustainabilityAdvice>("/sustainability/detect", {
    method: "POST",
    body: JSON.stringify({
      detection: {
        object_class: obj.name,
        confidence: obj.confidence,
        frame_id: `frame_${Date.now()}`,
        timestamp: new Date().toISOString(),
        bbox: obj.bbox,
      },
    }),
  })
}

export async function fetchAnalysisJob(jobId: string): Promise<AnalysisJobResponse> {
  return aerisFetch<AnalysisJobResponse>(`/analysis/${encodeURIComponent(jobId)}`)
}

export async function pollAnalysisJob(
  jobId: string,
  opts?: { intervalMs?: number; maxAttempts?: number }
): Promise<AnalysisJobResponse> {
  const intervalMs = opts?.intervalMs ?? 250
  const maxAttempts = opts?.maxAttempts ?? 120
  for (let i = 0; i < maxAttempts; i++) {
    const job = await fetchAnalysisJob(jobId)
    if (job.status === "complete" || job.status === "failed") return job
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  throw new Error("Analysis job polling timed out")
}

export function formatRecommendation(job: AnalysisJobResponse): string {
  if (job.status === "failed") return job.error ?? "Analysis failed"
  const rec = job.recommendations
  if (!rec) return "Waiting for recommendations…"
  const actionBits = rec.actions.slice(0, 2).map((a) => a.reason)
  return [rec.explanation, ...actionBits].filter(Boolean).join(" ")
}
