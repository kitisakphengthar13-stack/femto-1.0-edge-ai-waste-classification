# Femto 1.0 Project Audit

Audit date: 2026-05-01

Scope: repository structure, runtime code, configs, README, requirements, docs, deployment assumptions, Jetson / edge readiness, and consistency between code, configs, docs, and images.

This audit is read-only with respect to existing files. No existing source code, configuration, or documentation was modified.

Note: this audit predates the repository standardization pass and Phase 2A pure-logic extraction. It is retained as historical context. Current status updates are listed below so the original findings are not mistaken for the latest repository state.

---

## Current Status Update

The following items have been completed after the original audit:

- Added `requirements-dev.txt` for minimal hardware-free test tooling.
- Added `pyproject.toml` with non-invasive tool configuration.
- Added `configs/system_config.example.yaml` as a reference template matching the active config schema.
- Added `tools/preflight_check.py` for hardware-free configuration and asset-path validation.
- Added hardware-free tests under `tests/`.
- Added `src/femto/motion_detector.py` for pure frame-difference motion detection.
- Added `src/femto/decision_buffer.py` for pure waste decision buffering.
- Added `src/femto/shutdown_detection.py` for pure shutdown-card confirmation.
- Added `docs/hardware_validation_checklist.md` for target-device validation.

Remaining current risks:

- Full Jetson and hardware validation for Phase 2A is still pending.
- `Jetson.GPIO` is still imported at runtime/module import boundaries in hardware-related code.
- Camera, model, audio, GPIO, servo orchestration, cleanup, and OS shutdown side effects still remain in `src/femto/app.py` and related hardware modules.
- Result images and benchmark numbers still do not have a machine-readable result manifest with test date, model artifact, config, JetPack, TensorRT, or sample-count metadata.
- `tools/model_training.py` and `tools/model_export.py` still use placeholder paths and are example scripts, not plug-and-play CLIs.

The original audit sections below should be read with this update in mind.

---

## Executive Summary

Femto 1.0 is organized clearly enough for a prototype: runtime code lives under `src/femto/`, the launch script is isolated in `scripts/`, operational configuration is in `configs/`, non-runtime utilities are in `tools/`, and documentation is separated under `docs/` and `models/README.md`. The repository tells a coherent story about an Edge AI waste sorting prototype using YOLO, TensorRT, Jetson Orin Nano, CSI camera input, servo control, audio feedback, and shutdown-card handling.

The strongest areas are project structure, documentation breadth, and the decision to move runtime values into YAML. The main weaknesses are deployment reproducibility, responsibility separation inside `src/femto/app.py`, weak config validation, placeholder paths in deployable config, and a dependency file that is useful as a note but not sufficient as an installable environment definition. The code and docs mostly agree, but there are important inconsistencies around category naming, missing model/audio assets, Jetson-specific dependencies, and how ready the repository is to run from a fresh clone.

Overall status: good prototype repository, not yet production-ready or fully reproducible for Jetson deployment.

---

## Score Table

| Area | Score | Assessment |
|---|---:|---|
| Repository structure | 8/10 | Clear top-level separation between configs, docs, models, scripts, source, and tools. |
| Refactor readiness | 6/10 | Current structure is improved, but `src/femto/app.py` remains a large integration module. |
| Responsibility separation | 5/10 | Servo and mapping are separated; camera, detector, audio, motion, decision buffering, shutdown, and cleanup are still bundled in one class. |
| Configuration consistency | 6/10 | YAML centralizes values, but validation is shallow and deployable config still contains placeholder paths. |
| README quality | 8/10 | Comprehensive and useful for portfolio review; could better separate "documented prototype" from "ready-to-run package." |
| `requirements.txt` quality | 4/10 | Dependencies are unpinned and incomplete for actual Jetson runtime. |
| Documentation consistency across `docs/` | 7/10 | Broad and coherent, but repeats large sections and lacks versioned test/deployment evidence. |
| Deployment readiness | 4/10 | Deployment guide is useful, but fresh-clone execution is blocked by placeholder paths, missing assets, and Jetson-specific setup. |
| Jetson / edge assumptions | 5/10 | Hardware assumptions are documented but hardcoded in runtime imports and camera pipeline behavior. |
| End-to-end code/config/docs/images consistency | 6/10 | Most claims line up, but runtime config, asset availability, category labels, and measurable evidence need tighter traceability. |

