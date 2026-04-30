# Models

This directory is reserved for model-related documentation for **Femto 1.0 — Edge AI Waste Classification System**.

Actual model files are not included in this repository due to file size limitations and deployment-specific environment differences.

---

## Model Format Overview

During development and training, the YOLO model is usually used in `.pt` format.

For deployment on NVIDIA Jetson Orin Nano, this project uses a TensorRT `.engine` model instead of running the `.pt` model directly.

| Format | Main Use | Description |
|---|---|---|
| `.pt` | Training and development | PyTorch model format used for training, testing, and model export |
| `.engine` | Jetson deployment | TensorRT engine format used for optimized inference deployment on NVIDIA Jetson hardware |

---

## Why `.pt` Is Not Used for Deployment

The `.pt` model format is useful during development because it is flexible and easy to train, evaluate, modify, and export.

However, running a `.pt` model directly on Jetson is not ideal for deployment because:

- It depends on the PyTorch runtime
- It has more runtime overhead than a deployment-optimized runtime
- It is less optimized for NVIDIA Jetson inference deployment
- It is better suited for development and experimentation than final edge deployment

For this reason, the `.pt` model is used mainly during the training and export stage, not as the final deployment model.

---

## Why TensorRT `.engine` Is Used

TensorRT `.engine` format is used because it is a deployment-oriented model format for NVIDIA GPU inference.

On NVIDIA Jetson Orin Nano, TensorRT is suitable for running optimized inference workloads on the target hardware.

Using a TensorRT engine helps with:

- Optimized inference deployment
- Reduced runtime overhead compared with development-oriented execution
- FP16 inference support
- Better suitability for NVIDIA Jetson edge hardware
- Cleaner separation between training format and deployment format

In this project, the trained YOLO model is exported to TensorRT `.engine` format before deployment.

---

## Expected Deployment Model

For Jetson deployment, the system expects a TensorRT engine model file.

Example placeholder path:

```text
path/to/best.engine
```

This path must be replaced with the actual TensorRT engine model path used on the Jetson device.

The actual model file is not included in this repository.

---

## Why Model Files Are Not Included

The actual model files are not uploaded to this repository because:

- TensorRT `.engine` files can be large
- TensorRT engine files are usually environment-specific
- Engine files may depend on the Jetson device, JetPack version, TensorRT version, CUDA version, and hardware configuration
- The repository is intended to document the project structure, source code, configuration examples, and deployment workflow

Because of this, users should generate or place their own model file before running the system.

---

## Model Path Configuration

The model path is configured in:

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

Replace `path/to/best.engine` with the actual model path used on the Jetson device.

For example:

```yaml
model:
  path: "/home/jetson/FEMTO_1.0/models/best.engine"
  task: "detect"
  confidence_threshold: 0.50
```

The runtime loads this path through:

```text
scripts/run_system.py
src/femto/config.py
src/femto/app.py
```

The model path is no longer intended to be hardcoded directly inside the main runtime script.

---

## Model Training Reference

The YOLO `.pt` model can be trained during the development stage using:

```text
tools/model_training.py
```

This script is used to train the waste detection model before exporting it to TensorRT `.engine` format for Jetson deployment.

Example training logic:

```python
from multiprocessing import freeze_support
from ultralytics import YOLO

if __name__ == "__main__":
    freeze_support()

    # -------------------------
    # Base model
    # -------------------------
    model = YOLO("path/to/yolo26s.pt")

    # -------------------------
    # Training parameters
    # -------------------------
    data_yaml = "path/to/data.yaml"
    epochs = 250
    imgsz = 640
    batch_size = 9
    workers = 2
    project = "model_result"
    name = "model_name"

    model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        workers=workers,
        optimizer="auto",

        # Use default augmentation to improve model generalization
        augment=True,

        project=project,
        name=name,
        exist_ok=True,
    )
```

The main configurable training parameters are:

| Parameter | Description |
|---|---|
| `model` | Base YOLO model used for training |
| `data_yaml` | Dataset configuration file for YOLO training |
| `epochs` | Number of training epochs |
| `imgsz` | Input image size used during training |
| `batch_size` | Training batch size |
| `workers` | Number of data loading workers |
| `project` | Output directory for training results |
| `name` | Name of the training run |
| `augment` | Enables YOLO training augmentation |

After training, the best model checkpoint is typically saved under the training output directory. The resulting `.pt` model can then be exported to TensorRT `.engine` format using:

```text
tools/model_export.py
```

---

## TensorRT Export Reference

The TensorRT engine can be generated from a trained YOLO `.pt` model using the export tool:

```text
tools/model_export.py
```

Example export workflow:

```text
Trained YOLO .pt model
    ↓
TensorRT export
    ↓
TensorRT .engine model
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

After export, update `configs/system_config.yaml` with the actual `.engine` file path used on the Jetson device.

When possible, export or rebuild the TensorRT engine on the target Jetson device to reduce compatibility problems between TensorRT, CUDA, JetPack, and the hardware environment.

---

## Recommended Local Model Placement

A simple local deployment layout is:

```text
FEMTO_1.0/
├── models/
│   ├── best.engine
│   └── README.md
```

Then configure:

```yaml
model:
  path: "models/best.engine"
  task: "detect"
  confidence_threshold: 0.50
```

For automatic startup or deployment outside the repository root, absolute paths may be safer:

```yaml
model:
  path: "/home/jetson/FEMTO_1.0/models/best.engine"
  task: "detect"
  confidence_threshold: 0.50
```

---

## Notes

This directory intentionally does not contain actual model files.

Expected deployment model type:

```text
TensorRT .engine
```

The `.pt` model is mainly used for training and export, while the `.engine` model is used for Jetson deployment.

Actual model files should be generated or copied locally on the target Jetson device before running the system.

Before running the system, confirm that:

```text
[ ] The TensorRT .engine file exists
[ ] The path in configs/system_config.yaml points to the correct .engine file
[ ] The engine was exported for a compatible Jetson / TensorRT / CUDA / JetPack environment
[ ] The YOLO class names match configs/class_mapping.yaml
```