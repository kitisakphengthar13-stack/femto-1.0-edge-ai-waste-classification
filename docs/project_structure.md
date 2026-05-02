# Project Structure

Femto 1.0 follows a compact Python computer vision / edge AI repository layout.

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

## Directory Roles

| Path | Role |
|---|---|
| `configs/` | Runtime YAML files and example config template. |
| `docs/` | Architecture, deployment, configuration, development, and result documentation. |
| `docs/images/` | Existing result and system evidence images. |
| `models/` | Model placement documentation. Actual model files are intentionally ignored. |
| `scripts/` | Production runtime entry points. |
| `src/femto/` | Runtime Python package code. |
| `tests/` | Hardware-free tests for pure logic and validation helpers. |
| `tools/` | Development and operational utilities that are run manually. |

## Runtime Entry Point

The hardware runtime still starts from:

```bash
python scripts/run_system.py
```

The current standardization pass does not change that command or the runtime behavior behind it.
