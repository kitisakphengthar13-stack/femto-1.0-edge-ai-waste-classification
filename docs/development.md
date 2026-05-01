# Development

This document covers development checks that are safe to run away from the Jetson hardware.

## Development Dependencies

Install the minimal test tooling with:

```bash
pip install -r requirements-dev.txt
```

Runtime dependencies remain documented in `requirements.txt`. Jetson-specific packages such as TensorRT, PyTorch, TorchVision, OpenCV/GStreamer support, and `Jetson.GPIO` must still match the target JetPack environment.

## Hardware-Free Checks

Run the preflight checker:

```bash
python tools/preflight_check.py
```

Run the hardware-free tests:

```bash
python -m pytest
```

Run a syntax/import compile check without importing the Jetson runtime app:

```bash
python -m compileall tools tests src/femto/class_mapper.py src/femto/config.py src/femto/motion_detector.py src/femto/decision_buffer.py src/femto/shutdown_detection.py
```

Do not use these checks as hardware validation. They do not load the YOLO model, open the CSI camera, initialize audio, touch GPIO, move servos, or execute shutdown behavior.

## Test Scope

Current tests cover:

- `ClassMapper` behavior.
- Existing YAML loader validation behavior.
- Preflight validation using temporary YAML fixtures.
- Pure motion detection logic using generated frames.
- Pure waste decision buffering logic using fake class names.
- Pure shutdown-card confirmation logic using fake class names and confidence values.

Current tests intentionally avoid:

- `src/femto/app.py`
- `src/femto/servo_controller.py`
- `Jetson.GPIO`
- camera access
- YOLO model loading
- audio devices
- servo movement
- system shutdown

## Tool Configuration

`pyproject.toml` contains non-invasive tool configuration only:

- pytest test paths and Python path.
- Black line length.
- Ruff line length and lint rule selection.

It does not convert the project into an installable package.

## Phase 2A Pure Logic Extraction

Phase 2A extracts only hardware-free logic from `src/femto/app.py`:

- `src/femto/motion_detector.py`
- `src/femto/decision_buffer.py`
- `src/femto/shutdown_detection.py`

The runtime app still owns camera setup, YOLO model loading and invocation, audio playback, servo calls, GPIO cleanup, signal handling, and shutdown command execution. Hardware boundaries are intentionally unchanged until Jetson testing is available.
