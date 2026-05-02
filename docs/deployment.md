# Deployment Guide

This document explains the deployment setup for **Femto 1.0 — Edge AI Waste Classification System** on NVIDIA Jetson Orin Nano.

This guide is written as a deployment reference for the current project structure. Some paths are placeholder paths and must be replaced with the actual paths used on the Jetson device.

---

## 1. Target Device

The system is designed to run on:

| Item | Description |
|---|---|
| Device | NVIDIA Jetson Orin Nano |
| JetPack | JetPack 6.x |
| Model format | TensorRT `.engine` |
| Camera input | CSI Camera |
| Actuator control | Servo motors using PWM |
| Runtime entry point | `scripts/run_system.py` |
| Main runtime module | `src/femto/app.py` |
| Configuration files | `configs/system_config.yaml`, `configs/class_mapping.yaml` |

The Jetson Orin Nano is used as the main edge device for camera input, TensorRT inference, decision logic, servo control, audio feedback, and safe shutdown handling.

---

## 2. Repository Structure

The expected project structure is:

```text
FEMTO_1.0/
|-- configs/
|   |-- class_mapping.yaml
|   |-- system_config.example.yaml
|   `-- system_config.yaml
|-- docs/
|   |-- images/
|   |-- configuration.md
|   |-- deployment.md
|   |-- development.md
|   |-- project_structure.md
|   |-- results.md
|   |-- standardization_plan.md
|   `-- system_architecture.md
|-- models/
|   `-- README.md
|-- scripts/
|   `-- run_system.py
|-- src/
|   `-- femto/
|       |-- __init__.py
|       |-- app.py
|       |-- class_mapper.py
|       |-- config.py
|       |-- decision_buffer.py
|       |-- motion_detector.py
|       |-- servo_controller.py
|       `-- shutdown_detection.py
|-- tests/
|   |-- conftest.py
|   |-- test_class_mapper.py
|   |-- test_config_validation.py
|   |-- test_decision_buffer.py
|   |-- test_motion_detector.py
|   |-- test_preflight_check.py
|   `-- test_shutdown_detection.py
|-- tools/
|   |-- calibrate_servo_angle.py
|   |-- model_export.py
|   |-- model_training.py
|   `-- preflight_check.py
|-- .gitattributes
|-- .gitignore
|-- pyproject.toml
|-- README.md
|-- requirements-dev.txt
`-- requirements.txt
```

The repository does not include actual model files, TensorRT engine files, dataset files, or audio files.

Model and audio paths shown in the configuration file are placeholder paths and should be replaced with the actual paths used on the Jetson device.

`configs/system_config.yaml` is the active runtime configuration loaded by `scripts/run_system.py`. `configs/system_config.example.yaml` is a reference template for the same schema and is not loaded automatically.

Repository files such as configuration files are referenced from the project root:

```text
configs/system_config.yaml
configs/class_mapping.yaml
```

---

## 3. Runtime Structure

The current runtime uses a cleaner modular structure.

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

Main runtime responsibilities are separated as follows:

| File | Purpose |
|---|---|
| `scripts/run_system.py` | Main runtime entry point. Loads YAML configuration files and starts the FEMTO application |
| `src/femto/app.py` | Main runtime application loop for camera capture, motion-triggered inference, shutdown card handling, decision buffering, audio feedback, and servo sorting |
| `src/femto/config.py` | YAML configuration loader and validator |
| `src/femto/class_mapper.py` | Maps YOLO class names to waste categories using `configs/class_mapping.yaml` |
| `src/femto/motion_detector.py` | Hardware-free frame-difference motion detection logic |
| `src/femto/decision_buffer.py` | Hardware-free waste decision buffering and single-object decision logic |
| `src/femto/shutdown_detection.py` | Hardware-free shutdown-card confirmation buffer |
| `src/femto/servo_controller.py` | Servo PWM wrapper and non-blocking servo finite-state controller |
| `tools/calibrate_servo_angle.py` | Utility script for testing and calibrating servo angles before running the full sorting system |
| `tools/model_training.py` | Example training script with placeholder paths that must be edited or converted to CLI arguments before use |
| `tools/model_export.py` | Example TensorRT export script with placeholder paths that must be edited or converted to CLI arguments before use |
| `tools/preflight_check.py` | Hardware-free configuration and asset-path preflight checker |

---

## 4. Model Deployment

During development and training, the YOLO model is used in `.pt` format.

For deployment on NVIDIA Jetson Orin Nano, the trained model is converted into TensorRT `.engine` format to improve inference performance on edge hardware.

The model path in this repository is written as a placeholder:

```text
path/to/best.engine
```

This path must be replaced with the actual TensorRT engine path used on the Jetson device.

The model path can be changed in:

```text
configs/system_config.yaml
```

Example configuration:

```yaml
model:
  path: "path/to/best.engine"
  task: "detect"
  confidence_threshold: 0.50
