# Trash Detection Model

## Purpose

This document records the full custom trash-detection work done for Aeris so far:

- dataset annotation and export
- YOLO preprocessing and dataset preparation
- remote fine-tuning on Modal
- model quality improvements across training runs
- Streamlit integration for live webcam testing
- Streamlit integration for uploaded clip testing
- runtime and infrastructure fixes made along the way

This is the project history for the custom `can`, `paper`, and `bottle` detector.

---

## What This Adds To Aeris

The custom trash model is the computer-vision entry point for Aeris's waste detection flow.

Its contribution to the overall system is:

1. detect visible waste-like objects in camera frames
2. provide class labels and bounding boxes
3. feed those detections into the rest of the Aeris pipeline
4. support live demo experiences beyond the default generic YOLO classes

In practice, this work upgrades Aeris from:

- a generic detector with weak coverage for waste classes

to:

- a project-specific detector trained on the team's own labeled images for `can`, `paper`, and `bottle`

This matters because the default YOLO/COCO path was not reliable enough for cans and paper, and it also introduced bad label semantics for the project demo.

---

## Scope Of The Current Custom Model

The current fine-tuned model detects exactly three custom classes:

- `can`
- `paper`
- `bottle`

This is still a focused bootstrap detector, not a full general-purpose litter detector.

It is currently intended to:

- prove the custom-training path works end to end
- improve detection quality for the three most accessible demo classes
- support live bounding-box demos in Streamlit and local webcam testing

It does **not** yet cover:

- wrappers
- plastic bags
- bins
- cups
- mixed trash categories
- dirty surface detection
- scene-level notions like "messy" or "littered area"

---

## Dataset And Annotation History

### Early stage

The first stage of the work started with root folders like:

- `paper/`
- `can/`
- `bottle/`

That path supported fast weak-label dataset generation through:

- `backend/scripts/prepare_trash_dataset.py`

This was useful for experimentation, but weak centered-box labels were only a hackathon shortcut and were not good enough for reliable real object detection.

### Annotated dataset stage

After that, the workflow moved to annotated Roboflow-style COCO exports inside `new_dataset/`.

The project used multiple iterations of annotated exports, including:

- `new_dataset/My First Project.coco`
- `new_dataset/My First Project.coco (1)`
- `new_dataset/new dataset.coco`

The latest and strongest dataset so far is:

- `new_dataset/new dataset.coco`

This is the dataset used for the current best checkpoint.

---

## Annotation Work Completed So Far

The team has already done the important manual work of:

- collecting images for `paper`, `can`, and `bottle`
- annotating those objects with bounding boxes
- exporting the dataset in COCO format
- iterating the dataset with more images when the first runs underperformed

The biggest qualitative improvement in the annotation work was adding much more `paper`, since paper was badly underrepresented in the earlier dataset.

### Earlier annotated dataset

From the earlier COCO export used in the first serious custom runs:

- 147 total images
- 150 total annotations
- `can`: 71
- `paper`: 22
- `bottle`: 57

That dataset was enough to prove the pipeline worked, but it was too small and too imbalanced for robust performance.

### Newer dataset

From `new_dataset/new dataset.coco`:

- train: 511 images
- val: 90 images
- `can`: 169 annotations
- `paper`: 465 annotations
- `bottle`: 263 annotations

This dataset is much healthier, especially because the paper class now has far more coverage.

---

## Preprocessing And Dataset Preparation Work

The COCO export is converted into YOLO detection format by:

- `backend/scripts/prepare_roboflow_coco_dataset.py`

This script was improved during the project to do more than a naive copy-and-convert.

### Current preprocessing behavior

The prep path now:

1. locates the newest COCO export under `new_dataset`
2. reads COCO images and annotations
3. maps class names into Aeris training labels:
   - `Can -> can`
   - `Paper -> paper`
   - `Water Bottle -> bottle`
4. enforces stable class ordering:
   - `can`
   - `paper`
   - `bottle`
5. converts COCO XYWH boxes into YOLO center-width-height format
6. clips invalid boxes to image boundaries
7. skips unusable annotations
8. re-saves copied images during dataset build
9. creates train/val splits when the export only contains one split
10. writes a `dataset_report.json` summary

