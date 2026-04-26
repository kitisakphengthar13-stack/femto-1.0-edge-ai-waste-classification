# Deployment Guide

This document explains the deployment setup for **Femto 1.0 — Edge AI Waste Classification System** on NVIDIA Jetson Orin Nano.

This guide is written as a deployment reference for the project structure. Some paths are placeholder paths and must be replaced with the actual paths used on the Jetson device.

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
| Runtime script | `scripts/main.py` |

The Jetson Orin Nano is used as the main edge device for camera input, TensorRT inference, decision logic, servo control, audio feedback, and safe shutdown handling.

---

## 2. Repository Structure

The expected project structure is:

```text
FEMTO_1.0/
├── configs/
│   ├── class_mapping.yaml
│   └── system_config.yaml
│
├── docs/
│   ├── images/
│   ├── deployment.md
│   ├── results.md
│   └── system_architecture.md
│
├── models/
│   └── README.md
│
├── scripts/
│   ├── calibrate_servo_angle.py
│   ├── main.py
│   ├── model_export.py
│   └── model_training.py
│
├── README.md
└── requirements.txt
```

The repository does not include actual model files or audio files.  
Model and audio paths shown in the configuration file are placeholder paths and should be replaced with the actual paths used on the Jetson device.

Repository files such as configuration files are referenced from the project root:

```text
configs/system_config.yaml
configs/class_mapping.yaml
```

---

## 3. Model Deployment

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
  format: "TensorRT engine"
  input_size: 640
  confidence_threshold: 0.50
```

---

## 4. TensorRT Export

The TensorRT engine can be exported from the trained `.pt` model using:

```text
scripts/model_export.py
```

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

---

## 5. Python Environment

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

Do not blindly install desktop versions of GPU-related packages on Jetson. PyTorch, TorchVision, TensorRT, and some NVIDIA-related packages should match the JetPack version and CUDA environment.

General Python packages can be listed in:

```text
requirements.txt
```

Install only the packages that are compatible with the Jetson environment.

---

## 6. Configuration Files

The project uses configuration files to separate system settings from source code.

### System Configuration

Main system settings are stored in:

```text
configs/system_config.yaml
```

This file includes settings for:

- Model path
- Camera configuration
- Motion detection threshold
- Decision buffer size
- Shutdown card detection
- Servo pin mapping
- Servo duty-cycle mapping
- Audio file paths
- Runtime timing values
- Logging settings
- Performance summary

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
  shutdown_alert: "path/to/shutdown_alert.mp3"
```

### Class Mapping

Waste class-to-category mapping is stored in:

```text
configs/class_mapping.yaml
```

The model detects 10 waste classes and maps them into 4 waste categories:

| Category | Classes |
|---|---|
| Recyclable Waste | `plastic_bottle`, `can`, `paper` |
| General Waste | `plastic_bag`, `instant_noodle`, `mask` |
| Organic Waste | `banana`, `apple`, `orange` |
| Hazardous Waste | `battery` |

The system also uses `shutdown_card` as a special class for safe shutdown. This class is not counted as one of the 10 waste classes.

---

## 7. Camera Setup

The system uses a CSI camera connected to the Jetson Orin Nano.

The runtime application opens the camera using a GStreamer pipeline. This allows the system to use Jetson camera input through NVIDIA camera support.

The camera pipeline is configured for:

- CSI camera input
- 1280×720 frame capture
- BGR frame output for OpenCV
- Low buffer latency using dropped frames
- Jetson camera acceleration through GStreamer

Before running the full system, confirm that the CSI camera works correctly on the Jetson device.

The main runtime script expects the camera to open successfully. If the camera cannot be opened, the application will stop.

---

## 8. Servo and GPIO Setup

The physical sorting mechanism uses two servo motors controlled through PWM.

| Pin | Servo Role | Behavior |
|---|---|---|
| 32 | Rotation servo | Rotates the mechanism toward the target bin and releases PWM after movement |
| 33 | Tilt servo | Tilts the mechanism to release the waste item and keeps PWM active to maintain position |

The rotation servo on pin 32 releases its PWM signal after movement to reduce mechanical jitter. This design was used because holding PWM continuously caused vibration in the rotation mechanism.

The tilt servo on pin 33 keeps PWM active to maintain the mechanism position.

Servo calibration can be tested using:

```text
scripts/calibrate_servo_angle.py
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

## 9. Audio Setup

The system uses audio feedback for user interaction.

Audio feedback is used for:

- Startup alert
- Waste category announcement
- Shutdown alert

Audio files are not included in this repository. The audio paths in `configs/system_config.yaml` are placeholder paths and must be replaced with the actual audio file paths used on the Jetson device.

Example audio configuration:

```yaml
audio:
  enabled: true
  mixer_channel: 0

  startup_alert: "path/to/start_alert.mp3"
  shutdown_alert: "path/to/shutdown_alert.mp3"

  sounds:
    "Recycle Waste": "path/to/recycle.mp3"
    "General Waste": "path/to/general.mp3"
    "Organic Waste": "path/to/organic.mp3"
    "Hazardous Waste": "path/to/hazardous.mp3"
```

---

## 10. Running the System

The main runtime application is:

```text
scripts/main.py
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

In the actual prototype, the main runtime script was added to Ubuntu Startup Applications so the system can start automatically after the Jetson device boots.

A typical manual run command may look like:

```bash
python scripts/main.py
```

Depending on the Jetson environment, the command may need to be adjusted for the correct Python environment or full script path.

---

## 11. Startup Applications Setup

For automatic startup, the runtime script can be added to Ubuntu Startup Applications.

A typical startup command may follow this idea:

```bash
python /path/to/FEMTO_1.0/scripts/main.py
```

Or, when using a virtual environment:

```bash
/path/to/venv/bin/python /path/to/FEMTO_1.0/scripts/main.py
```

Use the actual project path and Python environment path on the Jetson device.

Before adding the script to Startup Applications, test the runtime manually first to confirm that:

- The model path is correct
- The CSI camera opens successfully
- Servo pins work correctly
- Audio files can be loaded
- The TensorRT engine runs properly
- GPIO permissions are available
- The shutdown card behavior works as expected

---

## 12. Shutdown Card Operation

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

---

## 13. Common Deployment Issues

### CSI camera cannot be opened

Possible causes:

- CSI camera is not connected correctly
- Camera ribbon cable is loose
- GStreamer pipeline does not match the camera setup
- Camera is already being used by another process

Check the camera connection and test the camera separately before running the full system.

### TensorRT engine fails to load

Possible causes:

- `.engine` file path is incorrect
- TensorRT engine was built for a different device or environment
- JetPack, TensorRT, CUDA, or Ultralytics versions are not compatible
- The model file is missing from the actual deployment path

Re-export the model on the target Jetson device when possible.

### Servo does not move

Possible causes:

- Incorrect pin connection
- PWM pin is not configured correctly
- Servo power supply is insufficient
- Ground is not shared between Jetson and servo power source
- Duty-cycle value is outside the usable range

Use `scripts/calibrate_servo_angle.py` to test servo movement manually.

### Rotation servo jitters

The rotation servo on pin 32 is intentionally designed to release PWM after movement. This reduces mechanical jitter caused by holding the servo signal continuously.

### Audio does not play

Possible causes:

- Audio file path is incorrect
- Audio output device is not configured
- Pygame mixer cannot initialize
- Audio files are missing from the actual deployment path

Check audio output and update the paths in `configs/system_config.yaml`.

### System does not start automatically

Possible causes:

- Startup Applications command uses the wrong path
- Python environment is not activated
- Model or audio paths are still placeholder paths
- Required permissions are missing
- Camera is not ready at boot time

Use absolute paths in the Startup Applications command if needed.

---

## 14. Deployment Notes

This repository uses placeholder paths to make the project structure easier to understand without including actual model or audio files.

For real deployment, update the configuration files and runtime script to match the actual Jetson environment.

Important deployment notes:

- Use JetPack-compatible AI packages
- Use a TensorRT `.engine` model for deployment
- Replace all placeholder paths with actual deployment paths
- Test the CSI camera before running the full system
- Test servo duty cycles before full operation
- Use stable power for the Jetson and servo motors
- Avoid directly cutting power during operation
- Use the shutdown card or proper OS shutdown when possible
- Confirm all paths before adding the script to Startup Applications

---

## 15. Conclusion

Femto 1.0 is deployed as an Edge AI system on NVIDIA Jetson Orin Nano using a TensorRT YOLO model, CSI camera input, PWM-based servo control, audio feedback, and safe shutdown handling.

The deployment setup is designed for a practical embedded AI prototype where computer vision inference is connected directly to a physical sorting mechanism.