---

## Repository Structure

Current layout:

| Path | Role | Audit Notes |
|---|---|---|
| `README.md` | Main project overview | Comprehensive, includes architecture, results, setup notes, and file map. |
| `requirements.txt` | Python dependency note | Too broad and unpinned for reproducible deployment. |
| `configs/system_config.yaml` | Runtime settings | Centralized but contains placeholder model/audio paths. |
| `configs/class_mapping.yaml` | Class/category mapping | Simple and clear; naming should be standardized with docs. |
| `src/femto/app.py` | Main runtime integration | Largest code file; owns too many runtime concerns. |
| `src/femto/config.py` | YAML loading | Validates only top-level sections. |
| `src/femto/class_mapper.py` | Class mapping | Small, clean responsibility. |
| `src/femto/motion_detector.py` | Pure motion detection | Added after original audit as Phase 2A hardware-free logic. |
| `src/femto/decision_buffer.py` | Pure waste decision buffering | Added after original audit as Phase 2A hardware-free logic. |
| `src/femto/shutdown_detection.py` | Pure shutdown-card confirmation | Added after original audit as Phase 2A hardware-free logic. |
| `src/femto/servo_controller.py` | Servo PWM and FSM | Good separation from app loop. |
| `scripts/run_system.py` | Main entry point | Clean entry point, but uses direct `sys.path` manipulation. |
| `tools/calibrate_servo_angle.py` | Calibration utility | Duplicates servo wrapper/config values instead of reusing runtime config. |
| `tools/model_training.py` | Training example | Placeholder script, not a configurable training CLI. |
| `tools/model_export.py` | Export example | Placeholder script, not a configurable export CLI. |
| `docs/` | Architecture, results, deployment | Strong breadth, with repeated material across files. |
| `docs/images/` | Evidence images | Useful evidence set, but no manifest linking images to test date/config. |
| `models/README.md` | Model placement docs | Good explanation of why model artifacts are omitted. |

---

## Severity-Ranked Issues

### Critical

#### 1. Fresh-clone runtime cannot run with committed config

Evidence:

- `configs/system_config.yaml:2` uses `path/to/best.engine`.
- `configs/system_config.yaml:16` uses `path/to/shutdown_alert.mp3`.
- `configs/system_config.yaml:32` uses `path/to/start_alert.mp3`.
- `configs/system_config.yaml:34-37` use placeholder category audio paths.
- `src/femto/app.py:91-94` loads the YOLO model directly from the configured path.
- `src/femto/app.py:132-143` loads configured audio files directly.

Impact:

The repository is documented as a runnable system, but the committed config is a template-like config. A fresh clone will fail during model or audio initialization unless every path is manually replaced.

Recommended fixes:

- Add an explicit `configs/system_config.example.yaml` and reserve `configs/system_config.yaml` for a local deployable file, or clearly mark the committed file as an example.
- Validate model and audio paths before runtime initialization and print actionable errors.
- Support disabling audio in config for headless or partial tests.
- Document a minimal smoke-test mode that does not require model, camera, audio, or GPIO.

Approval needed:

Changing config file strategy affects user workflow and should be approved before editing existing config/docs.

#### 2. Runtime is tightly coupled to Jetson hardware imports

Evidence:

- `src/femto/app.py:18` imports `Jetson.GPIO` at module import time.
- `src/femto/servo_controller.py:3` imports `Jetson.GPIO` at module import time.
- `tools/calibrate_servo_angle.py:1` imports `Jetson.GPIO` at module import time.
- `src/femto/app.py:98` opens a GStreamer camera pipeline.
- `src/femto/app.py:110` hardcodes `nvarguscamerasrc` in the generated pipeline.

Impact:

The package cannot be imported or smoke-tested on non-Jetson machines without Jetson.GPIO and Jetson camera support. This blocks CI, local static testing, and many development workflows.

Recommended fixes:

