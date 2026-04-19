import { useEffect, useMemo, useRef, useState } from "react";

import { apiBaseUrl, getAdvice, getFixedContext, getHealth, scanFrame } from "./api";
import type { DynamicContext, FixedContext, LocationState, SceneObject, SustainabilityAdvice } from "./types";

const DEMO_LOCATION: LocationState = {
  latitude: 40.9478,
  longitude: -90.3712,
  label: "Galesburg, IL",
  source: "demo_default",
};

const ADVICE_COOLDOWN_MS = 12_000;
const SCAN_INTERVAL_MS = 700;
const SCAN_MAX_WIDTH = 960;

type CameraState = "idle" | "starting" | "live" | "failed";
type ScanState = "idle" | "scanning" | "detected" | "empty" | "failed";
type AdviceState = "idle" | "thinking" | "ready" | "failed";

function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const scanTimerRef = useRef<number | null>(null);
  const scanInFlightRef = useRef(false);
  const lastAdviceAtRef = useRef<Record<string, number>>({});

  const [cameraState, setCameraState] = useState<CameraState>("idle");
  const [scanState, setScanState] = useState<ScanState>("idle");
  const [adviceState, setAdviceState] = useState<AdviceState>("idle");
  const [apiStatus, setApiStatus] = useState("checking");
  const [location, setLocation] = useState<LocationState>(DEMO_LOCATION);
  const [fixedContext, setFixedContext] = useState<FixedContext | null>(null);
  const [dynamicContext, setDynamicContext] = useState<DynamicContext | null>(null);
  const [advice, setAdvice] = useState<SustainabilityAdvice | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void getHealth()
      .then(() => {
        if (!cancelled) setApiStatus("connected");
      })
      .catch((err: unknown) => {
        if (!cancelled) setApiStatus(err instanceof Error ? err.message : "offline");
      });

    navigator.geolocation?.getCurrentPosition(
      (position) => {
        if (cancelled) return;
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          label: `${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`,
          source: "browser_gps",
        });
      },
      () => {
        if (!cancelled) setLocation(DEMO_LOCATION);
      },
      { enableHighAccuracy: false, timeout: 2500, maximumAge: 300000 },
    );

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    void getFixedContext(location)
      .then((context) => {
        if (!cancelled) setFixedContext(context);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load fixed context");
      });
    return () => {
      cancelled = true;
    };
  }, [location]);

  useEffect(() => {
    return () => {
      if (scanTimerRef.current) window.clearInterval(scanTimerRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const objects = dynamicContext?.objects ?? [];
  const primaryObject = useMemo(() => [...objects].sort((a, b) => b.confidence - a.confidence)[0] ?? null, [objects]);
  const sourceStatus = fixedContext?.source_status ?? {};

  async function startCamera() {
    setCameraState("starting");
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraState("live");
      scheduleScanning();
    } catch (err) {
      setCameraState("failed");
      setError(err instanceof Error ? err.message : "Camera unavailable");
    }
  }

  function scheduleScanning() {
    if (scanTimerRef.current) window.clearInterval(scanTimerRef.current);
    void runScan();
    scanTimerRef.current = window.setInterval(() => {
      void runScan();
    }, SCAN_INTERVAL_MS);
  }

  async function runScan() {
    if (!videoRef.current || videoRef.current.readyState < 2) return;
    if (scanInFlightRef.current) return;
    scanInFlightRef.current = true;
    setScanState("scanning");
    try {
      const blob = await captureFrame(videoRef.current);
      const context = await scanFrame(blob);
      setDynamicContext(context);
      setScanState(context.objects.length > 0 ? "detected" : "empty");
      const target = [...context.objects].sort((a, b) => b.confidence - a.confidence)[0];
      if (target) {
        await maybeFetchAdvice(target);
      }
    } catch (err) {
      setScanState("failed");
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      scanInFlightRef.current = false;
    }
  }

  async function maybeFetchAdvice(object: SceneObject) {
    const now = Date.now();
    const key = object.name;
    if (now - (lastAdviceAtRef.current[key] ?? 0) < ADVICE_COOLDOWN_MS) return;
    lastAdviceAtRef.current[key] = now;
    setAdviceState("thinking");
    try {
      const nextAdvice = await getAdvice(location, object);
      setAdvice(nextAdvice);
      setAdviceState("ready");
    } catch (err) {
      setAdviceState("failed");
      setError(err instanceof Error ? err.message : "Advice failed");
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Aeris</p>
          <h1>Live waste intelligence</h1>
        </div>
        <div className="status-cluster">
          <Status label="API" value={apiStatus} tone={apiStatus === "connected" ? "good" : "warn"} />
          <Status label="Camera" value={cameraState} tone={cameraState === "live" ? "good" : "neutral"} />
          <Status label="Vision" value={scanState} tone={scanState === "detected" ? "good" : "neutral"} />
        </div>
      </header>

      <section className="workspace">
        <section className="camera-pane">
          <div className="camera-stage">
            <video ref={videoRef} muted playsInline className="camera-video" />
            <Overlay context={dynamicContext} />
            {cameraState !== "live" && (
              <div className="camera-empty">
                <span>Camera idle</span>
                <button type="button" onClick={startCamera}>
                  Start camera
                </button>
              </div>
            )}
          </div>

          <div className="toolbar">
            <button type="button" onClick={cameraState === "live" ? runScan : startCamera}>
              {cameraState === "live" ? "Scan now" : "Start camera"}
            </button>
            <span>{dynamicContext?.source?.replaceAll("_", " ") ?? "waiting for frame"}</span>
            {error && <strong>{error}</strong>}
          </div>
        </section>

        <aside className="side-panel">
          <section className="context-block">
            <p className="eyebrow">Fixed context</p>
            <h2>{fixedContext?.location.label ?? location.label}</h2>
            <div className="metric-row">
              <Metric label="CASTNET" value={fixedContext?.castnet.location ?? "loading"} />
              <Metric label="Ozone" value={fixedContext ? `${fixedContext.castnet.ozone_ppb.toFixed(1)} ppb` : "..."} />
            </div>
            <p className="summary">{fixedContext?.summary ?? "Loading environment context..."}</p>
            <div className="flag-list">
              {(fixedContext?.risk_flags.length ? fixedContext.risk_flags : ["context_loading"]).map((flag) => (
                <span key={flag}>{flag.replaceAll("_", " ")}</span>
              ))}
            </div>
          </section>

          <section className="context-block">
            <p className="eyebrow">Detection</p>
            <h2>{primaryObject ? formatLabel(primaryObject.name) : "No object selected"}</h2>
            <ObjectList objects={objects} />
          </section>

          <section className="advice-block">
            <p className="eyebrow">Recommendation</p>
            <h2>{advice ? formatLabel(advice.object_detected) : adviceState === "thinking" ? "Analyzing" : "Waiting"}</h2>
            <p>{advice?.context ?? "Latest object advice will appear after the first stable detection."}</p>
            {advice && <strong>{advice.action}</strong>}
            {advice?.environment_summary && <small>{advice.environment_summary}</small>}
          </section>

          <section className="source-block">
            <span>Backend</span>
            <code>{apiBaseUrl()}</code>
            <span>Sources</span>
            <code>{Object.entries(sourceStatus).map(([key, value]) => `${key}:${value}`).join(" | ") || "pending"}</code>
          </section>
        </aside>
      </section>
    </main>
  );
}

async function captureFrame(video: HTMLVideoElement): Promise<Blob> {
  const canvas = document.createElement("canvas");
  const sourceWidth = video.videoWidth || 1280;
  const sourceHeight = video.videoHeight || 720;
  const scale = Math.min(1, SCAN_MAX_WIDTH / sourceWidth);
  canvas.width = Math.round(sourceWidth * scale);
  canvas.height = Math.round(sourceHeight * scale);
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Canvas unavailable");
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.78));
  if (!blob) throw new Error("Frame capture failed");
  return blob;
}

function Overlay({ context }: { context: DynamicContext | null }) {
  if (!context?.frame_width || !context.frame_height) return null;
  return (
    <svg className="overlay" viewBox={`0 0 ${context.frame_width} ${context.frame_height}`} preserveAspectRatio="xMidYMid meet">
      {context.objects.map((object, index) => {
        if (!object.bbox) return null;
        return (
          <g key={`${object.name}-${index}`}>
            <rect
              x={object.bbox.x}
              y={object.bbox.y}
              width={object.bbox.width}
              height={object.bbox.height}
              className="box"
            />
            <rect x={object.bbox.x} y={Math.max(0, object.bbox.y - 34)} width={220} height={28} className="tag-bg" />
            <text x={object.bbox.x + 10} y={Math.max(20, object.bbox.y - 14)} className="tag-text">
              {formatLabel(object.name)} {(object.confidence * 100).toFixed(0)}%
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function Status({ label, value, tone }: { label: string; value: string; tone: "good" | "warn" | "neutral" }) {
  return (
    <div className={`status ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ObjectList({ objects }: { objects: SceneObject[] }) {
  if (!objects.length) return <p className="summary">Point the camera at a bottle, cup, bag, wrapper, or box.</p>;
  return (
    <div className="object-list">
      {objects.map((object, index) => (
        <div key={`${object.name}-${index}`}>
          <span>{formatLabel(object.name)}</span>
          <strong>{(object.confidence * 100).toFixed(0)}%</strong>
        </div>
      ))}
    </div>
  );
}

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}

export default App;
