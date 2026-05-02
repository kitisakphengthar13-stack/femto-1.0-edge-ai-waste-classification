# Results

This document summarizes the reported prototype results of **Femto 1.0 — Edge AI Waste Classification System**, including software performance, hardware sorting performance, TensorRT runtime behavior, and Jetson runtime monitoring.

The software and hardware numbers in this document are reported prototype results across all 10 waste classes and are documented by the included image evidence.

The current repository structure has been refactored into a clearer runtime layout using `scripts/`, `src/femto/`, `configs/`, and `tools/`. The reported results below should be treated as system-level prototype results, not newly re-measured results after every code-structure change. They are not independently reproducible from this repository alone because the model artifact, deployment environment, audio assets, and result manifest are not included.

---

## 1. Overview

Femto 1.0 was documented with prototype tests from both software and hardware perspectives.

The software performance entry reports how accurately the prototype classified waste items across the 10 waste classes. This result is not a YOLO validation metric such as mAP, precision, or recall.

The hardware performance entry reports how long the physical sorting mechanism took to convey and sort each waste item into the target bin.

The two main overall results are:

| Metric | Result |
|---|---:|
| Overall software accuracy | 93.3% |
| Average hardware sorting time | 1.80 seconds / item |

The overall software accuracy is the reported average result across all 10 waste classes.

The average hardware sorting time is the reported average time across all 10 waste classes.

---

## 2. Result Scope

The values in this document represent **reported system-level prototype results** under controlled single-item operation.

They include the practical behavior of the running system, such as:

- Camera input behavior
- YOLO inference result used by the runtime system
- Waste class-to-category mapping
- Decision buffering behavior
- Physical sorting behavior
- Servo movement timing
- Jetson runtime operation

These results should not be interpreted as pure model validation metrics.

They are different from metrics such as:

```text
mAP
Precision
Recall
F1-score
Validation accuracy from a training dataset
```

The purpose of this result document is to show the documented behavior of the integrated Edge AI prototype. A future result manifest should record test date, model artifact, config, JetPack version, TensorRT version, sample counts, and test procedure.

---

## 3. Software Performance

The software performance section reports system-level classification accuracy for the prototype across the 10 waste classes.

This result is documented as runtime system accuracy, not a model validation metric such as mAP, precision, or recall.

### Detection Example

![Detection Example](images/detection_example.png)

The example above shows the deployed YOLO model detecting a waste item during system operation. The detection result is then used by the system for class-to-category mapping and sorting decision logic.

### Software Accuracy Result

![Software Performance](images/software_performance.png)

The reported prototype result is an overall software accuracy of **93.3%** across all 10 waste classes.

| Waste Class | Accuracy |
|---|---:|
| Plastic Bottle | 85% |
| Can | 97% |
| Paper | 97% |
| Plastic Bag | 74% |
| Instant Noodle | 100% |
| Face Mask | 92% |
| Banana | 100% |
| Apple | 99% |
| Orange | 89% |
| Battery | 100% |

The strongest reported class results were `Instant Noodle`, `Banana`, and `Battery`, each listed at 100% accuracy in the included result evidence.

The lowest-performing class was `Plastic Bag`, with 74% accuracy. This suggests that plastic bag detection was more difficult than other classes, likely due to shape variation, deformation, transparency, lighting changes, or visual similarity to the background.

---

## 4. Hardware Sorting Performance

The hardware performance section reports the physical sorting time required for the mechanism to convey and sort each waste item into the target bin.

This result is documented by the included hardware performance image, but the repository does not include a separate manifest that makes the measurement independently reproducible.

![Hardware Performance](images/hardware_performance.png)

The reported prototype result is an average hardware sorting time of **1.80 seconds per item** across all 10 waste classes.

| Waste Class | Average Sorting Time |
|---|---:|
| Plastic Bottle | 1.85 s |
| Can | 1.79 s |
| Paper | 1.77 s |
| Plastic Bag | 2.28 s |
| Instant Noodle | 1.72 s |
| Face Mask | 1.76 s |
| Banana | 1.66 s |
| Apple | 1.71 s |
| Orange | 1.73 s |
| Battery | 1.74 s |

Most classes were sorted under or near the 2.00-second target line.

`Plastic Bag` showed the highest average sorting time at approximately **2.28 seconds**, making it the slowest class in the hardware test. This result indicates that lightweight or deformable objects may require more stable mechanical handling than rigid objects.

---

## 5. TensorRT Inference Runtime

