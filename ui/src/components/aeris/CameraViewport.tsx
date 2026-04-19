import { useEffect, useRef } from "react";
import type { DetectedObject } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Camera, Loader2 } from "lucide-react";
import { formatObjectName, formatConfidence } from "@/lib/format";

interface CameraViewportProps {
  videoRef: React.RefObject<HTMLVideoElement>;
  /** Live ref the hook writes post-NMS detections into. Read every animation frame. */
  objectsRef: React.MutableRefObject<DetectedObject[]>;
  /** Live ref with source frame dimensions for the canvas draw's scale calc. */
  frameSizeRef: React.MutableRefObject<{ width: number; height: number }>;
  scanning: boolean;
  cameraReady: boolean;
  hasDetections: boolean;
  errorMessage?: string | null;
}

export function CameraViewport({
  videoRef,
  objectsRef,
  frameSizeRef,
  scanning,
  cameraReady,
  hasDetections,
  errorMessage,
}: CameraViewportProps) {
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  // Canvas pixel size cache — only rewritten when the container actually resizes.
  const sizeRef = useRef({ width: 0, height: 0, dpr: 1 });

  // Set canvas dimensions once and on container resize ONLY. Resetting canvas.width/height
  // reallocates the backing buffer, so doing it every frame is a massive perf hit.
  useEffect(() => {
    const canvas = overlayRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      const nextW = Math.round(rect.width);
      const nextH = Math.round(rect.height);
      if (nextW === sizeRef.current.width && nextH === sizeRef.current.height && dpr === sizeRef.current.dpr) {
        return;
      }
      canvas.width = nextW * dpr;
      canvas.height = nextH * dpr;
      canvas.style.width = `${nextW}px`;
      canvas.style.height = `${nextH}px`;
      sizeRef.current = { width: nextW, height: nextH, dpr };
    };

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);
    return () => ro.disconnect();
  }, []);

  // Single rAF loop: draws the video frame + boxes into one canvas each animation frame.
  // The <video> element is hidden — it's only the pixel source for drawImage.
  useEffect(() => {
    const canvas = overlayRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    let raf = 0;
    let running = true;
    const stroke = getCssVar("--detect-stroke");

    const draw = () => {
      if (!running) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) {
        raf = requestAnimationFrame(draw);
        return;
      }

      const { width, height, dpr } = sizeRef.current;
      if (!width || !height) {
        raf = requestAnimationFrame(draw);
        return;
      }

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);

      const videoW = video.videoWidth;
      const videoH = video.videoHeight;
      if (!videoW || !videoH || video.readyState < 2) {
        raf = requestAnimationFrame(draw);
        return;
      }

      // object-cover mapping: fill the container, crop overflow evenly.
      const scale = Math.max(width / videoW, height / videoH);
      const dispW = videoW * scale;
      const dispH = videoH * scale;
      const offsetX = (width - dispW) / 2;
      const offsetY = (height - dispH) / 2;

      // 1. Draw the live video frame directly onto the canvas.
      ctx.drawImage(video, offsetX, offsetY, dispW, dispH);

      // 2. Overlay detection boxes using the same coord space as the video pixels.
      // Detection coords are in the inference-source frame space, which may differ
      // from video.videoWidth/Height, so scale from frameSizeRef if it's populated.
      const frameSize = frameSizeRef.current;
      const sourceW = frameSize.width || videoW;
      const sourceH = frameSize.height || videoH;
      const boxScaleX = dispW / sourceW;
      const boxScaleY = dispH / sourceH;

      ctx.lineWidth = 2;
      ctx.font = "600 12px ui-sans-serif, system-ui, sans-serif";
      ctx.strokeStyle = `hsl(${stroke})`;
      ctx.shadowColor = `hsl(${stroke} / 0.4)`;

      const objects = objectsRef.current;
      for (let i = 0; i < objects.length; i++) {
        const o = objects[i];
        const x = offsetX + o.bbox.x * boxScaleX;
        const y = offsetY + o.bbox.y * boxScaleY;
        const w = o.bbox.width * boxScaleX;
        const h = o.bbox.height * boxScaleY;

        ctx.shadowBlur = 6;
        roundRect(ctx, x, y, w, h, 8);
        ctx.stroke();
        ctx.shadowBlur = 0;

        ctx.lineWidth = 3;
        const tick = Math.min(18, w / 4, h / 4);
        cornerTicks(ctx, x, y, w, h, tick);
        ctx.lineWidth = 2;

        const label = `${formatObjectName(o.name)} · ${formatConfidence(o.confidence)}`;
        const padX = 8;
        const padY = 4;
        const metrics = ctx.measureText(label);
        const labelW = metrics.width + padX * 2;
        const labelH = 22;
        const labelY = Math.max(0, y - labelH - 4);
        ctx.fillStyle = `hsl(${stroke} / 0.95)`;
        roundRect(ctx, x, labelY, labelW, labelH, 6);
        ctx.fill();
        ctx.fillStyle = "hsl(215 28% 9%)";
        ctx.fillText(label, x + padX, labelY + labelH - padY - 2);
      }

      raf = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      running = false;
      cancelAnimationFrame(raf);
    };
  }, [objectsRef, frameSizeRef, videoRef]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative aspect-[16/10] w-full overflow-hidden rounded-xl border bg-foreground/95",
        "shadow-[0_1px_0_hsl(var(--border)),0_24px_60px_-30px_hsl(var(--foreground)/0.35)]",
      )}
    >
      {/* Hidden source — the canvas samples frames from this element via drawImage. */}
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        aria-hidden
        style={{ position: "absolute", width: 1, height: 1, opacity: 0, pointerEvents: "none" }}
      />
      {/* The single surface the user actually sees: video frame + boxes composited. */}
      <canvas
        ref={overlayRef}
        className="block h-full w-full"
      />

      {/* Cinematic frame */}
      <div className="pointer-events-none absolute inset-3 rounded-lg ring-1 ring-background/15" />
      {scanning && cameraReady ? (
        <div className="scan-shimmer pointer-events-none absolute inset-0" />
      ) : null}

      {/* Corner brand */}
      <div className="pointer-events-none absolute left-4 top-4 flex items-center gap-2 rounded-full bg-background/85 px-2.5 py-1 text-[10.5px] font-medium uppercase tracking-wider text-foreground backdrop-blur">
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            scanning ? "bg-primary animate-pulse-soft" : "bg-muted-foreground",
          )}
        />
        {scanning ? "Live scan" : "Standby"}
      </div>

      {/* Empty / loading states */}
      {!cameraReady && !errorMessage ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-foreground/95 text-background/85">
          <Camera className="h-8 w-8 opacity-70" strokeWidth={1.75} />
          <p className="text-sm">Requesting camera access…</p>
        </div>
      ) : null}

      {errorMessage ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-foreground/95 px-6 text-center text-background/85">
          <Camera className="h-8 w-8 opacity-70" strokeWidth={1.75} />
          <p className="text-sm">{errorMessage}</p>
        </div>
      ) : null}

      {cameraReady && scanning && !hasDetections ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-4 flex justify-center">
          <div className="flex items-center gap-2 rounded-full bg-background/85 px-3 py-1.5 text-xs text-muted-foreground backdrop-blur">
            <Loader2 className="h-3 w-3 animate-spin" />
            Looking for recyclable objects…
          </div>
        </div>
      ) : null}
    </div>
  );
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

function cornerTicks(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  t: number,
) {
  ctx.beginPath();
  // TL
  ctx.moveTo(x, y + t);
  ctx.lineTo(x, y);
  ctx.lineTo(x + t, y);
  // TR
  ctx.moveTo(x + w - t, y);
  ctx.lineTo(x + w, y);
  ctx.lineTo(x + w, y + t);
  // BR
  ctx.moveTo(x + w, y + h - t);
  ctx.lineTo(x + w, y + h);
  ctx.lineTo(x + w - t, y + h);
  // BL
  ctx.moveTo(x + t, y + h);
  ctx.lineTo(x, y + h);
  ctx.lineTo(x, y + h - t);
  ctx.stroke();
}

function getCssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