- Move Jetson.GPIO imports behind a hardware adapter boundary.
- Add a `gpio_backend` abstraction with `jetson` and `mock` implementations.
- Add camera source modes such as `csi`, `usb`, `video_file`, and `mock`.
- Make the GStreamer pipeline configurable or generated by a dedicated camera module.

Approval needed:

This is an architectural change and should be approved before implementation.

#### 3. System shutdown is invoked directly from application logic

Evidence:

- `src/femto/app.py:283-285` triggers `perform_system_shutdown(poweroff=True)` after shutdown-card buffering.
- `src/femto/app.py:398-410` runs `poweroff`, `reboot`, `sudo poweroff`, or `sudo reboot`.

Impact:

Power control is a high-impact operation embedded directly inside the app. It is difficult to test safely and difficult to disable for development or demos.

Recommended fixes:

- Add a config setting such as `shutdown.enabled` and `shutdown.command`.
- Add a dry-run mode for shutdown-card testing.
- Move shutdown execution into a `ShutdownHandler` with unit-testable behavior.
- Require an explicit deployment profile before executing OS poweroff.

Approval needed:

Any change to shutdown behavior should be approved and tested on the Jetson.

---

### High

#### 4. `src/femto/app.py` has too many responsibilities

Current status note: Phase 2A has extracted pure motion detection, waste decision buffering, and shutdown-card confirmation. The remaining concern is the side-effect boundary: camera setup, YOLO initialization and invocation, audio, servo orchestration, GPIO cleanup, signal handling, and OS shutdown execution still remain in the runtime app or hardware-related modules.

Evidence:

- At original audit time, `src/femto/app.py` owned model loading, camera setup, audio setup, motion detection, inference parsing, shutdown logic, decision buffering, servo orchestration, signal handling, and cleanup.
- Current `docs/system_architecture.md` identifies possible future side-effect modules such as `camera.py`, `detector.py`, `audio_player.py`, a shutdown execution boundary, and `resource_manager.py`.

Impact:

The app class is understandable now, but future changes will raise regression risk. Hardware, model, and runtime concerns are hard to test independently.

Recommended fixes:

- Pure logic extraction for `MotionDetector`, `WasteDecisionBuffer`, and shutdown-card confirmation is complete.
- Next extract side-effect boundaries such as `Camera`, `Detector`, `AudioPlayer`, and an OS shutdown handler, after hardware validation planning.
- Keep `FemtoApp` as the orchestrator rather than the owner of every subsystem.

#### 5. Config validation is shallow

Evidence:

- `src/femto/config.py:18-34` checks only top-level sections in `system_config.yaml`.
- `src/femto/config.py:37-45` checks only that `waste_classes` exists and defaults `special_classes`.
- `src/femto/app.py` and `src/femto/servo_controller.py` access many nested keys directly, such as `system_config["model"]`, `servo_config["rotate_pin"]`, and timing/category fields.

Impact:

Malformed YAML or missing nested values will fail later with less helpful runtime errors, possibly after hardware initialization starts.

Recommended fixes:

- Add schema-style validation for required nested keys and value types.
- Validate that `class_mapping.yaml` categories exist in `servo.category_positions` and `audio.category_sounds`.
- Validate servo duty cycles, positive timings, buffer sizes, confidence thresholds, and odd/effective blur kernel values.
- Consider a typed config model using dataclasses or Pydantic if dependencies are acceptable.

#### 6. Historical: category naming was inconsistent between prose and config

Current status note: current runtime config still uses `Recycle Waste`, and current docs intentionally preserve that runtime label. Historical references to `Recyclable Waste` remain in this audit only as examples of earlier drift or as human-readable audio wording, not as runtime category keys.

Evidence:

- At original audit time, some README prose used `Recyclable waste` / `Recyclable Waste`.
- `configs/class_mapping.yaml:2-4` use `Recycle Waste`.
- `configs/system_config.yaml:34` and `configs/system_config.yaml:49` use `Recycle Waste`.
- At original audit time, some deployment prose used `Recyclable Waste` while config examples used `Recycle Waste`.

Impact:

The runtime is internally consistent around `Recycle Waste`, but the docs use both `Recycle` and `Recyclable`. This can cause users to edit YAML using a documented label that does not match servo/audio keys.