```

For real deployment, use a path that exists on the Jetson device, for example:

```yaml
model:
  path: "/home/jetson/FEMTO_1.0/models/best.engine"
  task: "detect"
  confidence_threshold: 0.50
```

---

## 5. TensorRT Export

The repository includes an example TensorRT export script at:

```text
tools/model_export.py
```

The current script contains a placeholder checkpoint path and must be edited for the local `.pt` file or converted to CLI arguments before use.

The export process follows this workflow:

```text
YOLO .pt model
    ↓
TensorRT export
    ↓
YOLO .engine model
    ↓
Jetson Orin Nano deployment
```

Example export logic:

```python
from ultralytics import YOLO

model = YOLO("path/to/best.pt", task="detect")

model.export(
    format="engine",
    half=True,
    device=0,
    batch=1,
)
```

Export settings used in this project:

| Setting | Value | Purpose |
|---|---:|---|
| `format` | `engine` | Export to TensorRT engine |
| `half` | `True` | Use FP16 inference |
| `device` | `0` | Use GPU device 0 |
| `batch` | `1` | Optimize for single-frame inference |

After export, update `configs/system_config.yaml` with the actual `.engine` file path used on the Jetson device.

When possible, export or rebuild the TensorRT engine on the target Jetson device to reduce compatibility problems between TensorRT, CUDA, JetPack, and hardware environment.

---

## 6. Python Environment

The runtime environment depends on the JetPack version installed on the Jetson device.

For JetPack 6.x, install Jetson-compatible versions of the main AI and hardware packages according to the JetPack environment.

Important packages include:

- Python
- Ultralytics
- OpenCV
- TensorRT
- PyTorch
- TorchVision
- Jetson.GPIO
- Pygame
- PyYAML

Do not blindly install desktop versions of GPU-related packages on Jetson. PyTorch, TorchVision, TensorRT, and NVIDIA-related packages should match the JetPack version and CUDA environment.

General Python packages can be listed in:

```text
requirements.txt
```

Install only the packages that are compatible with the Jetson environment.

---

## 7. Configuration Files

The project uses configuration files to separate system settings from source code.

### System Configuration

Main system settings are stored in:

```text
configs/system_config.yaml
```

This file includes settings for:

- Model path
- Model task type
- YOLO confidence threshold
- Camera configuration
- Motion detection threshold
- YOLO wake duration
- Decision buffer size
- Sorting cooldown delay
- Shutdown card detection
- Servo pin mapping
- Servo duty-cycle mapping
- Servo movement timing
- Audio file paths
- Runtime loop timing

The model and audio paths in `system_config.yaml` are placeholder paths. Replace them with the actual paths used on the Jetson device.

Example model path:

```yaml
model:
  path: "path/to/best.engine"
```

Example audio paths:

```yaml
audio:
  startup_alert: "path/to/start_alert.mp3"
  category_sounds:
    Recycle Waste: "path/to/recycle.mp3"
    General Waste: "path/to/general.mp3"
    Organic Waste: "path/to/organic.mp3"
    Hazardous Waste: "path/to/hazardous.mp3"
```

Example shutdown sound path:

```yaml
shutdown:
  sound_path: "path/to/shutdown_alert.mp3"