The trained YOLO model was converted from `.pt` format to TensorRT `.engine` format for deployment on NVIDIA Jetson Orin Nano.

![YOLO Verbose Runtime](images/yolo_verbose.png)

The included runtime log image shows TensorRT engine inference output. The inference input size is 640x640, and the per-frame processing time is shown in the YOLO verbose output.

TensorRT deployment was used because it is more suitable for optimized inference on NVIDIA Jetson hardware than running the original `.pt` model directly.

The inference runtime includes:

- Preprocessing time
- Model inference time
- Postprocessing time

These values help identify where runtime latency occurs during real-time operation.

---

## 6. Jetson Runtime Monitoring

Jetson runtime behavior was monitored using `jtop` during system operation.

![Jetson Runtime Monitoring](images/jtop.png)

The included monitoring image documents Jetson Orin Nano runtime resource usage during prototype operation.

The monitored resources include:

- CPU usage
- GPU usage
- RAM usage
- Power mode
- Running Python process
- GPU memory usage

This evidence supports the prototype deployment narrative, but a result manifest would be needed for independent reproduction of the exact test environment.

---

## 7. Runtime Refactor Note

The latest repository structure separates the runtime into clearer components:

```text
scripts/run_system.py
src/femto/app.py
src/femto/config.py
src/femto/class_mapper.py
src/femto/motion_detector.py
src/femto/decision_buffer.py
src/femto/shutdown_detection.py
src/femto/servo_controller.py
configs/system_config.yaml
configs/class_mapping.yaml
tools/preflight_check.py
tools/calibrate_servo_angle.py
tools/model_export.py
tools/model_training.py
```

This refactor improves code organization and makes runtime settings configurable through YAML files.

The refactor is intended to preserve the same core runtime behavior:

```text
Camera input
    ↓
Motion-triggered YOLO inference
    ↓
Single-object decision rule
    ↓
Consecutive detection buffering
    ↓
Class-to-category mapping
    ↓
Servo-based sorting
    ↓
Voice feedback
    ↓
Shutdown card handling
```

If new measurements are collected after further code or hardware changes, this document should be updated with the new test date, configuration, and measured results.

---

## 8. Result Summary

| Evaluation Area | Result |
|---|---|
| Software performance | 93.3% reported overall software accuracy |
| Hardware sorting performance | 1.80 seconds / item reported average sorting time |
| Model deployment format | TensorRT `.engine` |
| Runtime device | NVIDIA Jetson Orin Nano |
| Number of waste classes | 10 |
| Number of waste categories | 4 |

These results are reported system-level prototype results, not model evaluation metrics.

The results show that Femto 1.0 can perform real-time waste detection, waste category mapping, and physical sorting on an edge device.

The system demonstrates a complete camera-to-actuator pipeline, where the AI prediction result is used to control an actual sorting mechanism.

---

## 9. Limitations

Although the reported prototype results show stable overall performance, several limitations remain.

`Plastic Bag` had the lowest software accuracy and the highest hardware sorting time. This class is more difficult because plastic bags can deform, fold, reflect light, or appear in many different shapes.

The system currently works best when:

- One waste item is placed in the camera view at a time
- The object is visible clearly
- Lighting conditions are reasonably stable
- The item is positioned within the expected sorting area

The current decision logic intentionally rejects multiple detected objects in the same frame to avoid ambiguous sorting decisions.

Multi-object or multi-class disposal is not a supported result condition. When more than one object or class is detected in the same frame, the waste decision buffer is reset or rejected and no sorting action is triggered.

---

## 10. Future Improvements

Future improvements may include:

- Expanding the dataset with more variations of difficult classes
- Improving performance on deformable objects such as plastic bags
- Testing under more lighting conditions
- Adding object position control before sorting
- Improving the mechanical structure for more stable item handling
- Testing with more real-world waste samples
- Adding more sensors to support physical sorting reliability
- Optimizing TensorRT inference and camera pipeline performance further
- Re-testing the full system after major software or hardware changes
- Recording updated benchmark results after each major deployment revision

---

## 11. Conclusion

Femto 1.0 demonstrates a practical Edge AI waste classification and sorting system using YOLO, TensorRT, NVIDIA Jetson Orin Nano, CSI camera input, and servo-based actuation.

The reported prototype results are **93.3% overall software accuracy** and an average hardware sorting time of **1.80 seconds per item** across all 10 waste classes.

These results show that the system is capable of connecting computer vision inference with real physical sorting behavior in an embedded edge AI environment.