Recommended fixes:

- Choose one canonical category label.
- Update all docs, config keys, audio keys, and result tables to match.
- Add validation that every mapped category has servo and audio entries.

Approval needed:

Renaming runtime categories touches config and may affect audio filenames, existing labels, and result documentation.

#### 7. `requirements.txt` is not reproducible and does not fully represent runtime dependencies

Evidence:

- `requirements.txt` lists unpinned `ultralytics`, `opencv-python`, `pygame`, `PyYAML`, and `numpy`.
- `requirements.txt:7-10` says PyTorch, TorchVision, TensorRT, CUDA-related libraries, and Jetson.GPIO should be installed separately.
- Runtime imports `Jetson.GPIO` in `src/femto/app.py:18` and `src/femto/servo_controller.py:3`.

Impact:

The file is useful as a human note but not as a stable environment definition. On Jetson, `opencv-python` from pip can conflict with JetPack-provided OpenCV/GStreamer support.

Recommended fixes:

- Split environment documentation into desktop/dev and Jetson deployment requirements.
- Pin or constrain package versions known to work with the tested JetPack version.
- Consider `requirements-dev.txt`, `requirements-jetson.txt`, or a container recipe.
- Document packages intentionally excluded from pip installation.

---

### Medium

#### 8. Tool scripts are examples, not production utilities

Evidence:

- `tools/model_training.py:10` uses `path/to/yolo26s.pt`.
- `tools/model_training.py:15` uses `path/to/data.yaml`.
- `tools/model_export.py:3` uses `path/to/best.pt`.
- `tools/calibrate_servo_angle.py:5-9` hardcodes servo pins and start duty cycles instead of reading `configs/system_config.yaml`.

Impact:

The `tools/` directory is documented as utilities, but the scripts are mostly hardcoded examples. Users must edit source files to train/export/calibrate, which conflicts with the repository's configuration-driven story.

Recommended fixes:

- Convert training/export tools to small CLIs using `argparse`.
- Let calibration read `configs/system_config.yaml` by default and allow CLI overrides.
- Keep placeholder values in docs, not executable utility defaults.

#### 9. Entrypoint relies on direct `sys.path` mutation

Evidence:

- `scripts/run_system.py:7-8` inserts `src/` into `sys.path`.

Impact:

This works for a script-based prototype, but it is not ideal for packaging, testing, or installation as a module.

Recommended fixes:

- Add `pyproject.toml` with package metadata.
- Run through `python -m femto` or a console script entry point after editable install.
- Keep `scripts/run_system.py` only as a thin compatibility wrapper if desired.

Approval needed:

Packaging changes affect install and run commands.

#### 10. Historical: automated tests and smoke checks were not present

Current status note: hardware-free tests and `tools/preflight_check.py` now exist. They intentionally do not validate Jetson hardware, camera access, model loading, audio, GPIO, servo movement, or OS shutdown behavior.

Evidence:

- At original audit time, no `tests/` directory existed.
- Runtime still imports Jetson-only modules at import time in hardware-related modules, making full runtime import-level tests hard off-device.

Impact:

Refactors and config changes have no automated safety net. This is risky because runtime behavior controls physical hardware and shutdown.

Recommended fixes:

- Add tests for `ClassMapper`, config validation, motion detection, decision buffering, and shutdown-card buffering.
- Add mock GPIO, mock camera, and mock detector backends.
- Add a non-hardware smoke command that validates configs and imports pure modules.

#### 11. Documentation repeats large blocks and can drift

Evidence:

- Runtime structure appears in `README.md`, `docs/deployment.md`, and `docs/system_architecture.md`.
- Model export/training examples appear in both `docs/deployment.md` and `models/README.md`.
- Deployment and README both list similar repository trees and component descriptions.

Impact:

The current docs are readable, but maintaining the same claims in multiple files raises drift risk.

Recommended fixes:

- Make `README.md` the short overview.
- Keep deployment-only steps in `docs/deployment.md`.
- Keep architecture internals in `docs/system_architecture.md`.
- Keep model artifact policy in `models/README.md`.
- Replace duplicated long examples with cross-links.

