# System Architecture

This document explains the system architecture of **Femto 1.0 — Edge AI Waste Classification System**.

Femto 1.0 is designed as an end-to-end Edge AI system that combines computer vision, real-time inference, decision logic, physical actuation, voice feedback, YAML-based runtime configuration, and safe shutdown handling on NVIDIA Jetson Orin Nano.

---

## 1. Overview

The system receives image input from a CSI camera, detects the waste item using a YOLO object detection model, maps the detected class into a waste category, and controls a servo-based sorting mechanism to move the item into the correct bin.

The main goal of this architecture is to demonstrate a practical Edge AI pipeline that does not stop at model prediction, but also connects the prediction result to physical hardware control.

The system includes the following main functions:

- Camera-based image acquisition
- Motion-triggered YOLO inference
- TensorRT-based object detection
- Waste class-to-category mapping
- Consecutive detection buffering
- Servo-based physical sorting
- Voice feedback for user interaction
- Shutdown card detection for safe shutdown
- Resource cleanup for camera, GPIO, servo, PWM, and audio components
- YAML-based configuration for runtime settings

---

## 2. High-Level System Pipeline

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

![System Flowchart](images/system_flowchart.png)

The pipeline is designed to run locally on the edge device. The Jetson Orin Nano performs camera input processing, AI inference, decision logic, audio feedback, and hardware control without requiring cloud inference.

---

## 3. Hardware Architecture

![Prototype Overview](images/prototype_overview.png)

The hardware system consists of the following main components:

| Component | Purpose |
|---|---|
| NVIDIA Jetson Orin Nano | Main edge computing device for inference and control |
| CSI Camera | Captures waste item images for detection |
| Rotation Servo Motor | Rotates the sorting mechanism toward the target bin |
| Tilt Servo Motor | Tilts the mechanism to release the waste item |
| Speaker / Audio Output | Provides voice feedback and system alerts |
| Sorting Mechanism | Moves the detected waste item into the selected bin |
| Waste Bins | Receive waste items based on category |

The Jetson Orin Nano acts as the central controller. It receives image data from the CSI camera, performs YOLO inference using a TensorRT engine model, decides the target waste category, and controls the servo motors using PWM signals.

---

## 4. Software Architecture

The runtime software is organized into a simple modular structure.

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

The main runtime entry point is:

```text
scripts/run_system.py
```

The main application logic is implemented in:

```text
src/femto/app.py
```

Configuration loading and runtime settings are handled through:

```text
src/femto/config.py
configs/system_config.yaml
configs/class_mapping.yaml
```

The software architecture is currently separated into the following main files:

| File | Function |
|---|---|
| `scripts/run_system.py` | Main runtime entry point. Loads YAML configuration files and starts the application |
| `src/femto/app.py` | Main runtime application loop for camera capture, motion-triggered inference, shutdown card handling, decision buffering, audio feedback, and servo sorting |
| `src/femto/config.py` | Loads and validates YAML configuration files |
| `src/femto/class_mapper.py` | Maps YOLO class names to high-level waste categories |
| `src/femto/motion_detector.py` | Contains hardware-free frame-difference motion detection logic |
| `src/femto/decision_buffer.py` | Contains hardware-free waste decision buffering and single-object decision logic |
| `src/femto/shutdown_detection.py` | Contains hardware-free shutdown-card confirmation buffering |
| `src/femto/servo_controller.py` | Controls the two-servo sorting mechanism using a non-blocking finite-state machine |
| `configs/system_config.yaml` | Stores runtime settings such as model path, thresholds, camera settings, audio paths, servo pins, duty cycles, and timing values |
| `configs/class_mapping.yaml` | Stores YOLO class-to-category mapping and special classes such as `shutdown_card` |

This structure separates the runtime entry point, configuration handling, class mapping, pure motion detection, pure decision buffering, pure shutdown-card confirmation, and servo control from the main application loop. It makes the project easier to maintain compared with a single-script runtime structure.

---

## 5. Runtime Entry Point

The runtime starts from:

```text
scripts/run_system.py
```

This file has a small responsibility:

```text
1. Locate the project root
2. Add src/ to the Python import path
3. Load configs/system_config.yaml
4. Load configs/class_mapping.yaml
5. Create FemtoApp
6. Start the application runtime
```

The entry point does not contain the main camera loop, YOLO logic, servo logic, or shutdown logic. Those responsibilities are handled inside the runtime modules under `src/femto/`.

This design keeps the startup script simple and makes the main application behavior easier to locate.

---

## 6. Configuration Architecture

Femto 1.0 uses YAML configuration files to separate runtime parameters from source code.

The main configuration files are:

```text
configs/system_config.yaml
configs/class_mapping.yaml
```

### system_config.yaml

`configs/system_config.yaml` stores system-level runtime settings.

It controls values such as:

```text
Model path
YOLO task type
YOLO confidence threshold
Camera sensor ID
Camera resolution
Motion detection threshold
YOLO wake duration
Decision buffer size
Sorting cooldown delay
Shutdown card confidence threshold
Shutdown buffer size
Audio file paths
Servo pin numbers
Servo PWM frequency
Servo home position
Servo category positions
Servo movement timing
Runtime loop delay
```

