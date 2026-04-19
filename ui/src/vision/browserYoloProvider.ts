import * as ort from "onnxruntime-web";

import type { DetectedObject, ScanFrameResponse } from "@/lib/types";
import { nonMaxSuppression } from "./nms";
import type { VisionProvider } from "./types";

const MODEL_SIZE = 640;
const MODEL_PATH = "/models/yolo/best.onnx";
const CLASSES_PATH = "/models/yolo/classes.json";
const CONFIDENCE_THRESHOLD = 0.25;

type LetterboxMeta = {
  sourceWidth: number;
  sourceHeight: number;
  scale: number;
  padX: number;
  padY: number;
};

export async function createBrowserYoloProvider(): Promise<VisionProvider> {
  ort.env.wasm.wasmPaths = "/ort/";
  ort.env.wasm.numThreads = 1;

  const [session, classNames] = await Promise.all([
    ort.InferenceSession.create(MODEL_PATH, {
      executionProviders: ["wasm"],
      graphOptimizationLevel: "all",
    }),
    loadClassNames(),
  ]);

  return {
    source: "browser_yolo",
    async detect(blob: Blob): Promise<ScanFrameResponse> {
      const { tensor, meta } = await preprocess(blob);
      const inputName = session.inputNames[0];
      const output = await session.run({ [inputName]: tensor });
      const outputName = session.outputNames[0];
      const objects = parseYoloV8Output(output[outputName], classNames, meta);
      return {
        objects,
        source: "browser_yolo",
        frame_width: meta.sourceWidth,
        frame_height: meta.sourceHeight,
      };
    },
    async dispose() {
      await session.release();
    },
  };
}

async function loadClassNames(): Promise<string[]> {
  const response = await fetch(CLASSES_PATH, { cache: "no-store" });
  if (!response.ok) throw new Error("Missing YOLO classes.json");
  const data = (await response.json()) as unknown;
  if (Array.isArray(data)) return data.map(String);
  if (data && typeof data === "object" && "names" in data && Array.isArray(data.names)) {
    return data.names.map(String);
  }
  throw new Error("Invalid YOLO classes.json");
}

async function preprocess(blob: Blob): Promise<{ tensor: ort.Tensor; meta: LetterboxMeta }> {
  const bitmap = await createImageBitmap(blob);
  const sourceWidth = bitmap.width;
  const sourceHeight = bitmap.height;
  const scale = Math.min(MODEL_SIZE / sourceWidth, MODEL_SIZE / sourceHeight);
  const resizedWidth = Math.round(sourceWidth * scale);
  const resizedHeight = Math.round(sourceHeight * scale);
  const padX = Math.floor((MODEL_SIZE - resizedWidth) / 2);
  const padY = Math.floor((MODEL_SIZE - resizedHeight) / 2);

  const canvas = document.createElement("canvas");
  canvas.width = MODEL_SIZE;
  canvas.height = MODEL_SIZE;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Canvas unavailable");
  ctx.fillStyle = "rgb(114,114,114)";
  ctx.fillRect(0, 0, MODEL_SIZE, MODEL_SIZE);
  ctx.drawImage(bitmap, padX, padY, resizedWidth, resizedHeight);
  bitmap.close();

  const pixels = ctx.getImageData(0, 0, MODEL_SIZE, MODEL_SIZE).data;
  const input = new Float32Array(1 * 3 * MODEL_SIZE * MODEL_SIZE);
  const planeSize = MODEL_SIZE * MODEL_SIZE;

  for (let i = 0, pixel = 0; pixel < planeSize; pixel++, i += 4) {
    input[pixel] = pixels[i] / 255;
    input[planeSize + pixel] = pixels[i + 1] / 255;
    input[planeSize * 2 + pixel] = pixels[i + 2] / 255;
  }

  return {
    tensor: new ort.Tensor("float32", input, [1, 3, MODEL_SIZE, MODEL_SIZE]),
    meta: { sourceWidth, sourceHeight, scale, padX, padY },
  };
}

function parseYoloV8Output(tensor: ort.Tensor, classNames: string[], meta: LetterboxMeta): DetectedObject[] {
  const data = tensor.data as Float32Array;
  const dims = tensor.dims;
  const rows = normalizeRows(data, dims);
  const detections: DetectedObject[] = [];

  for (const row of rows) {
    const parsed = parseDetectionRow(row, classNames, meta);
    if (parsed) detections.push(parsed);
  }

  return nonMaxSuppression(detections, 0.45).slice(0, 5);
}

function normalizeRows(data: Float32Array, dims: readonly number[]): Float32Array[] {
  const a = dims[dims.length - 2];
  const b = dims[dims.length - 1];
  if (!a || !b) return [];

  const rows: Float32Array[] = [];
  if (a <= b && a < 256) {
    for (let col = 0; col < b; col++) {
      const row = new Float32Array(a);
      for (let channel = 0; channel < a; channel++) {
        row[channel] = data[channel * b + col];
      }
      rows.push(row);
    }
  } else {
    for (let rowIndex = 0; rowIndex < a; rowIndex++) {
      rows.push(data.slice(rowIndex * b, rowIndex * b + b));
    }
  }
  return rows;
}

function parseDetectionRow(row: Float32Array, classNames: string[], meta: LetterboxMeta): DetectedObject | null {
  if (row.length < 5) return null;

  const hasObjectness = row.length === classNames.length + 5;
  const classOffset = hasObjectness ? 5 : 4;
  const objectness = hasObjectness ? row[4] : 1;

  let classIndex = -1;
  let classScore = 0;
  for (let i = classOffset; i < row.length; i++) {
    if (row[i] > classScore) {
      classScore = row[i];
      classIndex = i - classOffset;
    }
  }

  const confidence = objectness * classScore;
  if (confidence < CONFIDENCE_THRESHOLD || classIndex < 0) return null;

  const cx = row[0];
  const cy = row[1];
  const w = row[2];
  const h = row[3];
  const x1 = (cx - w / 2 - meta.padX) / meta.scale;
  const y1 = (cy - h / 2 - meta.padY) / meta.scale;
  const x2 = (cx + w / 2 - meta.padX) / meta.scale;
  const y2 = (cy + h / 2 - meta.padY) / meta.scale;

  const x = clamp(x1, 0, meta.sourceWidth);
  const y = clamp(y1, 0, meta.sourceHeight);
  const width = clamp(x2, 0, meta.sourceWidth) - x;
  const height = clamp(y2, 0, meta.sourceHeight) - y;
  if (width <= 1 || height <= 1) return null;

  return {
    name: classNames[classIndex] ?? `class_${classIndex}`,
    confidence,
    distance: 1,
    reachable: true,
    bbox: { x, y, width, height },
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

