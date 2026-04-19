"use client"

import { useEffect, useMemo, useRef, useState } from "react"

import type { DecisionProvider, DynamicContext, FixedContext, SceneObject } from "@/lib/aeris-api"
import {
  fetchDemoContext,
  fetchHealth,
  postScanFrame,
  postSustainabilityDetect,
} from "@/lib/aeris-api"

type Detection = {
  label: string
  confidence: number
  x: number
  y: number
  w: number
  h: number
}

const SCENE_REF_W = 900
const SCENE_REF_H = 480

const WASTE_CLASSES = new Set([
  "soda_can", "plastic_bottle", "cardboard_box", "cigarette_butt",
  "plastic_bag", "food_wrapper", "glass_bottle", "styrofoam_cup",
])

function pickPrimaryObject(objects: SceneObject[]): SceneObject | null {
  if (!objects.length) return null
  const waste = objects.filter((o) => WASTE_CLASSES.has(o.name))
  const pool = waste.length ? waste : objects
  return [...pool].sort((a, b) => b.confidence - a.confidence)[0] ?? null
}

function sceneObjectToDetection(obj: SceneObject, cw: number, ch: number): Detection | null {
  if (!obj.bbox || cw < 32 || ch < 32) return null
  const sx = cw / SCENE_REF_W
  const sy = ch / SCENE_REF_H
  return {
    label: obj.name.replace(/_/g, " "),
    confidence: obj.confidence,
    x: obj.bbox.x * sx,
    y: obj.bbox.y * sy,
    w: obj.bbox.width * sx,
    h: obj.bbox.height * sy,
  }
}

function allObjectsToDetections(objects: SceneObject[], cw: number, ch: number): Detection[] {
  return objects.flatMap((o) => {
    const d = sceneObjectToDetection(o, cw, ch)
    return d ? [d] : []
  })
}

function readProvider(): DecisionProvider {
  const p = process.env.NEXT_PUBLIC_AERIS_PROVIDER
  if (p === "gemini" || p === "openai" || p === "anthropic" || p === "template") return p
  return "template"
}

/** Capture one JPEG frame from a <video> element. */
async function captureFrame(video: HTMLVideoElement): Promise<Blob | null> {
  if (video.readyState < 2) return null
  const canvas = document.createElement("canvas")
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480
  canvas.getContext("2d")?.drawImage(video, 0, 0)
  return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.85))
}

