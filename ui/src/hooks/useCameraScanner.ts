import { useCallback, useEffect, useRef, useState } from "react";
import { scanFrame } from "@/lib/api";
import type { DetectedObject, ScanFrameResponse } from "@/lib/types";

const STABILITY_WINDOW_MS = 2200;
const KEEP_ALIVE_MS = 1400;
const MIN_HITS = 2;
const HIGH_CONFIDENCE = 0.72;
const SWITCH_MARGIN = 0.18;

interface UseCameraScannerOptions {
  intervalMs?: number;
  enabled: boolean;
}

interface UseCameraScannerReturn {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  cameraReady: boolean;
  cameraError: string | null;
  objects: DetectedObject[];
  frameWidth: number;
  frameHeight: number;
  lastFrameId: string | null;
  lastTimestamp: string | null;
  scanning: boolean;
}

export function useCameraScanner({
  intervalMs = 700,
  enabled,
}: UseCameraScannerOptions): UseCameraScannerReturn {
  const videoRef = useRef<HTMLVideoElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const inFlightRef = useRef(false);
  const intervalRef = useRef<number | null>(null);
  const historyRef = useRef<DetectionSample[]>([]);
  const stableObjectsRef = useRef<DetectedObject[]>([]);
  const lastStableAtRef = useRef(0);

  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [objects, setObjects] = useState<DetectedObject[]>([]);
  const [frameWidth, setFrameWidth] = useState(0);
  const [frameHeight, setFrameHeight] = useState(0);
  const [lastFrameId, setLastFrameId] = useState<string | null>(null);
  const [lastTimestamp, setLastTimestamp] = useState<string | null>(null);

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

  const captureFrame = useCallback(async (): Promise<Blob | null> => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;
    const sourceW = video.videoWidth;
    const sourceH = video.videoHeight;
    const scale = Math.min(1, 960 / sourceW);
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

  // Polling loop
  useEffect(() => {
    if (!enabled || !cameraReady) return;

    async function tick() {
      if (inFlightRef.current) return;
      inFlightRef.current = true;
      try {
        const blob = await captureFrame();
        if (!blob) return;
        const result: ScanFrameResponse = await scanFrame(blob);
        setObjects(stabilizeDetections(result.objects ?? [], Date.now()));
        setFrameWidth(result.frame_width);
        setFrameHeight(result.frame_height);
        const fid = `frame_${Date.now()}`;
        setLastFrameId(fid);
        setLastTimestamp(new Date().toISOString());
      } catch {
        // swallow — keep last detection visible (avoids flicker)
      } finally {
        inFlightRef.current = false;
      }
    }

    tick();
    intervalRef.current = window.setInterval(tick, intervalMs);
    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current);
    };
  }, [enabled, cameraReady, intervalMs, captureFrame]);

  return {
    videoRef,
    cameraReady,
    cameraError,
    objects,
    frameWidth,
    frameHeight,
    lastFrameId,
    lastTimestamp,
    scanning: enabled && cameraReady,
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
