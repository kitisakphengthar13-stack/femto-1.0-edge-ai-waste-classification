# Configuration

Femto 1.0 uses YAML files under `configs/` to keep deployment values outside the Python source code.

## Active Files

| File | Purpose |
|---|---|
| `configs/system_config.yaml` | Active runtime configuration loaded by `scripts/run_system.py`. |
| `configs/class_mapping.yaml` | Active YOLO class-to-category mapping loaded by `scripts/run_system.py`. |
| `configs/system_config.example.yaml` | Reference template for the active system config schema. It is not loaded automatically. |

Do not assume a fresh clone is ready to run on hardware. The active config may contain placeholder model and audio paths until it is prepared for a specific Jetson deployment.

## Preflight Check

Run this from the repository root before launching the hardware runtime:

```bash
python tools/preflight_check.py
```

The preflight check is read-only. It validates YAML shape, detects placeholder or missing model/audio paths, and checks that mapped waste categories have matching servo and audio entries. It does not import `Jetson.GPIO`, open the camera, load the YOLO model, play audio, move servos, or modify files.

## Required System Sections

`configs/system_config.yaml` is expected to contain these top-level sections:

| Section | Main Responsibility |
|---|---|
| `model` | TensorRT/YOLO model path, task, and confidence threshold. |
| `decision` | Detection buffering and multi-object decision behavior. |
| `shutdown` | Shutdown-card class, threshold, buffer, delay, and alert sound path. |
| `motion` | Motion detection thresholding and YOLO wake duration. |
| `camera` | CSI camera sensor ID, resolution, and flip method. |
| `audio` | Startup and category sound file paths. |
| `servo` | Pins, PWM frequency, start position, category positions, and movement timing. |
| `runtime` | Loop sleep and dropped-frame sleep timing. |

## Category Names

The active runtime category labels are currently:

```text
Recycle Waste
General Waste
Organic Waste
Hazardous Waste
```

These exact strings must match across:

- `configs/class_mapping.yaml`
- `configs/system_config.yaml` `audio.category_sounds`
- `configs/system_config.yaml` `servo.category_positions`

Decision note: some documentation historically used the wording `Recyclable Waste`. The runtime currently uses `Recycle Waste`. Do not rename this category until the runtime config, audio assets, result docs, and hardware deployment have been reviewed together.

## Placeholder Paths

Placeholder paths such as `path/to/best.engine` and `path/to/recycle.mp3` must be replaced before running the hardware system.

The preflight checker reports placeholder or missing paths as failures, but it does not edit the config.