This allows the system behavior to be adjusted without modifying Python source code.

### class_mapping.yaml

`configs/class_mapping.yaml` stores the mapping between YOLO class names and high-level waste categories.

Example:

```text
plastic_bottle → Recycle Waste
can            → Recycle Waste
battery        → Hazardous Waste
shutdown_card  → shutdown special class
```

This file separates model class names from sorting category logic. If a new class is added later, the mapping can be updated in the YAML file instead of editing the runtime code.

---

## 7. Camera and Motion Detection

The system uses a CSI camera as the input source. The camera is opened through a GStreamer pipeline to support Jetson camera input and hardware-accelerated video handling.

Motion detection is used before running YOLO inference. Instead of running the object detection model continuously, the system first checks whether there is enough movement in the camera frame.

The motion detection process follows this logic:

```text
Current Frame
    ↓
Convert to Grayscale
    ↓
Apply Gaussian Blur
    ↓
Compare with Previous Frame
    ↓
Threshold Frame Difference
    ↓
Count Changed Pixels
    ↓
Wake YOLO if Motion Exceeds Threshold
```

This design reduces unnecessary YOLO inference when no waste item is present in front of the camera. It also helps make the runtime loop more efficient on edge hardware.

The motion threshold, frame difference threshold, blur kernel size, and YOLO wake duration are configured in:

```text
configs/system_config.yaml
```

---

## 8. YOLO TensorRT Inference

During development and training, the YOLO model is used in `.pt` format. For deployment on NVIDIA Jetson Orin Nano, the trained model is converted into TensorRT `.engine` format.

The TensorRT engine is used as the deployment model format for inference on the Jetson device.

```text
YOLO .pt Model
    ↓
TensorRT Export
    ↓
YOLO .engine Model
    ↓
Jetson Orin Nano Runtime Inference
```

![Detection Example](images/detection_example.png)

At runtime, each active frame is passed to the YOLO model. The model returns detected objects, class names, and confidence scores. The system then uses these results for shutdown detection, waste category mapping, and sorting decisions.

The model path and confidence threshold are configured in:

```text
configs/system_config.yaml
```

---

## 9. Waste Class Mapping

The YOLO model detects 10 waste classes. These classes are mapped into 4 main waste categories for sorting.

| Waste Category | Classes |
|---|---|
| Recycle Waste | `plastic_bottle`, `can`, `paper` |
| General Waste | `plastic_bag`, `instant_noodle`, `mask` |
| Organic Waste | `banana`, `apple`, `orange` |
| Hazardous Waste | `battery` |

The class mapping is defined in:

```text
configs/class_mapping.yaml
```

The mapping is loaded by:

```text
src/femto/class_mapper.py
```

The system also includes a special class:

```text
shutdown_card
```

The `shutdown_card` class is used only for safe system shutdown and is not counted as one of the 10 waste classes.

---

## 10. Decision Buffering Logic

The system does not immediately trigger sorting from a single-frame prediction. Instead, it uses a consecutive detection buffer to confirm that the detected class is stable.

This helps reduce unstable predictions, false triggers, and accidental servo activation.

The decision logic follows this process:

```text
YOLO Detection Result
    ↓
Check Number of Detected Objects
    ↓
Accept Only Single-Object Detection
    ↓
Compare Current Class with Previous Class
    ↓
Increase Consecutive Count if Class Matches
    ↓
Trigger Sorting When Count Reaches Buffer Size
```

If multiple objects are detected in the same frame, the system resets the current decision buffer. This prevents the mechanism from sorting when the scene is ambiguous.

After a sorting action is triggered, the system enters a short cooldown period before accepting the next sorting decision.

The decision buffer size and cooldown delay are configured in:

```text
configs/system_config.yaml
```

---

## 11. Servo-Based Sorting Mechanism

The physical sorting mechanism uses two servo motors controlled through PWM signals.

| Pin | Servo Role | Description |
|---|---|---|
| 32 | Rotation servo | Rotates the mechanism toward the target bin |
| 33 | Tilt servo | Tilts the mechanism to release the waste item |

The rotation servo on pin 32 is responsible for selecting the target bin direction. The tilt servo on pin 33 is responsible for releasing the waste item after the mechanism has rotated into position.

Servo pin numbers, PWM frequency, home position, category positions, and timing values are configured in:

```text
configs/system_config.yaml
```

The servo control implementation is handled by:

```text
src/femto/servo_controller.py
```

---

## 12. Servo PWM Design

The rotation servo on pin 32 releases its PWM signal after movement. This design was used because holding the PWM signal continuously caused mechanical vibration and servo jitter during testing.

The tilt servo on pin 33 keeps its PWM signal active to maintain the mechanism position.

This design acts as a simple jitter mitigation strategy for the rotation mechanism.

---

## 13. Servo Movement Sequence

The servo movement is handled as an asynchronous finite-state sequence rather than a single blocking action.

The movement cycle is:

```text
1. Rotate toward the target bin using pin 32
2. Tilt the mechanism using pin 33
3. Return the tilt servo to the default position
4. Return the rotation servo to the default position
5. Release PWM on the rotation servo to reduce jitter
```

This sequence allows the main runtime loop to continue updating the system while the servo movement is in progress.

The servo duty cycles are mapped by waste category. Example categories include:

```text
Recycle Waste
General Waste
Organic Waste
Hazardous Waste
```

The active runtime category string is `Recycle Waste`. This string must match `configs/class_mapping.yaml`, `audio.category_sounds`, and `servo.category_positions`.

The servo timing and duty-cycle mapping are configured in:

```text
configs/system_config.yaml
```

---

## 14. Voice Feedback System

The system includes audio feedback to communicate with the user during operation.

Voice feedback is used for:

- Startup notification
- Waste category result
- Shutdown alert

Each waste category has a corresponding audio message:

| Waste Category | Audio Feedback |
|---|---|
| Recycle Waste | Recycle Waste notification |
| General Waste | General waste notification |
| Organic Waste | Organic waste notification |
| Hazardous Waste | Hazardous waste notification |

The audio system improves user interaction by making the system response easier to understand during real-time operation.

Audio file paths are configured in:

```text
configs/system_config.yaml
```

---

## 15. Shutdown Card Detection

The system includes a shutdown card detection function for safe shutdown operation.

Instead of directly cutting power to the Jetson device, the system detects a special `shutdown_card` class using the YOLO model. When the shutdown card is detected continuously for a configured number of frames, the system plays a shutdown alert and then performs a system-level poweroff command.

The shutdown logic follows this process:

```text
Detect Shutdown Card
    ↓
Check Confidence Threshold
    ↓
Confirm Consecutive Detection
    ↓
Play Shutdown Alert
    ↓
Release Hardware Resources
    ↓
Execute System Poweroff
```

This approach helps reduce the risk of file corruption or hardware issues caused by directly disconnecting power.

The shutdown card confidence threshold, buffer size, delay, and shutdown sound path are configured in:

```text
configs/system_config.yaml
```

---

## 16. Resource Cleanup and Safety

The system includes cleanup logic to safely release hardware and software resources when the program exits.

The cleanup process includes:

- Releasing the camera
- Returning servos to their default positions
- Stopping PWM signals
- Cleaning up GPIO resources
- Stopping the audio mixer
- Handling keyboard interrupt and termination signals

This is important for embedded hardware systems because unreleased GPIO or PWM resources may cause unstable behavior in the next runtime session.

---

## 17. Current Module Boundaries

The current refactor separates the runtime into a small number of clear modules.

| Module | Responsibility |
|---|---|
| `scripts/run_system.py` | Runtime entry point |
| `src/femto/config.py` | YAML loading and validation |
| `src/femto/class_mapper.py` | Waste class-to-category mapping |
| `src/femto/motion_detector.py` | Hardware-free frame-difference motion detection |
| `src/femto/decision_buffer.py` | Hardware-free waste decision buffering |
| `src/femto/shutdown_detection.py` | Hardware-free shutdown-card confirmation |
| `src/femto/servo_controller.py` | Servo PWM wrapper and non-blocking servo FSM |
| `src/femto/app.py` | Main runtime loop and integration logic |

Some runtime responsibilities are still integrated inside `src/femto/app.py`. The app still owns camera initialization, YOLO model initialization and invocation, audio initialization and playback, servo orchestration, GPIO cleanup, signal handling, and OS shutdown execution. Pure motion detection, waste decision buffering, and shutdown-card confirmation now live in hardware-free modules.

This is intentional for the current stage of the project. The system has already been improved from a single-script runtime structure while avoiding an overly large refactor in one step.

Future module separation may include:

```text
camera.py
detector.py
audio_player.py
shutdown_handler.py
resource_manager.py
```

In this list, `shutdown_handler.py` refers to a possible future side-effect boundary for OS shutdown execution. The pure shutdown-card confirmation buffer already exists in `src/femto/shutdown_detection.py`.

---

## 18. Design Considerations

Several design decisions were made to improve system stability and make the system more suitable for edge deployment.

| Design Decision | Reason |
|---|---|
| TensorRT `.engine` deployment | Provides an optimized deployment format for NVIDIA Jetson hardware |
| Motion-triggered inference | Reduces unnecessary YOLO processing when no object is present |
| Consecutive detection buffering | Reduces unstable predictions and false sorting actions |
| Single-object decision rule | Avoids sorting when the scene contains multiple detected objects |
| YAML-based configuration | Allows runtime settings to be changed without editing source code |
| Non-blocking servo FSM | Allows the main runtime loop to continue while servo movement is in progress |
| PWM release on rotation servo | Reduces mechanical jitter from the rotation mechanism |
| Shutdown card detection | Allows safe shutdown without directly cutting power |
| Resource cleanup | Prevents camera, GPIO, PWM, and audio resource issues |

These decisions make the system more practical for real-world edge AI operation, where both AI prediction quality and hardware behavior must be considered together.