```

### Class Mapping

Waste class-to-category mapping is stored in:

```text
configs/class_mapping.yaml
```

The model detects 10 waste classes and maps them into 4 waste categories:

| Category | Classes |
|---|---|
| Recycle Waste | `plastic_bottle`, `can`, `paper` |
| General Waste | `plastic_bag`, `instant_noodle`, `mask` |
| Organic Waste | `banana`, `apple`, `orange` |
| Hazardous Waste | `battery` |

The system also uses `shutdown_card` as a special class for safe shutdown. This class is not counted as one of the 10 waste classes.

Example mapping:

```yaml
waste_classes:
  plastic_bottle: "Recycle Waste"
  can: "Recycle Waste"
  paper: "Recycle Waste"

  plastic_bag: "General Waste"
  instant_noodle: "General Waste"
  mask: "General Waste"

  banana: "Organic Waste"
  apple: "Organic Waste"
  orange: "Organic Waste"

  battery: "Hazardous Waste"

special_classes:
  shutdown_card: "shutdown"
```

---

## 8. Camera Setup

The system uses a CSI camera connected to the Jetson Orin Nano.

The runtime application opens the camera using a GStreamer pipeline. This allows the system to use Jetson camera input through NVIDIA camera support.

The camera pipeline is configured for:

- CSI camera input
- 1280×720 frame capture
- BGR frame output for OpenCV
- Low buffer latency using dropped frames
- Jetson camera acceleration through GStreamer

Camera-related values are configured in:

```text
configs/system_config.yaml
```

Example:

```yaml
camera:
  sensor_id: 0
  width: 1280
  height: 720
  flip_method: 0
```

Before running the full system, confirm that the CSI camera works correctly on the Jetson device.

The main runtime application expects the camera to open successfully. If the camera cannot be opened, the application will stop.

---

## 9. Servo and GPIO Setup

The physical sorting mechanism uses two servo motors controlled through PWM.

| Pin | Servo Role | Behavior |
|---|---|---|
| 32 | Rotation servo | Rotates the mechanism toward the target bin and releases PWM after movement |
| 33 | Tilt servo | Tilts the mechanism to release the waste item and keeps PWM active to maintain position |

The rotation servo on pin 32 releases its PWM signal after movement to reduce mechanical jitter. This design was used because holding PWM continuously caused vibration in the rotation mechanism.

The tilt servo on pin 33 keeps PWM active to maintain the mechanism position.

Servo-related values are configured in:

```text
configs/system_config.yaml
```

Example:

```yaml
servo:
  rotate_pin: 32
  tilt_pin: 33
  pwm_frequency: 50

  start_position:
    rotate_duty: 7.5
    tilt_duty: 4.12

  category_positions:
    Recycle Waste:
      rotate_duty: 5.0
      tilt_duty: 7.5
    General Waste:
      rotate_duty: 10.5
      tilt_duty: 1.78
    Organic Waste:
      rotate_duty: 10.3
      tilt_duty: 7.5
    Hazardous Waste:
      rotate_duty: 5.0
      tilt_duty: 1.78
```

Servo calibration can be tested using:

```text
tools/calibrate_servo_angle.py
```

The calibration script allows manual testing of PWM duty cycles for both servo motors.

Example command format inside the calibration tool:

```text
32 5.0
33 7.5
32 0
```

Where:

| Command | Meaning |
|---|---|
| `32 5.0` | Set rotation servo duty cycle to 5.0 |
| `33 7.5` | Set tilt servo duty cycle to 7.5 |
| `32 0` | Release PWM on rotation servo |

---

## 10. Audio Setup

The system uses audio feedback for user interaction.

Audio feedback is used for:

- Startup alert
- Waste category announcement
- Shutdown alert

Audio files are not included in this repository. The audio paths in `configs/system_config.yaml` are placeholder paths and must be replaced with the actual audio file paths used on the Jetson device.

Example audio configuration:

```yaml
audio:
  startup_alert: "path/to/start_alert.mp3"
  category_sounds:
    Recycle Waste: "path/to/recycle.mp3"
    General Waste: "path/to/general.mp3"
    Organic Waste: "path/to/organic.mp3"
    Hazardous Waste: "path/to/hazardous.mp3"

