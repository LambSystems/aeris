"use client"

import { useEffect, useMemo, useRef, useState } from "react"

type Detection = {
  label: string
  confidence: number
  x: number
  y: number
  w: number
  h: number
}

export default function Page() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const currentDetections = useRef<Detection[]>([])
  const renderBoxes = useRef<Detection[]>([])

  const [detectedObject, setDetectedObject] = useState<Detection | null>(null)

  const [airQuality, setAirQuality] = useState("Loading...")
  const [location, setLocation] = useState("Detecting...")
  const [entered, setEntered] = useState(false)

  useEffect(() => {
  if (!entered) return

  async function startCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" }
    })
    if (videoRef.current) videoRef.current.srcObject = stream
  }

  startCamera()
}, [entered])

  // 🎥 Camera
 

  // 🧠 Detection
  useEffect(() => {
    const interval = setInterval(generateDetection, 1500)
    return () => clearInterval(interval)
  }, [])

  // 👤 Users simulation
  useEffect(() => {
    const interval = setInterval(() => {
      const aqi = ["Good (42)", "Moderate (78)", "Unhealthy (132)"]
      const loc = ["New York, NY", "Chicago, IL", "Los Angeles, CA"]

      setAirQuality(aqi[Math.floor(Math.random() * aqi.length)])
      setLocation(loc[Math.floor(Math.random() * loc.length)])
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  const generateDetection = () => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const labels = ["person", "car", "dog", "bicycle", "chair"]

    const w = Math.random() * 150 + 80
    const h = Math.random() * 150 + 80
    const x = Math.random() * (canvas.width - w)
    const y = Math.random() * (canvas.height - h)

    const d: Detection = {
      label: labels[Math.floor(Math.random() * labels.length)],
      confidence: Math.random(),
      x,
      y,
      w,
      h
    }

    currentDetections.current = [d]
    setDetectedObject(d)

    if (renderBoxes.current.length === 0) {
      renderBoxes.current = [d]
    }
  }

  const lerp = (a: number, b: number, t: number) => a + (b - a) * t

  useEffect(() => {
    let id: number
    const loop = () => {
      drawBox()
      id = requestAnimationFrame(loop)
    }
    loop()
    return () => cancelAnimationFrame(id)
  }, [])

  const drawBox = () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")

    canvas.width = video.videoWidth || window.innerWidth
    canvas.height = video.videoHeight || window.innerHeight

    ctx?.clearRect(0, 0, canvas.width, canvas.height)

    const target = currentDetections.current[0]
    if (!target) return

    const prev = renderBoxes.current[0] || target

    const smooth: Detection = {
      ...target,
      x: lerp(prev.x, target.x, 0.1),
      y: lerp(prev.y, target.y, 0.1),
      w: lerp(prev.w, target.w, 0.1),
      h: lerp(prev.h, target.h, 0.1)
    }

    ctx!.strokeStyle = "#00FF66"
    ctx!.lineWidth = 3
    ctx!.strokeRect(smooth.x, smooth.y, smooth.w, smooth.h)

    renderBoxes.current = [smooth]
  }

  const d = renderBoxes.current[0]

  // 🧠 Recommendation logic (CORE CHANGE)
  const recommendation = useMemo(() => {
    if (!detectedObject) return "Scanning..."

    const obj = detectedObject.label.toLowerCase()
    const aq = airQuality.toLowerCase()

    if (obj === "person" && aq.includes("unhealthy")) {
      return "Air quality is poor → reduce outdoor exposure"
    }
    if (obj === "car" && aq.includes("unhealthy")) {
      return "Avoid idling → pollution already high"
    }
    if (obj === "bicycle") {
      return "Eco-friendly transport detected"
    }
    if (obj === "dog") {
      return "Keep walks short if air worsens"
    }

    return "Environment stable"
  }, [detectedObject, airQuality])

  if (!entered) {
  return (
    <div className="h-screen w-screen relative overflow-hidden text-white">

      {/* 🌍 VIDEO BACKGROUND */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover"
      >
        <source src="/earth.mp4" type="video/mp4" />
      </video>

      {/* DARK OVERLAY */}
      <div className="absolute inset-0 bg-black/50" />

      {/* NAVBAR */}
      <div className="absolute top-0 left-0 right-0 z-20 flex justify-between items-center px-10 py-6">
        <h1 className="text-2xl font-semibold">AEIRS</h1>

        <div className="hidden md:flex gap-8 text-sm text-white/90">
          <span>Home</span>
          <span>Features</span>
          <span>Impact</span>
          <span>How it Works</span>
        </div>
      </div>

      {/* HERO TEXT */}
      <div className="relative z-10 flex h-full items-center px-16">
        <div className="max-w-xl">
          <h1 className="text-5xl font-bold mb-6">
            Track Your Air. <br /> Shape Safer Spaces.
          </h1>

          <p className="text-white/80 mb-8">
            AI-powered environmental awareness system.
          </p>

          <button
            onClick={() => setEntered(true)}
            className="bg-white/10 border border-white/30 px-6 py-3 rounded-full backdrop-blur-md hover:bg-white/20 transition"
          >
            Step into AEIRS
          </button>
        </div>
      </div>

    </div>
  )
}

  return (
    <div className="h-screen w-screen bg-black relative overflow-hidden">

      {/* Camera */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="absolute w-full h-full object-cover"
      />

      {/* Canvas */}
      <canvas ref={canvasRef} className="absolute w-full h-full" />

      {/* 🔗 Line → BOX → RECOMMENDATION */}
      {d && (
        <svg className="absolute w-full h-full pointer-events-none">
          <line
            x1={d.x + d.w / 2}
            y1={d.y}
            x2={d.x + d.w / 2}
            y2={d.y - 50}
            stroke="white"
            strokeWidth="2"
          />
        </svg>
      )}

      {/* 💬 RECOMMENDATION (FOLLOWS BOX) */}
      {d && (
        <div
          className="absolute bg-white/95 p-3 rounded-xl shadow-lg text-black text-xs w-48"
          style={{
            left: d.x + d.w / 2 - 90,
            top: d.y - 100
          }}
        >
          <h2 className="font-semibold mb-1">Recommendation</h2>
          <p>{recommendation}</p>
        </div>
      )}

      {/* RIGHT PANELS */}
      <div className="absolute top-4 right-4 flex flex-col gap-4 w-56">

        {/* DETECTED */}
        <div className="bg-white/95 p-3 rounded-xl shadow-lg text-black text-xs">
          <h2 className="font-semibold mb-1">Detected Objects</h2>
          {detectedObject ? (
            <p>
              {detectedObject.label} ({(detectedObject.confidence * 100).toFixed(0)}%)
            </p>
          ) : (
            <p>No object</p>
          )}
        </div>

        {/* USERS */}
        <div className="bg-white/85 p-3 rounded-xl shadow-lg text-black text-xs">
          <h2 className="font-semibold mb-1">Users</h2>
          <p>🌫️ {airQuality}</p>
          <p>📍 {location}</p>
        </div>

      </div>
    </div>
  )
}