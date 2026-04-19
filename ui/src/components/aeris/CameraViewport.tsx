import { useEffect, useRef } from "react";
import type { DetectedObject } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Camera, Loader2 } from "lucide-react";
import { formatObjectName, formatConfidence } from "@/lib/format";

interface CameraViewportProps {
  videoRef: React.RefObject<HTMLVideoElement>;
  objects: DetectedObject[];
  frameWidth: number;
  frameHeight: number;
  scanning: boolean;
  cameraReady: boolean;
  errorMessage?: string | null;
}

export function CameraViewport({
  videoRef,
  objects,
  frameWidth,
  frameHeight,
  scanning,
  cameraReady,
  errorMessage,
}: CameraViewportProps) {
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Draw bounding boxes; redraws when objects change or container resizes.
  useEffect(() => {
    const canvas = overlayRef.current;
    const container = containerRef.current;
    const video = videoRef.current;
    if (!canvas || !container || !video) return;

    const draw = () => {
      const rect = container.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, rect.width, rect.height);

      const sourceW = frameWidth || video.videoWidth || rect.width;
      const sourceH = frameHeight || video.videoHeight || rect.height;
      if (!sourceW || !sourceH) return;

      // object-cover style mapping (video is object-cover in DOM)
      const scale = Math.max(rect.width / sourceW, rect.height / sourceH);
      const dispW = sourceW * scale;
      const dispH = sourceH * scale;
      const offsetX = (rect.width - dispW) / 2;
      const offsetY = (rect.height - dispH) / 2;

      const stroke = getCssVar("--detect-stroke");
      ctx.lineWidth = 2;
      ctx.font = "600 12px ui-sans-serif, system-ui, sans-serif";

      objects.forEach((o) => {
        const x = offsetX + o.bbox.x * scale;
        const y = offsetY + o.bbox.y * scale;
        const w = o.bbox.width * scale;
        const h = o.bbox.height * scale;

        ctx.strokeStyle = `hsl(${stroke})`;
        ctx.shadowColor = `hsl(${stroke} / 0.4)`;
        ctx.shadowBlur = 6;
        roundRect(ctx, x, y, w, h, 8);
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Corner ticks
        ctx.lineWidth = 3;
        const tick = Math.min(18, w / 4, h / 4);
        cornerTicks(ctx, x, y, w, h, tick);

        // Label pill
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
      });
    };

    draw();
    const ro = new ResizeObserver(draw);
    ro.observe(container);
    return () => ro.disconnect();
  }, [objects, frameWidth, frameHeight, videoRef]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative aspect-[16/10] w-full overflow-hidden rounded-xl border bg-foreground/95",
        "shadow-[0_1px_0_hsl(var(--border)),0_24px_60px_-30px_hsl(var(--foreground)/0.35)]",
      )}
    >
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="h-full w-full object-cover"
      />
      <canvas
        ref={overlayRef}
        className="pointer-events-none absolute inset-0 h-full w-full"
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

      {cameraReady && scanning && objects.length === 0 ? (
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