### Why this preprocessing matters

These changes were added specifically to improve training stability and data quality:

- box clipping prevents malformed labels
- stable class order avoids checkpoint confusion between runs
- image re-save reduces problems from odd or partially corrupt source files
- a dataset report makes the pipeline auditable

### Key files

- `backend/scripts/prepare_roboflow_coco_dataset.py`
- `backend/datasets/trash_coco_yolo/`

---

## Fine-Tuning Pipeline

Remote training is handled by:

- `backend/scripts/modal_train_yolo.py`

The script:

1. finds the newest COCO dataset export under `new_dataset`
2. converts it to YOLO format locally
3. uploads the dataset to the Modal volume `aeris-yolo-trash-dataset`
4. fine-tunes `yolov8m.pt` on an NVIDIA L4 GPU
5. writes checkpoints and training artifacts to the Modal volume `aeris-yolo-trash-checkpoints`

### Training configuration used

- base model: `yolov8m.pt`
- epochs: `30`
- image size: `640`
- batch size: `16`
- patience: `8`
- hardware: Modal `L4`

### Important training infrastructure fixes made

Several real issues had to be solved before training stabilized:

1. **Windows delete permission problems**
   - fixed by adding safer removal behavior for generated datasets

2. **Missing `libGL.so.1` in Modal**
   - fixed by adding Debian packages for OpenCV runtime

3. **Bad dataset path handling inside Modal**
   - fixed by rewriting `data.yaml` paths for the mounted remote dataset

4. **Ultralytics + NumPy 2.x incompatibility**
   - fixed by pinning `numpy==1.26.4`

5. **Ultralytics font download failure**
   - fixed by adding `curl` to the Modal image

6. **COCO export folder naming instability**
   - fixed by making the training script auto-discover the newest dataset export under `new_dataset`

These are all part of the real model-delivery work, not just training itself.

---

## Training Run History

### `trash-quick-v2`

This was the first meaningful custom run on the small annotated dataset.

Rough result:

- best `mAP50`: about `0.59`
- best `mAP50-95`: about `0.56`

Interpretation:

- good enough to prove the path worked
- not good enough for reliable paper/can/bottle differentiation
- bottle/can confusion remained common
- small and far-away objects remained weak

### `trash-quick-v3`

This run used a stronger updated dataset than `v2`, especially with more paper.

Rough result:

- best `mAP50`: about `0.65`
- best `mAP50-95`: about `0.59`

Interpretation:

- clear improvement over `v2`
- better balance
- still not where we wanted it to be

### `trash-quick-v4`

This is the current strongest run and the recommended checkpoint.

Validation result for the best checkpoint:

- overall `mAP50`: `0.895`
- overall `mAP50-95`: `0.848`

Per-class results:

- `can`
  - `mAP50`: `0.868`
  - `mAP50-95`: `0.859`
- `paper`
  - `mAP50`: `0.950`
  - `mAP50-95`: `0.931`
- `bottle`
  - `mAP50`: `0.867`
  - `mAP50-95`: `0.753`

This run is the current best representation of the custom model.

---

## Current Recommended Checkpoint

Use:

- `backend/models/trash-quick-v4-best.pt`

This checkpoint was downloaded from the Modal volume after the `trash-quick-v4` run completed.

It is the model currently recommended for:

- Streamlit live camera
- Streamlit uploaded clip processing
- local detector experiments

---

## Augmentation And Accuracy Notes

### Was augmentation used?

Yes.

Ultralytics default augmentation was part of training, including common operations such as:

- mosaic
- horizontal flip
- translation
- scale
- HSV color augmentation

So the earlier poor accuracy was **not** mainly caused by "no augmentation."

### What actually improved accuracy?

The biggest improvements came from:

- more labeled data
- better class balance
- much more `paper`
- repeated retraining on improved exports

### Why the model was weak earlier

The early limitations came mostly from:

- too little data overall
- very weak `paper` representation
- not enough far-away examples
- not enough multi-object clutter
- bottle/can visual similarity

