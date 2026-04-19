import type { DetectedObject } from "@/lib/types";

export function nonMaxSuppression(objects: DetectedObject[], iouThreshold = 0.45): DetectedObject[] {
  const sorted = [...objects].sort((a, b) => b.confidence - a.confidence);
  const selected: DetectedObject[] = [];

  for (const candidate of sorted) {
    const overlaps = selected.some(
      (current) => current.name === candidate.name && iou(current, candidate) > iouThreshold,
    );
    if (!overlaps) selected.push(candidate);
  }

  return selected;
}

function iou(a: DetectedObject, b: DetectedObject): number {
  const ax2 = a.bbox.x + a.bbox.width;
  const ay2 = a.bbox.y + a.bbox.height;
  const bx2 = b.bbox.x + b.bbox.width;
  const by2 = b.bbox.y + b.bbox.height;

  const ix1 = Math.max(a.bbox.x, b.bbox.x);
  const iy1 = Math.max(a.bbox.y, b.bbox.y);
  const ix2 = Math.min(ax2, bx2);
  const iy2 = Math.min(ay2, by2);
  const iw = Math.max(0, ix2 - ix1);
  const ih = Math.max(0, iy2 - iy1);
  const intersection = iw * ih;
  const union = a.bbox.width * a.bbox.height + b.bbox.width * b.bbox.height - intersection;
  return union <= 0 ? 0 : intersection / union;
}

