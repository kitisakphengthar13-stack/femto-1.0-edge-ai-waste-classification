# Hardware Validation Checklist

This checklist is for validating Femto 1.0 on the target Jetson hardware after repository standardization and Phase 2A pure-logic extraction.

Phase 2A status: hardware-validation pending.

Phase 2A extracted only pure logic for motion detection, waste decision buffering, and shutdown-card confirmation. It did not intentionally change camera setup, YOLO invocation, audio playback, Jetson.GPIO usage, servo timing, cleanup, or poweroff behavior. The full runtime still needs validation on the Jetson before the refactor is considered complete.

---

## Pre-Run Checks

```text
[ ] TensorRT .engine model exists on the Jetson.
[ ] configs/system_config.yaml points to the correct model path.
[ ] Audio files exist at the configured paths.
[ ] CSI camera is connected.
[ ] Servo power is stable.
[ ] Jetson and servo power supply share ground.
[ ] GPIO permissions are available.
[ ] Shutdown card is available for testing.
[ ] The test area is clear and safe for servo movement.
```

Run the preflight checker first:

```bash
python tools/preflight_check.py
```

Expected:

```text
[ ] No FAIL messages for model path.
[ ] No FAIL messages for audio paths.
[ ] Category mappings match servo and audio config entries.
```

---

## 1. Clean Startup

Command:

```bash
python scripts/run_system.py
```

Validate:

```text
[ ] Program starts without Python import errors.
[ ] YOLO/model initialization begins without path errors.
[ ] Camera initialization begins.
[ ] Audio initialization begins.
[ ] Servo controller initializes.
[ ] Startup alert plays, if configured.
[ ] Console reaches the ready message.
```

Notes:

```text
Observed result:
Issues:
```

---

## 2. CSI Camera Open

Validate:

```text
[ ] CSI camera opens successfully.
[ ] No "CSI camera could not be opened" runtime error.
[ ] No repeated camera frame drop warnings during normal operation.
[ ] Camera image orientation matches expected `flip_method`.
[ ] Camera resolution matches configured width/height.
```

Notes:

```text
Observed result:
Issues:
```

---

## 3. YOLO TensorRT / Model Loading

Validate:

```text
[ ] TensorRT `.engine` file loads successfully.
[ ] Model task remains `detect`.
[ ] No TensorRT/CUDA/Ultralytics compatibility error appears.
[ ] First inference completes after motion is detected.
[ ] Class names returned by the model match configs/class_mapping.yaml.
```

Notes:

```text
Model path:
JetPack version:
TensorRT version:
Observed result:
Issues:
```

---

## 4. Motion-Triggered YOLO Wake Behavior

Validate idle behavior:

```text
[ ] With no object movement, YOLO inference does not run continuously.
[ ] No repeated sorting decisions occur while the scene is idle.
```

Validate motion behavior:

```text
[ ] Moving an object in front of the camera wakes YOLO.
[ ] YOLO stays awake for the configured `yolo_awake_duration_seconds`.
[ ] Inference buffers reset after YOLO goes back to sleep.
[ ] Servo-active state still keeps YOLO awake during sorting movement.
```

Phase 2A check:

```text
[ ] Motion behavior matches the pre-refactor runtime behavior.
```

Notes:

```text
Observed result:
Issues:
```

---

## 5. Waste Decision Buffering

Validate single-object behavior:

```text
[ ] A single stable detected class increments the decision buffer.
[ ] Sorting triggers only after the configured `decision.buffer_size`.
[ ] Different detected class resets the consecutive count.
[ ] No detection does not trigger sorting.
[ ] Shutdown card class is ignored by waste sorting logic.
```

Validate multi-object behavior:

```text
[ ] Multiple detected objects reset the waste decision buffer when `allow_multiple_objects` is false.
[ ] No ambiguous multi-object scene triggers servo sorting.
```

Phase 2A check:

```text
[ ] Waste decision behavior matches the pre-refactor runtime behavior.
```

Notes:

```text
Observed result:
Issues:
```

---

## 6. Servo Sorting Timing

Validate each category:

```text
[ ] Recycle Waste routes to the expected bin.
[ ] General Waste routes to the expected bin.
[ ] Organic Waste routes to the expected bin.
[ ] Hazardous Waste routes to the expected bin.
```

