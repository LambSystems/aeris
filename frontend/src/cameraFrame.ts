export interface CapturedFrame {
  frame: Blob;
  imageWidth: number;
  imageHeight: number;
}

export function captureVideoFrame(
  video: HTMLVideoElement,
  type = "image/jpeg",
  quality = 0.72,
): Promise<CapturedFrame> {
  const imageWidth = video.videoWidth;
  const imageHeight = video.videoHeight;

  if (imageWidth <= 0 || imageHeight <= 0) {
    return Promise.reject(new Error("Camera video is not ready to capture a frame."));
  }

  const canvas = document.createElement("canvas");
  canvas.width = imageWidth;
  canvas.height = imageHeight;

  const context = canvas.getContext("2d");
  if (!context) {
    return Promise.reject(new Error("Could not create a canvas context for frame capture."));
  }

  context.drawImage(video, 0, 0, imageWidth, imageHeight);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (frame) => {
        if (!frame) {
          reject(new Error("Could not encode camera frame."));
          return;
        }

        resolve({ frame, imageWidth, imageHeight });
      },
      type,
      quality,
    );
  });
}
