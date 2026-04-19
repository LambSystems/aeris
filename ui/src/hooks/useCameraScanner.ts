import { useCallback, useEffect, useRef, useState } from "react";
import type { DetectedObject, ScanFrameResponse } from "@/lib/types";
import { createPreferredVisionProvider, type VisionProviderSource } from "@/vision";
import type { VisionProvider } from "@/vision/types";

const STABILITY_WINDOW_MS = 2200;
const KEEP_ALIVE_MS = 1400;
const MIN_HITS = 2;
const HIGH_CONFIDENCE = 0.72;
const SWITCH_MARGIN = 0.18;

interface UseCameraScannerOptions {
  /** @deprecated Kept for backwards compatibility; the loop now runs as fast as inference allows. */
  intervalMs?: number;
  enabled: boolean;
}

interface UseCameraScannerReturn {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  cameraReady: boolean;
  cameraError: string | null;
  /** Live ref for the canvas rAF draw loop — bypasses React renders. Always latest post-NMS detections. */
  objectsRef: React.MutableRefObject<DetectedObject[]>;
  /** Live ref for source frame dimensions — used by the canvas draw for scaling. */
  frameSizeRef: React.MutableRefObject<{ width: number; height: number }>;
  /** Coarse React state — only updated when detection count changes, for UI chrome ("+N more"). */
  objectCount: number;
  /** Single debounced object used to trigger the Claude advice call without flickering. */
  stablePrimary: DetectedObject | null;
  lastFrameId: string | null;
  lastTimestamp: string | null;
  scanning: boolean;
  visionSource: VisionProviderSource | "loading";
}

export function useCameraScanner({
  enabled,
}: UseCameraScannerOptions): UseCameraScannerReturn {
  const videoRef = useRef<HTMLVideoElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const providerRef = useRef<VisionProvider | null>(null);
  const historyRef = useRef<DetectionSample[]>([]);
  const stableObjectsRef = useRef<DetectedObject[]>([]);
  const lastStableAtRef = useRef(0);

  // Live refs — written on every inference, read on every animation frame. No React re-render.
  const objectsRef = useRef<DetectedObject[]>([]);
  const frameSizeRef = useRef<{ width: number; height: number }>({ width: 0, height: 0 });

  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [objectCount, setObjectCount] = useState(0);
  const [stablePrimary, setStablePrimary] = useState<DetectedObject | null>(null);
  const [lastFrameId, setLastFrameId] = useState<string | null>(null);
  const [lastTimestamp, setLastTimestamp] = useState<string | null>(null);
  const [visionSource, setVisionSource] = useState<VisionProviderSource | "loading">("loading");

  // Start camera once
  useEffect(() => {
    let stream: MediaStream | null = null;
    let cancelled = false;

    async function start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment", width: 1280, height: 720 },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        const video = videoRef.current;
        if (!video) return;
        video.srcObject = stream;
        await video.play();
        setCameraReady(true);
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Unable to access camera.";
        setCameraError(
          /denied|permission/i.test(msg)
            ? "Camera permission denied. Allow access to scan."
            : "Unable to start the camera on this device.",
        );
      }
    }
    start();
    return () => {
      cancelled = true;
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    void createPreferredVisionProvider()
      .then((provider) => {
        if (cancelled) {
          void provider.dispose?.();
          return;
        }
        providerRef.current = provider;
        setVisionSource(provider.source);
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Browser YOLO failed to initialize";
        if (!cancelled) {
          setCameraError(`Browser YOLO failed: ${message}`);
        }
      });

    return () => {
      cancelled = true;
      void providerRef.current?.dispose?.();
      providerRef.current = null;
    };
  }, []);

  const captureFrame = useCallback(async (): Promise<Blob | null> => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;
    const sourceW = video.videoWidth;
    const sourceH = video.videoHeight;
    // Capture near the model's input size — faster encode, no loss of detail.
    const scale = Math.min(1, 720 / sourceW);
    const w = Math.round(sourceW * scale);
    const h = Math.round(sourceH * scale);
    if (!w || !h) return null;
    if (!captureCanvasRef.current) {
      captureCanvasRef.current = document.createElement("canvas");
    }
    const canvas = captureCanvasRef.current;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, w, h);
    return await new Promise<Blob | null>((resolve) =>
      canvas.toBlob((b) => resolve(b), "image/jpeg", 0.78),
    );
  }, []);

  // Continuous inference loop — each frame starts right after the previous completes.
  useEffect(() => {
    if (!enabled || !cameraReady) return;

    let stopped = false;

    let lastCount = -1;
    let lastStableKey = "";

    const runOnce = async () => {
      try {
        const provider = providerRef.current;
        if (!provider) return;
        const blob = await captureFrame();
        if (!blob || stopped) return;
        const result: ScanFrameResponse = await provider.detect(blob);
        if (stopped) return;

        const raw = result.objects ?? [];

        // Hot path: write to refs so the canvas rAF loop paints the boxes instantly.
        objectsRef.current = raw;
        frameSizeRef.current = { width: result.frame_width, height: result.frame_height };

        // Cold path: only touch React state when the visible UI actually needs to re-render.
        if (raw.length !== lastCount) {
          lastCount = raw.length;
          setObjectCount(raw.length);
        }

        const stable = stabilizeDetections(raw, Date.now())[0] ?? null;
        const stableKey = stable ? `${stable.name}:${stable.confidence.toFixed(2)}` : "";
        if (stableKey !== lastStableKey) {
          lastStableKey = stableKey;
          setStablePrimary(stable);
          setLastFrameId(`frame_${Date.now()}`);
          setLastTimestamp(new Date().toISOString());
        }
      } catch {
        // swallow — keep last detection visible (avoids flicker)
      }
    };

    const schedule = () => {
      if (stopped) return;
      // rAF aligns with display refresh; inference itself is the real throttle.
      requestAnimationFrame(async () => {
        if (stopped) return;
        if (!providerRef.current) {
          // Provider still loading — retry shortly.
          window.setTimeout(schedule, 80);
          return;
        }
        await runOnce();
        schedule();
      });
    };

    schedule();
    return () => {
      stopped = true;
    };
  }, [enabled, cameraReady, captureFrame]);

  return {
    videoRef,
    cameraReady,
    cameraError,
    objectsRef,
    frameSizeRef,
    objectCount,
    stablePrimary,
    lastFrameId,
    lastTimestamp,
    scanning: enabled && cameraReady,
    visionSource,
  };

  function stabilizeDetections(rawObjects: DetectedObject[], now: number): DetectedObject[] {
    const candidates = rawObjects.filter((object) => object.bbox && object.confidence >= 0.18);
    historyRef.current = [...historyRef.current, { at: now, objects: candidates }].filter(
      (sample) => now - sample.at <= STABILITY_WINDOW_MS,
    );

    const scored = scoreStableCandidates(historyRef.current);
    const previous = stableObjectsRef.current[0] ?? null;
    const next = chooseStableCandidate(scored, previous);

    if (next) {
      stableObjectsRef.current = [next];
      lastStableAtRef.current = now;
      return stableObjectsRef.current;
    }

    if (previous && now - lastStableAtRef.current <= KEEP_ALIVE_MS) {
      return stableObjectsRef.current;
    }

    stableObjectsRef.current = [];
    return [];
  }
}

