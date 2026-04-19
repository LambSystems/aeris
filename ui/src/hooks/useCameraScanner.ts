import { useCallback, useEffect, useRef, useState } from "react";
import { scanFrame } from "@/lib/api";
import type { DetectedObject, ScanFrameResponse } from "@/lib/types";

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
        setObjects(result.objects ?? []);
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
}
