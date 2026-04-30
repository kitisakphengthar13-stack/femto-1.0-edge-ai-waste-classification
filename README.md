# Femto 1.0 — Edge AI Waste Classification System

Femto 1.0 is an Edge AI-based waste classification system deployed on NVIDIA Jetson Orin Nano.  
The system uses a YOLO object detection model to detect and classify waste items from a camera input, maps each detected object into a waste category, and controls a servo-based sorting mechanism to move the item into the correct bin.

This project demonstrates an end-to-end Computer Vision and Edge AI pipeline, including model training, TensorRT deployment, real-time inference, motion-triggered processing, hardware control, voice feedback, YAML-based configuration, and safe shutdown handling.

---

## Demo

YouTube Demo: [Watch the demo](https://www.youtube.com/watch?v=EHQ0HLIj6ms)

---

## System Preview

![Prototype Overview](docs/images/prototype_overview.png)

---

## Project Overview

The model was trained using a custom dataset containing 10 waste classes.  
These classes are mapped into 4 main waste categories used by the sorting system:

- Recyclable waste
- General waste
- Organic waste
- Hazardous waste

During development and training, the system used a YOLO model in `.pt` format.  
For deployment on NVIDIA Jetson Orin Nano, the model was converted into TensorRT `.engine` format as an optimized deployment format for NVIDIA edge hardware.

The full system integrates camera-based image acquisition, YOLO-based object detection, waste class-to-category mapping, decision buffering, servo motor control using PWM, voice feedback, and shutdown card detection for safe system shutdown.

The current runtime has been refactored into a more maintainable structure.  
The main entry point loads YAML configuration files, starts the FEMTO application, and delegates the runtime logic to modules inside `src/femto/`.

---

## Detection Example

![Detection Example](docs/images/detection_example.png)

---

## Key Results

| Metric | Result |
|---|---:|
| Overall software accuracy | 93.3% |
| Average hardware sorting time | 1.80 seconds / item |
| Waste classes | 10 classes |
| Waste categories | 4 categories |
| Deployment device | NVIDIA Jetson Orin Nano |
| Deployment model format | TensorRT `.engine` |

The software accuracy value represents the overall average accuracy across all 10 waste classes from real system testing.  
The hardware sorting time represents the overall average time required to convey and sort one waste item into the target bin across all 10 classes from real physical sorting tests.

These values are system-level test results from the actual prototype, not YOLO validation metrics such as mAP, precision, or recall.

---

## Key Features

- YOLO-based waste object detection
- Custom-trained dataset with 10 waste classes
- Waste mapping into 4 sorting categories
- TensorRT `.engine` model deployment
- Real-time inference on NVIDIA Jetson Orin Nano
- CSI camera input using GStreamer pipeline
- Motion-triggered inference to reduce unnecessary YOLO processing
- Servo-based physical sorting mechanism
- PWM-based actuator control
- Non-blocking servo finite-state control
- Consecutive detection buffering to reduce unstable predictions
- YAML-based runtime configuration
- Voice feedback system for user interaction
- Shutdown card detection for safe system shutdown
- Safe cleanup for camera, GPIO, audio, and PWM resources

---

## System Pipeline

```text
CSI Camera
    ↓
Frame Capture
    ↓
Motion Detection
    ↓
YOLO TensorRT Inference
    ↓
Waste Class Prediction
    ↓
Class-to-Category Mapping
    ↓
Decision Buffering
    ↓
Servo Angle Selection
    ↓
Physical Sorting Mechanism
    ↓
Voice Feedback / System Status
```

![System Flowchart](docs/images/system_flowchart.png)

---

## Runtime Software Flow

```text
scripts/run_system.py
    ↓
Load configs/system_config.yaml
Load configs/class_mapping.yaml
    ↓
src/femto/app.py
    ↓
Initialize model, camera, audio, and servo controller
    ↓
Run motion-triggered inference loop
    ↓
Map YOLO class to waste category
    ↓
Confirm prediction using decision buffering
    ↓
Trigger servo sorting and voice feedback
```

The runtime is designed to keep the entry point simple.  
`scripts/run_system.py` is responsible for loading configuration files and starting the application.  
The main runtime behavior is handled inside `src/femto/app.py`.

---

## Sorting Mechanism

The physical sorting mechanism uses two servo motors controlled through PWM signals.

| Pin | Role | Description |
|---|---|---|
| 32 | Rotation servo | Rotates the mechanism toward the target bin |
| 33 | Tilt servo | Tilts the mechanism to release the waste item |

The rotation servo on pin 32 releases its PWM signal after movement to reduce mechanical jitter, while the tilt servo on pin 33 keeps its PWM signal active to maintain the mechanism position.

Servo pin numbers, PWM frequency, home position, category positions, and timing values are defined in `configs/system_config.yaml`.

---

## Waste Classes and Categories

| Waste Class | Category |
|---|---|
| Plastic Bottle | Recyclable Waste |
| Can | Recyclable Waste |
| Paper | Recyclable Waste |
| Plastic Bag | General Waste |
| Instant Noodle | General Waste |
| Face Mask | General Waste |
| Banana | Organic Waste |
| Apple | Organic Waste |
| Orange | Organic Waste |
| Battery | Hazardous Waste |

The system also includes a special `shutdown_card` class used only for safe system shutdown.  
This class is not counted as one of the 10 waste classes.

Waste class-to-category mapping is defined in `configs/class_mapping.yaml`.

---

## Configuration

Femto 1.0 uses YAML configuration files to separate runtime settings from source code.

| File | Purpose |
|---|---|
| `configs/system_config.yaml` | Model path, confidence threshold, camera settings, motion settings, decision buffer, shutdown settings, audio paths, servo pins, servo duty cycles, and runtime delays |
| `configs/class_mapping.yaml` | YOLO waste class names mapped to high-level waste categories, plus special classes such as `shutdown_card` |

This makes the system easier to adjust without modifying the Python source code.

Examples of values controlled by configuration:

```text
Model path
YOLO confidence threshold
Motion detection threshold
Decision buffer size
Shutdown card confidence threshold
Servo pin numbers
Servo duty cycles
Audio file paths
Runtime loop delay
```

---

## Repository Structure

```text
FEMTO_1.0/
├── configs/
│   ├── class_mapping.yaml
│   └── system_config.yaml
│
├── docs/
│   ├── images/
│   │   ├── detection_example.png
│   │   ├── hardware_performance.png
│   │   ├── jtop.png
│   │   ├── prototype_overview.png
│   │   ├── software_performance.png
│   │   ├── system_flowchart.png
│   │   └── yolo_verbose.png
│   ├── deployment.md
│   ├── results.md
│   └── system_architecture.md
│
├── models/
│   └── README.md
│
├── scripts/
│   └── run_system.py
│
├── src/
│   └── femto/
│       ├── __init__.py
│       ├── app.py
│       ├── class_mapper.py
│       ├── config.py
│       └── servo_controller.py
│
├── tools/
│   ├── calibrate_servo_angle.py
│   ├── model_export.py
│   └── model_training.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Main Components

| Path | Purpose |
|---|---|
| `scripts/run_system.py` | Main runtime entry point. Loads YAML configuration files and starts the FEMTO application |
| `src/femto/app.py` | Main runtime application loop for camera capture, motion-triggered inference, shutdown card handling, decision buffering, audio feedback, and servo sorting |
| `src/femto/config.py` | YAML configuration loader and validator |
| `src/femto/class_mapper.py` | Maps YOLO class names to waste categories using `configs/class_mapping.yaml` |
| `src/femto/servo_controller.py` | Servo PWM wrapper and non-blocking servo finite-state controller |
| `configs/class_mapping.yaml` | Waste class-to-category mapping |
| `configs/system_config.yaml` | System paths, thresholds, servo settings, audio settings, camera settings, and runtime settings |
| `tools/calibrate_servo_angle.py` | Utility script for testing and calibrating servo angles before running the full sorting system |
| `tools/model_training.py` | Utility script for training the YOLO waste classification/detection model |
| `tools/model_export.py` | Utility script for exporting the trained YOLO model to TensorRT engine format for Jetson deployment |
| `docs/system_architecture.md` | System architecture details |
| `docs/results.md` | Performance results |
| `docs/deployment.md` | Jetson deployment guide |
| `models/README.md` | Model file instructions |

---

## How to Run

Run the main system from the repository root:

```bash
python scripts/run_system.py
```

Before running the system, check these files:

```text
configs/system_config.yaml
configs/class_mapping.yaml
```

Make sure the following paths and settings are correct for your Jetson environment:

```text
Model path
Audio file paths
Camera settings
Servo pin numbers
Servo duty cycle values
Motion detection threshold
Shutdown card settings
```

---

## Model Workflow

```text
Custom Dataset
    ↓
YOLO Training (.pt)
    ↓
TensorRT Export (.engine)
    ↓
Jetson Orin Nano Deployment
    ↓
Real System Testing
    ↓
Real-Time Waste Sorting
```

Training, export, and calibration scripts are placed under `tools/` because they are development utilities, not the main runtime entry point.

---

## Technologies Used

- Python
- YOLO
- OpenCV
- TensorRT
- NVIDIA Jetson Orin Nano
- CSI Camera
- Jetson.GPIO
- Servo Motor
- PWM Control
- GStreamer
- Pygame
- YAML Configuration

---

## Performance Evidence

The project includes performance images in `docs/images/`:

- `prototype_overview.png` — physical prototype overview
- `system_flowchart.png` — system operation flowchart
- `detection_example.png` — YOLO detection example from the deployed system
- `software_performance.png` — real system software accuracy results across 10 waste classes
- `hardware_performance.png` — real physical sorting time results across 10 waste classes
- `yolo_verbose.png` — TensorRT inference runtime log
- `jtop.png` — Jetson Orin Nano resource monitoring during operation

These images are used to document the physical prototype, system workflow, software-level performance, hardware-level performance, and runtime behavior of the complete deployed prototype.

---

## Project Status

This project is a practical prototype developed to demonstrate the application of Computer Vision and Edge AI in an automated waste sorting system.

The current version focuses on real-time object detection, Edge AI deployment, YAML-based runtime configuration, physical sorting control, user interaction through voice feedback, and safe shutdown operation.

The runtime has been refactored from a single-script structure into a clearer modular structure using `scripts/`, `src/femto/`, `configs/`, and `tools/`.

Future improvements may include larger dataset collection, improved mechanical design, additional sensor integration, better handling of overlapping waste items, more robust performance under different lighting conditions, and further separation of runtime modules such as camera, detector, motion detector, audio player, decision buffer, and shutdown handler.

---

## Notes

This repository is designed for portfolio and educational purposes.  
Model weights, TensorRT engine files, audio files, and dataset files may not be included directly in the repository due to file size, environment-specific deployment requirements, and storage limitations.

Please refer to `models/README.md` and `docs/deployment.md` for model placement and deployment instructions.