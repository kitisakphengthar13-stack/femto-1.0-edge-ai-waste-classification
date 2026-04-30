from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML file: {path}")

    return data


def load_system_config(path: str | Path) -> dict[str, Any]:
    config = load_yaml(path)

    required_sections = [
        "model",
        "decision",
        "shutdown",
        "motion",
        "camera",
        "audio",
        "servo",
        "runtime",
    ]

    for section in required_sections:
        if section not in config:
            raise KeyError(f"Missing required config section: {section}")

    return config


def load_class_mapping(path: str | Path) -> dict[str, Any]:
    config = load_yaml(path)

    if "waste_classes" not in config:
        raise KeyError("Missing required config section: waste_classes")

    config.setdefault("special_classes", {})
    return config