import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CameraViewport } from "@/components/aeris/CameraViewport";
import { DecisionPanel } from "@/components/aeris/DecisionPanel";
import { StatusChip } from "@/components/aeris/StatusChip";
import { Button } from "@/components/ui/button";
import { useCameraScanner } from "@/hooks/useCameraScanner";
import { detectSustainability, getFixedContext } from "@/lib/api";
import type {
  DetectedObject,
  FixedContextResponse,
  SustainabilityResponse,
} from "@/lib/types";
import { formatObjectName } from "@/lib/format";
import {
  Pause,
  Play,
  Leaf,
  Wifi,
  WifiOff,
  MapPin,
} from "lucide-react";

// Default coords match backend example (Bondville, IL area).
const DEFAULT_LAT = 40.9478;
const DEFAULT_LNG = -90.3712;

const Index = () => {
  const [scanning, setScanning] = useState(true);
  const [coords, setCoords] = useState<{ lat: number; lng: number }>({
    lat: DEFAULT_LAT,
    lng: DEFAULT_LNG,
  });

  const {
    videoRef,
    cameraReady,
    cameraError,
    objects,
    frameWidth,
    frameHeight,
    lastFrameId,
    lastTimestamp,
    visionSource,
  } = useCameraScanner({ enabled: scanning, intervalMs: 700 });

  // Try to grab user geolocation once; fall back to default silently.
  useEffect(() => {
    if (!("geolocation" in navigator)) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => {},
      { timeout: 4000, maximumAge: 60_000 },
    );
  }, []);

  // Fixed environmental context — fetch once per coords.
  const [context, setContext] = useState<FixedContextResponse | null>(null);
  const [contextLoading, setContextLoading] = useState(true);
  const [contextError, setContextError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setContextLoading(true);
    setContextError(null);
    getFixedContext(coords.lat, coords.lng)
      .then((ctx) => {
        if (!cancelled) setContext(ctx);
      })
      .catch(() => {
        if (!cancelled) setContextError("context_failed");
      })
      .finally(() => {
        if (!cancelled) setContextLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [coords.lat, coords.lng]);

  // Pick top-confidence detection as the "primary" focus.
  const primaryObject: DetectedObject | null = useMemo(() => {
    if (!objects.length) return null;
    return [...objects].sort((a, b) => b.confidence - a.confidence)[0];
  }, [objects]);

  // Recommendation. Throttled by primary object identity to prevent flicker.
  const [recommendation, setRecommendation] =
    useState<SustainabilityResponse | null>(null);
  const [recLoading, setRecLoading] = useState(false);
  const [recUpdating, setRecUpdating] = useState(false);
  const lastReqKeyRef = useRef<string>("");

  useEffect(() => {
    if (!primaryObject || !lastFrameId || !lastTimestamp) return;
    // Stable key: object class only — keeps recommendation steady while scanning the same item.
    const key = primaryObject.name;
    if (key === lastReqKeyRef.current && recommendation) {
      // Same object class — keep current recommendation, no refetch.
      return;
    }
    lastReqKeyRef.current = key;

    if (recommendation) setRecUpdating(true);
    else setRecLoading(true);

    detectSustainability({
      latitude: coords.lat,
      longitude: coords.lng,
      detection: {
        object_class: primaryObject.name,
        confidence: primaryObject.confidence,
        frame_id: lastFrameId,
        timestamp: lastTimestamp,
        bbox: primaryObject.bbox,
      },
    })
      .then((r) => setRecommendation(r))
      .catch(() => {})
      .finally(() => {
        setRecLoading(false);
        setRecUpdating(false);
      });
  }, [primaryObject, lastFrameId, lastTimestamp, coords.lat, coords.lng, recommendation]);

  const sceneMode: "indoor" | "outdoor" =
    context?.weather_alerts && context.weather_alerts.length > 0
      ? "outdoor"
      : (context?.weather?.wind_speed_kmh ?? 0) > 5
        ? "outdoor"
        : "indoor";

  const toggleScanning = useCallback(() => setScanning((s) => !s), []);

  const locationLabel =
    context?.castnet?.location ??
    context?.location?.name ??
    `${coords.lat.toFixed(2)}, ${coords.lng.toFixed(2)}`;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card/60 backdrop-blur">
        <div className="container flex flex-wrap items-center gap-3 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Leaf className="h-4 w-4" strokeWidth={2.25} />
            </div>
            <div className="leading-tight">
              <h1 className="text-base font-semibold tracking-tight">Aeris</h1>
              <p className="text-[10.5px] uppercase tracking-wider text-muted-foreground">
                Environmental scanner
              </p>
            </div>
          </div>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <StatusChip
              tone={cameraReady ? "primary" : "muted"}
              label={cameraReady ? "Camera ready" : "Camera offline"}
              icon={cameraReady ? Wifi : WifiOff}
            />
            <StatusChip tone="accent" label={locationLabel} icon={MapPin} />
            <StatusChip
              tone={scanning ? "primary" : "muted"}
              label={scanning ? "Scanning" : "Paused"}
              pulse={scanning}
            />
            <StatusChip
              tone={visionSource === "browser_yolo" ? "primary" : "muted"}
              label={formatVisionSource(visionSource)}
            />
          </div>
        </div>
      </header>

      <main className="container grid gap-4 py-4 lg:grid-cols-[minmax(0,7fr)_minmax(320px,3fr)] lg:gap-6 lg:py-6">
        <section className="flex flex-col gap-3">
          <CameraViewport
            videoRef={videoRef}
            objects={objects}
            frameWidth={frameWidth}
            frameHeight={frameHeight}
            scanning={scanning}
            cameraReady={cameraReady}
            errorMessage={cameraError}
          />

          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card px-4 py-2.5">
            <div className="flex items-center gap-2 text-sm">
              <span
                className={
                  primaryObject
                    ? "h-2 w-2 rounded-full bg-primary animate-pulse-soft"
                    : "h-2 w-2 rounded-full bg-muted-foreground"
                }
              />
              <span className="text-foreground">
                {primaryObject
                  ? `Detected ${formatObjectName(primaryObject.name)}`
                  : scanning
                    ? "Searching for objects…"
                    : "Scanning paused"}
              </span>
              {objects.length > 1 ? (
                <span className="text-xs text-muted-foreground">
                  +{objects.length - 1} more
                </span>
              ) : null}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={scanning ? "outline" : "default"}
                size="sm"
                onClick={toggleScanning}
                className="gap-1.5"
              >
                {scanning ? (
                  <>
                    <Pause className="h-3.5 w-3.5" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5" />
                    Resume
                  </>
                )}
              </Button>
            </div>
          </div>
        </section>

        <DecisionPanel
          primaryObject={primaryObject}
          context={context}
          contextLoading={contextLoading}
          contextError={contextError}
          recommendation={recommendation}
          recommendationLoading={recLoading}
          recommendationUpdating={recUpdating}
          sceneMode={sceneMode}
        />
      </main>
    </div>
  );
};

function formatVisionSource(source: "browser_yolo" | "backend_yolo" | "loading"): string {
  if (source === "browser_yolo") return "Browser YOLO";
  if (source === "backend_yolo") return "Backend YOLO";
  return "Vision loading";
}

export default Index;