shutdown:
  sound_path: "path/to/shutdown_alert.mp3"
```

---

## 11. Running the System

Before starting the hardware runtime, run the hardware-free preflight checker from the repository root:

```bash
python tools/preflight_check.py
```

The preflight checker reads `configs/system_config.yaml` and `configs/class_mapping.yaml`, detects placeholder or missing model/audio paths, and verifies category consistency across class mapping, servo positions, and audio entries. It does not import `Jetson.GPIO`, open the camera, load the YOLO model, play audio, move servos, execute shutdown, or modify files.

Phase 2A pure logic has been extracted into hardware-free modules for motion detection, waste decision buffering, and shutdown-card confirmation. Automated tests cover hardware-free software logic. Jetson-specific behavior such as TensorRT runtime, CSI camera, GPIO, servo movement, audio playback, and poweroff behavior must still be validated manually on the target device. No completed hardware validation results are currently documented in this repository.

The main runtime entry point is:

```text
scripts/run_system.py
```

The runtime pipeline performs:

```text
Camera input
    ↓
Motion detection
    ↓
YOLO TensorRT inference
    ↓
Waste class prediction
    ↓
Class-to-category mapping
    ↓
Decision buffering
    ↓
Servo control
    ↓
Voice feedback
    ↓
Safe shutdown handling
```

A typical manual run command from the repository root is:

```bash
python scripts/run_system.py
```

Depending on the Jetson environment, the command may need to be adjusted for the correct Python environment or full script path.

Before running, confirm that:

- `configs/system_config.yaml` has the correct model path
- `configs/system_config.yaml` has the correct audio paths
- `configs/system_config.yaml` has the correct servo pin and duty-cycle values
- `configs/class_mapping.yaml` matches the class names in the trained YOLO model
- The CSI camera opens correctly
- The TensorRT engine loads correctly
- The servo power supply is stable
- GPIO permissions are available

---

## 12. Startup Applications Setup

For automatic startup, the runtime script can be added to Ubuntu Startup Applications.

A typical startup command may follow this idea:

```bash
python /path/to/FEMTO_1.0/scripts/run_system.py
```

Or, when using a virtual environment:

```bash
/path/to/venv/bin/python /path/to/FEMTO_1.0/scripts/run_system.py
```

Use the actual project path and Python environment path on the Jetson device.

Before adding the script to Startup Applications, test the runtime manually first to confirm that:

- The model path is correct
- The CSI camera opens successfully
- Servo pins work correctly
- Servo duty cycles are calibrated
- Audio files can be loaded
- The TensorRT engine runs properly
- GPIO permissions are available
- The shutdown card behavior works as expected
- Hardware cleanup works correctly when stopping the program

Using absolute paths is recommended for startup commands, especially for model files, audio files, and Python environments.

---

## 13. Shutdown Card Operation

The system includes a safe shutdown function using a special `shutdown_card` class.

Instead of directly cutting power to the Jetson device, the system detects the shutdown card through YOLO inference.

The shutdown process is:

```text
Detect shutdown_card
    ↓
Confirm confidence threshold
    ↓
Confirm consecutive detection buffer
    ↓
Play shutdown alert
    ↓
Clean up camera, GPIO, PWM, and audio resources
    ↓
Execute system poweroff
```

This helps reduce the risk of data corruption or unstable hardware behavior caused by directly disconnecting power.

Shutdown card settings are configured in:

```text
configs/system_config.yaml
```

Example:

```yaml
shutdown:
  class_name: "shutdown_card"
  confidence_threshold: 0.70
  buffer_size: 40
  delay_seconds: 10.0
  sound_path: "path/to/shutdown_alert.mp3"
