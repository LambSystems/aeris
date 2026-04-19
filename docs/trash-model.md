# Trash Detection Model

## What This Adds To Aeris

This model is the CV entry point for the waste-facing part of Aeris.

Its role in the full project is:

1. detect visible waste-related objects in the live camera feed
2. convert those detections into structured scene context
3. pass that context into the Aeris reasoning and recommendation flow

In practical terms, the trash model gives Aeris a way to see common cleanup targets before the rest of the system decides what action to recommend.

---

## Current Model Scope

The current fine-tuned model is a 3-class detector:

- `can`
- `paper`
- `bottle`

This is a narrow bootstrap model, not a general litter detector yet.

It is useful for:

- proving that Aeris can swap from a generic COCO detector to a project-specific detector
- demoing live bounding boxes on custom classes
- establishing the training and deployment path for future waste classes

It does **not** yet cover broader trash categories such as wrappers, bins, bags, food containers, or mixed litter scenes.

---

## Dataset Source

The model was trained from the annotated export in:

`new_dataset/My First Project.coco`

That source was converted into YOLO format by:

`backend/scripts/prepare_roboflow_coco_dataset.py`

The converted dataset is written to:

`backend/datasets/trash_coco_yolo`

---

## Annotation Summary

The current annotated dataset contains:

- 147 total images
- 150 total annotations
- 3 labeled classes

Class counts:

- `can`: 71 annotations
- `paper`: 22 annotations
- `bottle`: 57 annotations

Train/validation split created during conversion:

- train: 125 images
- val: 22 images

Important limitation: `paper` is badly underrepresented relative to `can` and `bottle`, which is one reason its performance is weaker.

---

## Training Process

### Conversion

The annotated COCO export is converted to YOLO detection format locally:

```powershell
cd backend
.venv\Scripts\python.exe scripts\prepare_roboflow_coco_dataset.py
```

### Remote Training

Training is run on Modal with an NVIDIA L4 GPU:

```powershell
cd backend
modal run scripts/modal_train_yolo.py --epochs 30 --imgsz 640 --batch 16 --patience 8 --run-name trash-quick-v2
```

What this script does:

1. converts the annotated COCO export into YOLO layout
2. uploads the dataset to the Modal volume `aeris-yolo-trash-dataset`
3. fine-tunes `yolov8m.pt`
4. writes checkpoints and training artifacts to `aeris-yolo-trash-checkpoints`

Training implementation:

- script: `backend/scripts/modal_train_yolo.py`
- base checkpoint: `yolov8m.pt`
- epochs: 30
- image size: 640
- batch size: 16
- patience: 8
- hardware: Modal L4 GPU

---

## Augmentation

Yes, augmentation was used.

Ultralytics YOLOv8 training enabled its default augmentations during this run, including settings such as:

- mosaic
- horizontal flip
- scale
- translate
- HSV color augmentation

So the current limitations are **not** mainly explained by "no augmentation."

The bigger issues are:

- too little data overall
- too little `paper` data specifically
- too few far-away examples
- too few cluttered multi-object scenes
- visual similarity between cans and bottles in some views

---

## Rough Accuracy To Expect

From the completed `trash-quick-v2` run:

- best validation `mAP50`: about `0.59`
- best validation `mAP50-95`: about `0.56`
- validation precision at the best checkpoint: about `0.47`
- validation recall at the best checkpoint: about `0.97`

These numbers mean the model is usable as an early prototype, but not yet reliable enough to describe as production-grade.

### Real-world expectation

Users should expect:

- close, clear, centered bottles and cans: often detected
- paper: less reliable than bottle/can
- far-away objects: often missed
- multiple overlapping objects: more confusion
- visually ambiguous items: bottle/can mixups can happen

For a demo, the honest framing is:

> The current custom model is a proof-of-capability detector with moderate accuracy on three custom waste classes. It works best on close, well-lit objects with limited scene clutter.

---

## Why Accuracy Drops In Practice

### 1. Small objects are hard

Far-away objects occupy very few pixels, so the model gets less shape detail.

### 2. The classes are visually similar

A bottle and a can can share:

- reflective surfaces
- cylindrical shape
- similar color patterns

That confusion is normal in a small dataset.

### 3. `paper` is underrepresented

`paper` has only 22 annotations, so the model has not seen enough examples of:

- flat paper
- crumpled paper
- folded paper
- different backgrounds

### 4. The dataset likely lacks enough clutter

If most training images show one dominant object, the model will struggle more when:

- several objects appear together
- objects overlap
- the background is busy

### 5. Fast inference settings reduce small-object quality

When Streamlit is run with smaller inference sizes like `256` or `320`, FPS improves, but far-away and small objects become harder to detect.

---

## Recommendations To Improve Accuracy

If the goal is better accuracy rather than just a working demo, this is the order I recommend.

### 1. Add more labeled data before changing the model

This is the highest-value improvement.

Recommended target:

- at least 150 to 300 labeled instances per class
- especially more `paper`
- include clean, crushed, bent, partially hidden, and background-heavy examples

### 2. Add distance diversity

Deliberately collect examples at:

- close range
- medium range
- far range

If you do not train on far-away objects, the model will keep wanting the object to be close.

### 3. Add cluttered scenes

Collect images with:

- can + bottle together
- paper near bottle
- several trash items in one frame
- partial occlusion

This directly addresses the "many objects on screen clash" problem.

### 4. Fix class balance

The current imbalance hurts `paper`.

The simplest fix is to add more paper images first, not to tune hyperparameters first.

### 5. Keep the fine-tuned model at a higher inference size when accuracy matters

For demo speed:

- `imgsz 256-320` is fine

For better accuracy:

- prefer `imgsz 512-640`

This matters especially for small and far-away items.

### 6. Only after more data, consider model or training changes

Good next experiments after dataset improvement:

- train longer with the larger dataset
- compare `yolov8m` vs `yolov8s`
- try higher-resolution training if small-object detection remains weak
- add more class-specific cleanup for ambiguous labels

---

## What I Would Recommend Right Now

If time is limited, do this:

1. keep the current model for the demo as a custom-model proof point
2. be explicit that it is best on close objects
3. add more labeled `paper` images first
4. add mixed scenes with can + bottle + paper together
5. retrain once the dataset is materially larger

If you only make one change, make it this:

> add a lot more labeled images, especially far-away paper examples and cluttered scenes

That will help more than chasing augmentation tweaks.

---

## Relevant Files

- `backend/scripts/prepare_roboflow_coco_dataset.py`
- `backend/scripts/modal_train_yolo.py`
- `backend/models/trash-quick-v2-best.pt`
- `backend/streamlit_app.py`
- `backend/scripts/realtime_yolo.py`