### Why the latest model is better

The latest model improved because:

- the dataset is much larger
- the paper class has real coverage now
- class balance is much healthier
- preprocessing got more robust
- the training pipeline became reproducible

---

## Runtime Integration Work

The custom model work was not just about training. It was also integrated into the running app.

### `yolo_service.py`

`backend/app/cv/yolo_service.py` was updated so Aeris no longer forces awkward remapped labels from earlier demo logic.

Important changes:

- labels now keep their original names
- class display is no longer forced into unrelated Aeris aliases
- the system can surface raw class names more honestly

### `realtime_yolo.py`

`backend/scripts/realtime_yolo.py` was added and improved as a local webcam detector.

Features added:

- normal YOLO tracking mode
- optional YOLO-World prompt mode
- `imgsz` controls
- `frame-skip` controls
- live FPS and inference overlays

This script became the fastest local path for direct webcam testing.

### Streamlit live integration

`backend/streamlit_app.py` was upgraded substantially.

It now supports:

- loading the selected custom checkpoint via `YOLO_MODEL_PATH`
- live webcam detection
- real-time bounding boxes
- lower-latency settings
- FPS overlay
- inference-size control
- frame skipping

### Fixes made in Streamlit integration

The following issues were identified and fixed:

1. old demo mapping was forcing wrong semantics such as bottle behaving like a fake can class
2. Streamlit was originally hardcoded to `yolov8n.pt`
3. `streamlit-webrtc` dependencies were missing locally
4. live inference was too slow because it was running full model inference every frame

### Uploaded clip integration

Streamlit was also extended to support uploaded video clips.

That feature now includes:

- upload a local video clip
- process it with the same custom model
- draw bounding boxes into the output clip
- preview the result in-browser
- download the processed clip

### Clip-processing improvements made

The upload workflow was refined because the first version was too heavy and not browser-friendly.

Fixes included:

- source-frame sampling
- max processed frame limits
- browser-friendlier MP4 output generation
- clip download support

---

## How To Run The Current Model

### Streamlit

From the repo root:

```powershell
cd backend
$env:YOLO_MODEL_PATH = (Resolve-Path ".\models\trash-quick-v4-best.pt").Path
.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8507
```

### Modal retraining

From `backend/`:

```powershell
$env:PYTHONIOENCODING='utf-8'
.venv\Scripts\modal.exe run scripts\modal_train_yolo.py --epochs 30 --imgsz 640 --batch 16 --patience 8 --run-name trash-quick-v5
```

Because the training script now auto-discovers the newest COCO export under `new_dataset`, you do not need to hardcode the dataset folder path anymore.

---

## Files That Were Central To This Work

### Data and training

- `backend/scripts/prepare_trash_dataset.py`
- `backend/scripts/prepare_roboflow_coco_dataset.py`
- `backend/scripts/modal_train_yolo.py`
- `backend/datasets/trash_coco_yolo/`
- `backend/models/trash-quick-v4-best.pt`

### Runtime integration

- `backend/app/cv/yolo_service.py`
- `backend/scripts/realtime_yolo.py`
- `backend/streamlit_app.py`

### Documentation

- `docs/trash-model.md`
- `docs/yolo-integration.md`
- `backend/README.md`

---

## Current Status

As of now, the project has:

- a custom annotated dataset workflow
- a hardened COCO-to-YOLO preprocessing path
- a reproducible Modal fine-tuning pipeline
- a strong `v4` custom checkpoint
- live webcam integration
- uploaded-clip processing support

The current detector is now a real project-specific model rather than a placeholder demo detector.

---

## Summary

The work completed so far includes:

- manually annotating custom datasets for `can`, `paper`, and `bottle`
- iterating the dataset when early performance was weak
- building a preprocessing pipeline that converts and sanitizes COCO exports for YOLO
- fine-tuning multiple YOLO runs on Modal
- debugging the training infrastructure until it became stable
- integrating the trained model into Streamlit and local realtime tools
- improving usability with FPS controls and uploaded-clip support

This is the full custom trash-model track inside Aeris so far.

