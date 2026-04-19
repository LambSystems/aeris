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
  const [activeTab, setActiveTab] = useState("home")

  // 🎥 Camera (only after entering)
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

  // 🌍 LANDING PAGE
  if (!entered) {
    return (
      <div className="h-screen w-screen relative overflow-hidden text-white">

        {/* VIDEO */}
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
        >
          <source src="/earth.mp4" type="video/mp4" />
        </video>

        {/* OVERLAY */}
        <div className="absolute inset-0 bg-black/50" />

        {/* NAVBAR */}
        <div className="absolute top-0 left-0 right-0 z-20 flex justify-between items-center px-10 py-6">
          <h1 className="text-2xl font-semibold">AEIRS</h1>

          <div className="relative hidden md:flex gap-10 text-sm text-white/90">
            {["home", "features", "impact"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className="relative pb-1 capitalize"
              >
                {tab}
                {activeTab === tab && (
                  <div className="absolute left-0 bottom-0 w-full h-[2px] bg-blue-400" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* CONTENT */}
        <div className="relative z-10 flex h-full items-center px-16">
          <div className="max-w-xl">

            {activeTab === "home" && (
              <>
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
              </>
            )}

            {activeTab === "features" && (
              <>
                <h1 className="text-5xl font-bold mb-6">
                  Powerful Real-Time Detection
                </h1>

                <p className="text-white/80 mb-8">
                  AEIRS detects objects and combines them with environmental
                  signals to generate real-time insights.
                  <br /><br />
                  • Object detection  
                  • Air quality awareness  
                  • Smart recommendations  
                </p>
              </>
            )}

            {activeTab === "impact" && (
              <>
                <h1 className="text-5xl font-bold mb-6">
                  Driving Environmental Awareness
                </h1>

                <p className="text-white/80 mb-8">
                  AEIRS helps people make safer and smarter decisions by linking
                  their surroundings with environmental data.
                  <br /><br />
                  Reduce exposure. Improve habits. Build healthier communities.
                </p>
              </>
            )}

          </div>
        </div>

      </div>
    )
  }

  // 📷 AEIRS SCREEN
  return (
    <div className="h-screen w-screen bg-black relative overflow-hidden">

      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="absolute w-full h-full object-cover"
      />

      <canvas ref={canvasRef} className="absolute w-full h-full" />

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

      <div className="absolute top-4 right-4 flex flex-col gap-4 w-56">

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

        <div className="bg-white/85 p-3 rounded-xl shadow-lg text-black text-xs">
          <h2 className="font-semibold mb-1">Users</h2>
          <p>🌫️ {airQuality}</p>
          <p>📍 {location}</p>
        </div>

      </div>
    </div>
  )
}