Validate timing and movement:

```text
[ ] Rotation servo moves before tilt servo.
[ ] Tilt servo releases item.
[ ] Tilt servo returns to home position.
[ ] Rotation servo returns to home position.
[ ] Rotation PWM release behavior remains unchanged.
[ ] No unexpected jitter or stalled movement occurs.
[ ] Sorting cycle duration is consistent with configured timing.
```

Important:

```text
Do not change pins, PWM values, duty cycles, or timing during this validation unless a separate calibration task is approved.
```

Notes:

```text
Observed result:
Issues:
```

---

## 7. Audio Playback

Validate:

```text
[ ] Startup alert plays once during startup, if configured.
[ ] Recycle Waste audio plays for Recycle Waste sorting.
[ ] General Waste audio plays for General Waste sorting.
[ ] Organic Waste audio plays for Organic Waste sorting.
[ ] Hazardous Waste audio plays for Hazardous Waste sorting.
[ ] Shutdown alert plays before shutdown command, if configured.
[ ] Missing or invalid audio path produces an understandable error before deployment.
```

Notes:

```text
Observed result:
Issues:
```

---

## 8. Shutdown-Card Confirmation

Validate non-trigger cases:

```text
[ ] A single brief shutdown-card detection does not power off immediately.
[ ] Low-confidence shutdown-card detection does not count.
[ ] Multiple objects including shutdown card do not count as confirmed shutdown.
[ ] Any non-shutdown frame clears the shutdown confirmation buffer.
```

Validate trigger case:

```text
[ ] Continuous shutdown-card detection reaches configured `shutdown.buffer_size`.
[ ] Shutdown alert plays, if configured.
[ ] System waits configured `shutdown.delay_seconds`.
[ ] Runtime calls the existing poweroff path.
```

Phase 2A check:

```text
[ ] Shutdown-card confirmation behavior matches the pre-refactor runtime behavior.
```

Notes:

```text
Observed result:
Issues:
```

---

## 9. Cleanup On Ctrl+C

Validate:

```text
[ ] Pressing Ctrl+C exits cleanly.
[ ] Camera resource is released.
[ ] Servo controller attempts safe stop.
[ ] Pygame mixer quits.
[ ] Console prints successful cleanup message.
[ ] No traceback occurs during normal Ctrl+C cleanup.
```

Notes:

```text
Observed result:
Issues:
```

---

## 10. GPIO Cleanup

Validate:

```text
[ ] GPIO cleanup runs on Ctrl+C.
[ ] GPIO cleanup runs after shutdown-card path before poweroff.
[ ] A second launch after Ctrl+C does not fail due to stale GPIO/PWM state.
[ ] No unexpected Jetson.GPIO warnings appear outside known cleanup warnings.
```

Notes:

```text
Observed result:
Issues:
```

---

## 11. Poweroff / Reboot Behavior

Poweroff validation:

```text
[ ] Shutdown-card path calls the existing `poweroff` command.
[ ] If standard `poweroff` fails, existing sudo fallback behavior is preserved.
[ ] Filesystem shuts down cleanly.
[ ] Device powers off as expected.
```

Reboot path validation, if manually invoked or separately tested:

```text
[ ] Existing reboot command path works.
[ ] Existing sudo reboot fallback behavior is preserved.
```

Important:

```text
Do not change shutdown behavior during this validation. Dry-run or safer shutdown behavior should be implemented only as a separate approved task.
```

Notes:

```text
Observed result:
Issues:
```

---

## Completion Criteria

Phase 2A can be marked hardware-validated only when:

```text
[ ] Clean startup passes.
[ ] CSI camera opens reliably.
[ ] TensorRT model loads and runs inference.
[ ] Motion-triggered wake behavior matches expected behavior.
[ ] Waste decision buffering triggers sorting correctly.
[ ] All category servo routes work.
[ ] Audio playback works.
[ ] Shutdown-card confirmation works.
[ ] Ctrl+C cleanup works.
[ ] GPIO cleanup allows a clean second launch.
[ ] Poweroff/reboot behavior is confirmed.
```

Final validation notes:

```text
Validation date:
Jetson device:
JetPack version:
Model file:
Config file used:
Tester:
Summary:
```