#### 12. Performance evidence lacks traceability metadata

Evidence:

- `docs/results.md` reports 93.3% software accuracy and 1.80 seconds/item hardware sorting time.
- `docs/images/` contains evidence images including `software_performance.png`, `hardware_performance.png`, `yolo_verbose.png`, and `jtop.png`.
- No manifest records test date, model hash/name, config version, JetPack version, TensorRT version, or dataset/sample counts.

Impact:

The evidence is useful for portfolio review, but not enough for reproducible benchmarking or regression comparison.

Recommended fixes:

- Add a results manifest documenting test date, hardware, JetPack, model artifact, config, sample counts, and methodology.
- Link each result image to the relevant test setup.
- Add a changelog note when code structure changes without re-running benchmarks.

---

### Low

#### 13. `models/README.md` is strong but belongs partly in deployment docs

Evidence:

- `models/README.md` includes training and export references, model placement, and deployment compatibility guidance.

Impact:

The file is useful, but some content overlaps with `docs/deployment.md`.

Recommended fixes:

- Keep model placement and artifact policy in `models/README.md`.
- Move long training/export workflow details to a dedicated `docs/model_workflow.md` if the project grows.

#### 14. `src/femto/__init__.py` is empty

Evidence:

- `src/femto/__init__.py` has 0 lines.

Impact:

This is acceptable, but package versioning or package exports are not defined.

Recommended fixes:

- Add `__version__` only if packaging is introduced.
- Otherwise leave it empty.

---

## Refactor Opportunities

Recommended target responsibilities:

| Proposed Module | Responsibility | Source to Extract From |
|---|---|---|
| `camera.py` | Camera pipeline construction and frame reading | `src/femto/app.py` |
| `detector.py` | YOLO model loading and inference result normalization | `src/femto/app.py` |
| `motion_detector.py` | Frame differencing and wake logic | Completed in `src/femto/motion_detector.py` |
| `decision_buffer.py` | Consecutive class confirmation and multi-object rules | Completed in `src/femto/decision_buffer.py` |
| `audio_player.py` | Pygame initialization and sound playback | `src/femto/app.py` |
| `shutdown_handler.py` | Future OS shutdown side-effect boundary | Pure confirmation completed in `src/femto/shutdown_detection.py`; OS command execution remains in `src/femto/app.py` |
| `gpio_backend.py` | Jetson/mock GPIO adapter | `src/femto/servo_controller.py`, `tools/calibrate_servo_angle.py` |
| `resource_manager.py` | Ordered cleanup of camera, audio, GPIO, and servos | `src/femto/app.py` |

Pure, testable logic has already been extracted for Phase 2A. Remaining refactor priority should focus on hardware and OS side-effect boundaries after hardware validation planning.

---

## Code Responsibility Separation

Current state:

- Good: `ClassMapper` has one clear responsibility.
- Good: `ServoController` separates servo behavior from the main loop.
- Good: `scripts/run_system.py` is a thin launcher.
- Needs work: `FemtoApp` still owns nearly all runtime integration.
- Needs work: calibration duplicates servo setup instead of reusing shared config or controller code.
- Needs work: shutdown execution is mixed with detection decision flow.

Recommended direction:

- Keep `FemtoApp` as an orchestrator.
- Make subsystem classes responsible for hardware/model/audio details.
- Make decision logic pure and independently testable.
- Keep OS-level actions behind explicit interfaces.

---

## Configuration Consistency

Positive findings:

- `configs/system_config.yaml` centralizes model, decision, shutdown, motion, camera, audio, servo, and runtime values.
- `configs/class_mapping.yaml` separates model class names from sorting categories.
- Servo category keys and class-mapping category values currently match for runtime categories.

Gaps:

- Placeholder paths make the committed config non-deployable.
- Config validation checks only top-level sections.
- Historical docs used both `Recycle Waste` and `Recyclable Waste`; current runtime-facing docs should keep `Recycle Waste` unless the runtime config is renamed deliberately.
- Training/export/calibration tools do not consume shared config.
- Camera pipeline values are only partially configurable; several GStreamer settings are hardcoded in `src/femto/app.py`.

Recommended fixes:

- Add nested config validation.
- Add cross-file validation between class mapping, servo categories, and audio categories.
- Define a canonical category vocabulary.
- Split example config from local deployment config.
- Add profile support for `jetson`, `mock`, and possibly `desktop-dev`.

---

## README.md and requirements.txt Quality

### README.md

Strengths:

- Clear project purpose.
- Good system overview and architecture explanation.
- Documents the actual repository structure.
- Explains model format, runtime flow, results, and omitted assets.

Improvements:

- Make the "not directly runnable from fresh clone" status more prominent.
- Standardize category naming.
- Shorten duplicated details by linking deeper docs.
- Add a quick preflight checklist before `python scripts/run_system.py`.
- Add expected failure modes when placeholder paths are unchanged.

### requirements.txt

Strengths:

- Correctly warns that Jetson GPU/AI packages require special handling.
- Keeps obvious Python-level dependencies visible.

Improvements:

- Pin or constrain versions.
- Split desktop/dev and Jetson requirements.
- Avoid implying that `pip install -r requirements.txt` is sufficient for deployment.
- Document JetPack-tested versions.
- Account for `Jetson.GPIO`, TensorRT, PyTorch, TorchVision, CUDA, and OpenCV/GStreamer compatibility.

---

## Documentation Consistency Across docs/

Strengths:

- `docs/system_architecture.md` gives a coherent architecture explanation.
- `docs/deployment.md` is detailed and practical for Jetson setup.
- `docs/results.md` distinguishes system-level prototype results from YOLO validation metrics.
- Image references are present and aligned with the narrative.

Gaps:

- Much of the runtime structure and model workflow is repeated across docs.
- No single source of truth exists for category labels.
- No test metadata manifest exists for the result images.
- Deployment instructions now include `tools/preflight_check.py`, but this remains hardware-free and does not validate camera, GPIO, model loading, audio, servo movement, or shutdown execution.

Recommended fixes:

- Add a short docs index if more files are added.
- Reduce repeated blocks.
- Add result metadata.
- Add config validation and smoke-test instructions once tooling exists.

---

## Deployment Readiness

Current readiness: prototype deployment guide is strong, automated deployment readiness is weak.

Deployment blockers from a fresh clone:

- No model artifact is included.
- No audio assets are included.
- Committed config contains placeholder paths.
- Jetson.GPIO is required at import time.
- CSI camera pipeline requires Jetson camera stack.
- TensorRT engine compatibility depends on JetPack/TensorRT/CUDA versions.
- No install script, container file, systemd unit, or startup application file is provided.
- `tools/preflight_check.py` now validates config shape, model/audio paths, and class/category consistency. It does not validate camera access, GPIO access, model loading, audio playback, servo movement, or shutdown execution.

Recommended deployment additions:

- Extend `tools/preflight_check.py` only if future work needs broader environment checks; current behavior is hardware-free by design.
- Example `systemd` service or documented Startup Applications command with absolute paths.
- JetPack version matrix.
- Known-good package versions.
- Dry-run mode for shutdown card.
- Mock mode for local development and CI.

---

## Jetson / Edge Device Assumptions

Documented assumptions:

- NVIDIA Jetson Orin Nano.
- JetPack 6.x.
- TensorRT `.engine` deployment.
- CSI camera via GStreamer.
- Jetson.GPIO with BOARD pin numbering.
- PWM pins 32 and 33.
- Pygame audio output.
- OS-level `poweroff` for shutdown-card operation.

Implicit or hardcoded assumptions:

- `nvarguscamerasrc` is available.
- OpenCV has GStreamer support.
- Camera resolution 1280x720 is valid.
- The current user can access camera, GPIO, audio, and poweroff commands.
- Servo power and ground wiring are correct.
- Audio files exist and Pygame can initialize an output device.
- The TensorRT engine was built for the exact deployment environment.

Recommended fixes:

- Make assumptions explicit in a preflight checker.
- Add mock/dev modes.
- Add clearer failure messages for missing hardware capabilities.
- Move hardcoded camera pipeline details into config or a camera builder.

---

## End-to-End Consistency Between Code, Configs, Docs, and Images

Mostly consistent:

- Code loads `configs/system_config.yaml` and `configs/class_mapping.yaml`, matching docs.
- Runtime categories in config align with servo and audio keys.
- Docs correctly state that models, datasets, and audio files are omitted.
- Image assets referenced by docs exist under `docs/images/`.
- Results docs avoid claiming mAP/precision/recall and describe system-level measurements.

Inconsistent or incomplete:

- Historical docs used `Recyclable Waste`, `Recyclable waste`, and `Recycle Waste`; current runtime-facing docs should keep `Recycle Waste`.
- The README run command does not make clear enough that committed placeholders must be replaced first.
- Tool scripts are described as utilities, but they require source edits or placeholder replacement before use.
- Result images are not tied to a specific config/model/test manifest.
- Deployment docs describe JetPack-specific caution but do not provide a reproducible environment definition.

---

## Proposed Phased Refactor Plan

### Phase 1: Stabilize Without Behavioral Change

- Config preflight validation and cross-checks for category mapping, servo positions, and audio category keys have been added.
- Add clearer error messages for placeholder model/audio paths.
- Tests for `ClassMapper`, config validation, preflight behavior, and Phase 2A pure logic have been added.
- Add a dry-run flag for shutdown behavior.

### Phase 2: Extract Pure Runtime Logic

- `MotionDetector`, `WasteDecisionBuffer`, and pure shutdown-card confirmation have been extracted with hardware-free tests.
- Full Jetson and hardware validation remains pending.

### Phase 3: Add Hardware Boundaries

- Extract `Camera` and `Detector`.
- Extract `AudioPlayer`.
- Introduce GPIO backend abstraction.
- Add mock mode for local development and CI.
- Update calibration tool to read shared config.

### Phase 4: Improve Packaging and Deployment

- `pyproject.toml` has been added for non-invasive tool configuration. Packaging metadata remains future work if needed.
- Replace `sys.path` launcher behavior with package entry points.
- Add Jetson requirements or container documentation.
- A hardware-free preflight command has been added. Broader Jetson environment validation remains future work.
- Add optional `systemd` unit documentation.

### Phase 5: Documentation and Evidence Cleanup

- Keep category vocabulary aligned around the current runtime label `Recycle Waste`, unless a separate approved rename updates config, docs, assets, and deployment together.
- Reduce duplicated docs.
- Add result metadata manifest.
- Add deployment version matrix.
- Re-run and record benchmark results after significant runtime refactors.

---

## Changes Safe to Automate

These changes are low-risk and can be automated once approved as a work batch:

- A hardware-free preflight validation script and tests for current pure validation paths have been added.
- Add a docs index or result metadata template.
- `requirements-dev.txt` has been added. The current preflight checker reports failures for placeholder or missing required paths.
- Add a `.gitkeep` or README note for expected local-only asset directories if desired.
- Convert tool scripts to accept CLI arguments while preserving existing defaults.
- Add a mock GPIO backend only if runtime default behavior remains Jetson.

---

## Changes That Need Approval First

These changes affect runtime behavior, deployment workflow, naming, or hardware safety:

- Renaming `Recycle Waste` to `Recyclable Waste` or any other canonical category name.
- Changing `configs/system_config.yaml` from placeholder config to deployable local config.
- Further changing config-file workflow beyond the already-added `configs/system_config.example.yaml`.
- Changing shutdown-card behavior or adding dry-run defaults.
- Moving Jetson.GPIO imports behind adapters.
- Changing camera pipeline generation or supported camera source modes.
- Changing servo timing, duty cycles, pin defaults, or PWM release behavior.
- Converting the existing non-packaging `pyproject.toml` into installable package metadata.
- Replacing Startup Applications guidance with a `systemd` service.
- Updating benchmark claims or result images.

---

## Final Assessment

Femto 1.0 is a solid, well-documented edge AI prototype repository. Its current organization is suitable for portfolio review and continued development, but not yet for reproducible deployment or safe large-scale refactoring. The next best investment is not a broad rewrite; it is a narrow stabilization pass: validate configs, standardize category labels, add non-hardware tests, and isolate pure decision logic. After that, hardware abstraction and packaging work will be much safer.