type DetectionSample = {
  at: number;
  objects: DetectedObject[];
};

type CandidateScore = {
  name: string;
  hits: number;
  averageConfidence: number;
  score: number;
  latest: DetectedObject;
};

function scoreStableCandidates(samples: DetectionSample[]): CandidateScore[] {
  const byName = new Map<string, DetectedObject[]>();

  for (const sample of samples) {
    const bestByName = new Map<string, DetectedObject>();
    for (const object of sample.objects) {
      const existing = bestByName.get(object.name);
      if (!existing || object.confidence > existing.confidence) {
        bestByName.set(object.name, object);
      }
    }
    for (const [name, object] of bestByName) {
      byName.set(name, [...(byName.get(name) ?? []), object]);
    }
  }

  return [...byName.entries()]
    .map(([name, objects]) => {
      const latest = objects[objects.length - 1];
      const averageConfidence = objects.reduce((sum, object) => sum + object.confidence, 0) / objects.length;
      return {
        name,
        hits: objects.length,
        averageConfidence,
        score: objects.length * 0.65 + averageConfidence,
        latest: {
          ...latest,
          confidence: Math.max(latest.confidence, averageConfidence),
        },
      };
    })
    .sort((a, b) => b.score - a.score);
}

function chooseStableCandidate(scored: CandidateScore[], previous: DetectedObject | null): DetectedObject | null {
  const best = scored[0];
  if (!best) return null;

  const previousScore = previous ? scored.find((candidate) => candidate.name === previous.name) : null;
  if (previous && previousScore) {
    const shouldKeepPrevious =
      previousScore.hits >= 1 &&
      best.name !== previous.name &&
      best.score < previousScore.score + SWITCH_MARGIN &&
      best.hits < 3;
    if (shouldKeepPrevious) return { ...previousScore.latest, name: previous.name };
  }

  const isStable = best.hits >= MIN_HITS || best.averageConfidence >= HIGH_CONFIDENCE;
  if (!isStable && previous?.name === best.name) return best.latest;
  return isStable ? best.latest : null;
}
