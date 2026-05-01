# Standardization Plan

This document records the conservative repository-standardization pass. It separates what was standardized from what intentionally remains unchanged because it may affect hardware behavior.

## Standardized

- Added repository hygiene for Python caches, test caches, coverage output, build output, logs, local config overrides, model artifacts, datasets, audio, video, and IDE files.
- Added `.gitattributes` for text line endings and binary handling of images, audio, video, and model artifacts.
- Added `pyproject.toml` with non-invasive test/format/lint tool configuration only.
- Added `requirements-dev.txt` for minimal test tooling.
- Added `configs/system_config.example.yaml` as a reference template matching the active config schema.
- Added hardware-free tests under `tests/`.
- Added `tools/preflight_check.py` to validate configs without importing Jetson hardware modules.
- Added focused documentation for configuration, development checks, and repository structure.
- Added README/deployment guidance for preflight and hardware-free checks.
- Extracted Phase 2A pure logic for motion detection, waste decision buffering, and shutdown-card confirmation into hardware-free modules with unit tests.

## Intentionally Unchanged

- Model inference behavior.
- Camera behavior and GStreamer pipeline.
- Jetson.GPIO import and cleanup behavior.
- Servo pins, PWM frequency, duty cycles, timing, and cleanup behavior.
- Shutdown-card and OS poweroff behavior.
- Benchmark numbers, result claims, and performance images.
- Runtime category names such as `Recycle Waste`.
- Active `configs/system_config.yaml` schema.
- Production runtime entry point `python scripts/run_system.py`.
- Hardware boundaries in `src/femto/app.py`; camera, YOLO, audio, servo, GPIO, and shutdown side effects remain owned by the runtime app.

## Requires Real Jetson / Hardware Validation

- Running `scripts/run_system.py`.
- Loading the TensorRT `.engine` model.
- Opening the CSI camera through the configured GStreamer pipeline.
- Initializing `Jetson.GPIO`.
- Moving rotation and tilt servos.
- Playing audio through the Jetson audio device.
- Detecting the shutdown card and executing poweroff behavior.
- Verifying timing, PWM release behavior, and physical sorting reliability.

## Later Changes Requiring Approval

- Renaming `Recycle Waste` to `Recyclable Waste` or another canonical label.
- Moving `Jetson.GPIO` behind an adapter.
- Adding camera source modes or changing pipeline generation.
- Extracting `src/femto/app.py` into camera, detector, audio, motion, decision, shutdown, and resource modules.
- Changing shutdown behavior or adding a default dry-run mode.
- Changing servo calibration values or timing.
- Converting the repository into an installable Python package.
- Adding a systemd deployment unit.
- Updating benchmark claims or result images.