export default function Page() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const currentDetections = useRef<Detection[]>([])
  const renderBoxes = useRef<Detection[]>([])

  const [detectedObject, setDetectedObject] = useState<Detection | null>(null)
  const [detectionCount, setDetectionCount] = useState(0)

  const [fixedContext, setFixedContext] = useState<FixedContext | null>(null)
  const [backendOk, setBackendOk] = useState<boolean | null>(null)
  const [backendMessage, setBackendMessage] = useState<string>("Checking API…")

  const [recommendation, setRecommendation] = useState<string>("Scanning…")
  const [analysisError, setAnalysisError] = useState<string | null>(null)

  const [entered, setEntered] = useState(false)

  // Scale factor from canvas/video space → CSS screen space for popup positioning
  const videoScale = useRef({ x: 1, y: 1 })

  // Start camera
  useEffect(() => {
    if (!entered) return
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then((stream) => {
        if (videoRef.current) videoRef.current.srcObject = stream
      })
      .catch((e) => {
        setBackendMessage("Camera error: " + (e instanceof Error ? e.message : String(e)))
      })
  }, [entered])

  // Connect to backend + load CASTNET context
  useEffect(() => {
    if (!entered) return
    let cancelled = false
    ;(async () => {
      try {
        await fetchHealth()
        if (cancelled) return
        setBackendOk(true)
        setBackendMessage("API connected")
        const fx = await fetchDemoContext()
        if (cancelled) return
        setFixedContext(fx)
      } catch (e) {
        if (cancelled) return
        setBackendOk(false)
        setBackendMessage(e instanceof Error ? e.message : "Could not reach API")
        setRecommendation("Start the backend: cd backend && uvicorn app.main:app --reload")
      }
    })()
    return () => { cancelled = true }
  }, [entered])

  // Main detection loop
  useEffect(() => {
    if (!entered || !fixedContext || backendOk === false) return

    let cancelled = false
    let timer: number | undefined

    const tick = async () => {
      if (cancelled) return
      const video = videoRef.current
      if (!video) { timer = window.setTimeout(tick, 3500); return }

      const cw = video.videoWidth || window.innerWidth
      const ch = video.videoHeight || window.innerHeight

      try {
        // 1. Capture current frame — retry next tick if video not ready yet
        const blob = await captureFrame(video)
        if (cancelled) return
        if (!blob) {
          timer = window.setTimeout(tick, 1000)
          return
        }

        // Track scale from video → screen for popup positioning
        if (video.videoWidth && video.videoHeight) {
          const rect = video.getBoundingClientRect()
          videoScale.current = {
            x: rect.width / video.videoWidth,
            y: rect.height / video.videoHeight,
          }
        }

        const dynamic = await postScanFrame(blob)
        if (cancelled) return

        // 2. Store all detections for rendering; pick primary for advice
        const all = allObjectsToDetections(dynamic.objects, cw, ch)
        currentDetections.current = all
        setDetectionCount(all.length)

        const primary = pickPrimaryObject(dynamic.objects)
        const det = primary ? sceneObjectToDetection(primary, cw, ch) : null
        if (det) {
          setDetectedObject(det)
          if (renderBoxes.current.length === 0) renderBoxes.current = [det]
        } else {
          setDetectedObject(null)
          setRecommendation("No objects detected — point camera at waste.")
        }

        // 3. Get sustainability advice for detected object
        if (primary) {
          const advice = await postSustainabilityDetect(primary)
          if (cancelled) return
          setRecommendation(`${advice.context} ${advice.action}`)
        }

        setAnalysisError(null)
      } catch (e) {
        if (cancelled) return
        const msg = e instanceof Error ? e.message : String(e)
        setAnalysisError(msg)
        setRecommendation("Could not refresh analysis")
      }

      if (!cancelled) timer = window.setTimeout(tick, 3500)
    }

    tick()

    return () => {
      cancelled = true
      if (timer !== undefined) window.clearTimeout(timer)
    }
  }, [entered, fixedContext, backendOk])

  // Smooth bounding box animation
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t

  useEffect(() => {
    let id: number
    const loop = () => { drawBox(); id = requestAnimationFrame(loop) }
    loop()
    return () => cancelAnimationFrame(id)
  }, [])

  const drawBox = () => {
    if (!videoRef.current || !canvasRef.current) return
    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")!
    canvas.width = video.videoWidth || window.innerWidth
    canvas.height = video.videoHeight || window.innerHeight
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    const detections = currentDetections.current
    if (!detections.length) { renderBoxes.current = []; return }

    // Lerp the primary (first) box for the popup anchor; draw all others directly
    const primary = detections[0]
    const prev = renderBoxes.current[0] || primary
    const smooth: Detection = {
      ...primary,
      x: lerp(prev.x, primary.x, 0.1),
      y: lerp(prev.y, primary.y, 0.1),
      w: lerp(prev.w, primary.w, 0.1),
      h: lerp(prev.h, primary.h, 0.1),
    }
    renderBoxes.current = [smooth]

    for (const det of detections) {
      const isWaste = WASTE_CLASSES.has(det.label.replace(/ /g, "_"))
      const color = isWaste ? "#00FF66" : "#60CFFF"
      const { x, y, w, h } = det === primary ? smooth : det

      // Box
      ctx.strokeStyle = color
      ctx.lineWidth = 2.5
      ctx.strokeRect(x, y, w, h)

      // Label background
      const tag = `${det.label} ${(det.confidence * 100).toFixed(0)}%`
      ctx.font = "bold 13px system-ui, sans-serif"
      const tw = ctx.measureText(tag).width
      const th = 18
      const ty = y > th + 4 ? y - th - 4 : y + h + 2
      ctx.fillStyle = isWaste ? "#00FF66" : "#60CFFF"
      ctx.fillRect(x, ty, tw + 10, th + 4)

      // Label text
      ctx.fillStyle = "#000"
      ctx.fillText(tag, x + 5, ty + th - 1)
    }
  }

  const d = renderBoxes.current[0]

  const airSummary = useMemo(() => {
    if (!fixedContext) return "Loading CASTNET profile…"
    const { ozone_risk, deposition_risk } = fixedContext.pollution_profile
    return `Ozone: ${ozone_risk} · Deposition: ${deposition_risk}`
  }, [fixedContext])

  if (!entered) {
    return (
      <div className="relative h-screen w-screen overflow-hidden text-white">
        <video autoPlay loop muted playsInline className="absolute inset-0 h-full w-full object-cover">
          <source src="/earth.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-black/50" />
        <div className="absolute left-0 right-0 top-0 z-20 flex items-center justify-between px-10 py-6">
          <h1 className="text-2xl font-semibold">AEIRS</h1>
          <div className="hidden gap-8 text-sm text-white/90 md:flex">
            <span>Home</span>
            <span>Features</span>
            <span>Impact</span>
            <span>How it Works</span>
          </div>
        </div>
        <div className="relative z-10 flex h-full items-center px-16">
          <div className="max-w-xl">
            <h1 className="mb-6 text-5xl font-bold">
              Track Your Air. <br /> Shape Safer Spaces.
            </h1>
            <p className="mb-8 text-white/80">AI-powered environmental awareness system.</p>
            <button
              type="button"
              onClick={() => setEntered(true)}
              className="rounded-full border border-white/30 bg-white/10 px-6 py-3 backdrop-blur-md transition hover:bg-white/20"
            >
              Step into AEIRS
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      <video ref={videoRef} autoPlay playsInline className="absolute inset-0 h-full w-full object-cover" />
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" style={{ zIndex: 10 }} />

      {d && (() => {
        const sx = videoScale.current.x
        const sy = videoScale.current.y
        const cx = (d.x + d.w / 2) * sx
        const cy = d.y * sy
        return (
          <svg className="pointer-events-none absolute inset-0 h-full w-full" style={{ zIndex: 20 }}>
            <line x1={cx} y1={cy} x2={cx} y2={cy - 50} stroke="white" strokeWidth="2" />
          </svg>
        )
      })()}

      {d && (() => {
        const sx = videoScale.current.x
        const sy = videoScale.current.y
        const cx = (d.x + d.w / 2) * sx
        const cy = d.y * sy
        return (
        <div
          className="absolute w-64 rounded-xl bg-white/95 p-3 text-xs text-black shadow-lg"
          style={{ left: cx - 120, top: Math.max(8, cy - 140), zIndex: 30 }}
        >
          <h2 className="mb-1 font-semibold">
            ♻ {detectedObject?.label} ({((detectedObject?.confidence ?? 0) * 100).toFixed(0)}%)
          </h2>
          <p className="leading-snug">{recommendation}</p>
          {analysisError && <p className="mt-1 text-red-600">{analysisError}</p>}
        </div>
        )
      })()}

      <div className="absolute right-4 top-4 flex w-56 flex-col gap-4" style={{ zIndex: 30 }}>
        <div className="rounded-xl bg-white/95 p-3 text-xs text-black shadow-lg">
          <h2 className="mb-1 font-semibold">Backend</h2>
          <p className={backendOk ? "text-emerald-700" : backendOk === false ? "text-red-600" : ""}>
            {backendMessage}
          </p>
          <p className="mt-1 break-all text-[10px] text-neutral-500">
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
          </p>
        </div>

        <div className="rounded-xl bg-white/95 p-3 text-xs text-black shadow-lg">
          <h2 className="mb-1 font-semibold">Detected ({detectionCount})</h2>
          {detectedObject
            ? <p>{detectedObject.label} ({(detectedObject.confidence * 100).toFixed(0)}%)</p>
            : <p className="text-neutral-400">Nothing yet</p>}
        </div>

        <div className="rounded-xl bg-white/85 p-3 text-xs text-black shadow-lg">
          <h2 className="mb-1 font-semibold">Context</h2>
          <p className="leading-snug">📍 {fixedContext?.location ?? "…"}</p>
          <p className="mt-1 leading-snug">🌫️ {airSummary}</p>
          <p className="mt-1 text-[10px] leading-snug text-neutral-600">
            {fixedContext?.summary ?? "CASTNET summary loads when the API is up."}
          </p>
        </div>
      </div>
    </div>
  )
}