```

---

## 14. Common Deployment Issues

### CSI camera cannot be opened

Possible causes:

- CSI camera is not connected correctly
- Camera ribbon cable is loose
- GStreamer pipeline does not match the camera setup
- Camera is already being used by another process
- Camera settings in `configs/system_config.yaml` do not match the actual camera setup

Check the camera connection and test the camera separately before running the full system.

### TensorRT engine fails to load

Possible causes:

- `.engine` file path is incorrect
- TensorRT engine was built for a different device or environment
- JetPack, TensorRT, CUDA, or Ultralytics versions are not compatible
- The model file is missing from the actual deployment path
- `configs/system_config.yaml` still contains a placeholder model path

Re-export the model on the target Jetson device when possible.

### Servo does not move

Possible causes:

- Incorrect pin connection
- PWM pin is not configured correctly
- Servo power supply is insufficient
- Ground is not shared between Jetson and servo power source
- Duty-cycle value is outside the usable range
- Servo pin or duty-cycle values in `configs/system_config.yaml` are incorrect

Use `tools/calibrate_servo_angle.py` to test servo movement manually.

### Rotation servo jitters

The rotation servo on pin 32 is intentionally designed to release PWM after movement. This reduces mechanical jitter caused by holding the servo signal continuously.

If jitter still occurs, re-check:

- Servo power stability
- Mechanical load
- Ground connection
- Duty-cycle values
- Whether PWM release is enabled in `configs/system_config.yaml`

### Audio does not play

Possible causes:

- Audio file path is incorrect
- Audio output device is not configured
- Pygame mixer cannot initialize
- Audio files are missing from the actual deployment path
- `configs/system_config.yaml` still contains placeholder audio paths

Check audio output and update the paths in `configs/system_config.yaml`.

### System does not start automatically

Possible causes:

- Startup Applications command uses the wrong path
- Python environment is not activated
- Model or audio paths are still placeholder paths
- Required permissions are missing
- Camera is not ready at boot time
- Relative paths fail when launched from Startup Applications

Use absolute paths in the Startup Applications command if needed.

### Import error: femto module not found

Possible causes:

- The script is not being run from the expected project structure
- The `src/` directory is missing
- `src/femto/__init__.py` is missing
- The startup command points to the wrong project path

Run the system from the repository root:

```bash
python scripts/run_system.py
```

If using Startup Applications, use the full absolute path to `scripts/run_system.py`.

---

## 15. Deployment Checklist

Before running the full system, confirm the following:

```text
[ ] TensorRT .engine model exists on the Jetson device
[ ] configs/system_config.yaml points to the correct model path
[ ] configs/system_config.yaml points to the correct audio paths
[ ] configs/class_mapping.yaml matches the trained YOLO class names
[ ] CSI camera opens correctly
[ ] Servo duty cycles are calibrated
[ ] Servo power supply is stable
[ ] Jetson and servo power supply share ground
[ ] Pygame audio output works
[ ] GPIO permissions are available
[ ] Shutdown card behavior is tested
[ ] Ctrl+C cleanup returns hardware to a safe state
[ ] Startup Applications command uses the correct absolute path
```

---

## 16. Deployment Notes

This repository uses placeholder paths to make the project structure easier to understand without including actual model or audio files.

For real deployment, update the configuration files to match the actual Jetson environment.

Important deployment notes:

- Use JetPack-compatible AI packages
- Use a TensorRT `.engine` model for deployment
- Replace all placeholder paths with actual deployment paths
- Test the CSI camera before running the full system
- Test servo duty cycles before full operation
- Use stable power for the Jetson and servo motors
- Share ground between Jetson and external servo power supply
- Avoid directly cutting power during operation
- Use the shutdown card or proper OS shutdown when possible
- Confirm all paths before adding the script to Startup Applications
- Prefer absolute paths when running automatically at boot

---

## 17. Conclusion

Femto 1.0 is deployed as an Edge AI system on NVIDIA Jetson Orin Nano using a TensorRT YOLO model, CSI camera input, PWM-based servo control, audio feedback, YAML-based runtime configuration, and safe shutdown handling.

The deployment setup is designed for a practical embedded AI prototype where computer vision inference is connected directly to a physical sorting mechanism.
