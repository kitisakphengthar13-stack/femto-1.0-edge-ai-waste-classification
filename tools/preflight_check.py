from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYSTEM_CONFIG = PROJECT_ROOT / "configs" / "system_config.yaml"
DEFAULT_CLASS_MAPPING = PROJECT_ROOT / "configs" / "class_mapping.yaml"

REQUIRED_SYSTEM_KEYS = {
    "model": ["path", "confidence_threshold"],
    "decision": ["buffer_size", "result_delay_seconds", "allow_multiple_objects"],
    "shutdown": ["class_name", "confidence_threshold", "buffer_size", "delay_seconds", "sound_path"],
    "motion": [
        "enabled",
        "pixel_threshold",
        "yolo_awake_duration_seconds",
        "frame_diff_threshold",
        "blur_kernel_size",
    ],
    "camera": ["sensor_id", "width", "height", "flip_method"],
    "audio": ["startup_alert", "category_sounds"],
    "servo": ["rotate_pin", "tilt_pin", "pwm_frequency", "start_position", "category_positions", "timing"],
    "runtime": ["loop_sleep_seconds", "camera_drop_sleep_seconds"],
}

REQUIRED_SERVO_START_KEYS = ["rotate_duty", "tilt_duty"]
REQUIRED_SERVO_CATEGORY_KEYS = ["rotate_duty", "tilt_duty"]
REQUIRED_SERVO_TIMING_KEYS = [
    "rotate_step_seconds",
    "tilt_return_seconds",
    "rotate_return_seconds",
    "cycle_done_seconds",
    "startup_delay_seconds",
    "release_rotate_pwm",
]

PLACEHOLDER_MARKERS = (
    "path/to/",
    "/path/to/",
    "your_model",
    "example",
    "placeholder",
    "<",
    ">",
)


@dataclass(frozen=True)
class CheckMessage:
    level: str
    message: str


def load_yaml_file(path: Path) -> tuple[dict[str, Any] | None, list[CheckMessage]]:
    if not path.exists():
        return None, [CheckMessage("FAIL", f"Missing YAML file: {path}")]

    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        return None, [CheckMessage("FAIL", f"Invalid YAML in {path}: {exc}")]
    except OSError as exc:
        return None, [CheckMessage("FAIL", f"Could not read {path}: {exc}")]

    if not isinstance(data, dict):
        return None, [CheckMessage("FAIL", f"YAML root must be a mapping: {path}")]

    return data, [CheckMessage("PASS", f"Loaded YAML: {path}")]


def is_placeholder_path(value: Any) -> bool:
    if not isinstance(value, str):
        return True

    normalized = value.strip().lower().replace("\\", "/")
    if not normalized:
        return True

    return any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def resolve_config_path(path_value: str, base_dir: Path) -> Path:
    candidate = Path(path_value).expanduser()
    if candidate.is_absolute():
        return candidate
    return base_dir / candidate


def validate_required_keys(system_config: dict[str, Any], mapping_config: dict[str, Any]) -> list[CheckMessage]:
    messages: list[CheckMessage] = []

    for section, keys in REQUIRED_SYSTEM_KEYS.items():
        section_value = system_config.get(section)
        if not isinstance(section_value, dict):
            messages.append(CheckMessage("FAIL", f"Missing or invalid system config section: {section}"))
            continue

        messages.append(CheckMessage("PASS", f"Found system config section: {section}"))
        for key in keys:
            if key not in section_value:
                messages.append(CheckMessage("FAIL", f"Missing system config key: {section}.{key}"))

    servo = system_config.get("servo", {})
    if isinstance(servo, dict):
        start_position = servo.get("start_position", {})
        if isinstance(start_position, dict):
            for key in REQUIRED_SERVO_START_KEYS:
                if key not in start_position:
                    messages.append(CheckMessage("FAIL", f"Missing system config key: servo.start_position.{key}"))
        elif "start_position" in servo:
            messages.append(CheckMessage("FAIL", "servo.start_position must be a mapping"))

        category_positions = servo.get("category_positions", {})
        if isinstance(category_positions, dict):
            for category, values in category_positions.items():
                if not isinstance(values, dict):
                    messages.append(CheckMessage("FAIL", f"servo.category_positions.{category} must be a mapping"))
                    continue
                for key in REQUIRED_SERVO_CATEGORY_KEYS:
                    if key not in values:
                        messages.append(CheckMessage("FAIL", f"Missing system config key: servo.category_positions.{category}.{key}"))
        elif "category_positions" in servo:
            messages.append(CheckMessage("FAIL", "servo.category_positions must be a mapping"))

        timing = servo.get("timing", {})
        if isinstance(timing, dict):
            for key in REQUIRED_SERVO_TIMING_KEYS:
                if key not in timing:
                    messages.append(CheckMessage("FAIL", f"Missing system config key: servo.timing.{key}"))
        elif "timing" in servo:
            messages.append(CheckMessage("FAIL", "servo.timing must be a mapping"))

    waste_classes = mapping_config.get("waste_classes")
    if isinstance(waste_classes, dict) and waste_classes:
        messages.append(CheckMessage("PASS", "Found class mapping section: waste_classes"))
    else:
        messages.append(CheckMessage("FAIL", "Missing or invalid class mapping section: waste_classes"))

    special_classes = mapping_config.get("special_classes", {})
    if not isinstance(special_classes, dict):
        messages.append(CheckMessage("FAIL", "special_classes must be a mapping when provided"))
    else:
        messages.append(CheckMessage("PASS", "Found class mapping section: special_classes"))

    return messages


def validate_paths(system_config: dict[str, Any], base_dir: Path) -> list[CheckMessage]:
    messages: list[CheckMessage] = []

    model_path = system_config.get("model", {}).get("path")
    messages.extend(_validate_existing_path("Model path", model_path, base_dir, fail_on_missing=True))

    shutdown_sound = system_config.get("shutdown", {}).get("sound_path")
    messages.extend(_validate_existing_path("Shutdown sound path", shutdown_sound, base_dir, fail_on_missing=True))

    startup_alert = system_config.get("audio", {}).get("startup_alert")
    messages.extend(_validate_existing_path("Startup audio path", startup_alert, base_dir, fail_on_missing=True))

    category_sounds = system_config.get("audio", {}).get("category_sounds", {})
    if isinstance(category_sounds, dict):
        for category, sound_path in category_sounds.items():
            messages.extend(
                _validate_existing_path(
                    f"Audio path for category '{category}'",
                    sound_path,
                    base_dir,
                    fail_on_missing=True,
                )
            )
    elif "audio" in system_config:
        messages.append(CheckMessage("FAIL", "audio.category_sounds must be a mapping"))

    return messages


def _validate_existing_path(label: str, path_value: Any, base_dir: Path, fail_on_missing: bool) -> list[CheckMessage]:
    messages: list[CheckMessage] = []

    if not isinstance(path_value, str) or not path_value.strip():
        messages.append(CheckMessage("FAIL", f"{label} is empty or not a string"))
        return messages

    if is_placeholder_path(path_value):
        messages.append(CheckMessage("FAIL", f"{label} appears to be a placeholder: {path_value}"))
        return messages

    resolved = resolve_config_path(path_value, base_dir)
    if resolved.exists():
        messages.append(CheckMessage("PASS", f"{label} exists: {resolved}"))
    else:
        level = "FAIL" if fail_on_missing else "WARN"
        messages.append(CheckMessage(level, f"{label} does not exist: {resolved}"))

    return messages


def validate_cross_references(system_config: dict[str, Any], mapping_config: dict[str, Any]) -> list[CheckMessage]:
    messages: list[CheckMessage] = []

    waste_classes = mapping_config.get("waste_classes", {})
    if not isinstance(waste_classes, dict):
        return messages

    mapped_categories = {category for category in waste_classes.values() if isinstance(category, str)}
    servo_categories = set()
    audio_categories = set()

    category_positions = system_config.get("servo", {}).get("category_positions", {})
    if isinstance(category_positions, dict):
        servo_categories = set(category_positions.keys())

    category_sounds = system_config.get("audio", {}).get("category_sounds", {})
    if isinstance(category_sounds, dict):
        audio_categories = set(category_sounds.keys())

    for category in sorted(mapped_categories):
        if category in servo_categories:
            messages.append(CheckMessage("PASS", f"Mapped category has servo position: {category}"))
        else:
            messages.append(CheckMessage("FAIL", f"Mapped category missing servo position: {category}"))

        if category in audio_categories:
            messages.append(CheckMessage("PASS", f"Mapped category has audio entry: {category}"))
        else:
            messages.append(CheckMessage("FAIL", f"Mapped category missing audio entry: {category}"))

    unused_servo_categories = sorted(servo_categories - mapped_categories)
    for category in unused_servo_categories:
        messages.append(CheckMessage("WARN", f"Servo category is not referenced by class mapping: {category}"))

    unused_audio_categories = sorted(audio_categories - mapped_categories)
    for category in unused_audio_categories:
        messages.append(CheckMessage("WARN", f"Audio category is not referenced by class mapping: {category}"))

    shutdown_class = system_config.get("shutdown", {}).get("class_name")
    special_classes = mapping_config.get("special_classes", {})
    if isinstance(shutdown_class, str) and isinstance(special_classes, dict):
        if shutdown_class in special_classes:
            messages.append(CheckMessage("PASS", f"Shutdown class is listed in special_classes: {shutdown_class}"))
        else:
            messages.append(CheckMessage("WARN", f"Shutdown class is not listed in special_classes: {shutdown_class}"))

    return messages


def run_preflight(system_config_path: Path, class_mapping_path: Path, base_dir: Path) -> list[CheckMessage]:
    messages: list[CheckMessage] = []

    system_config, system_messages = load_yaml_file(system_config_path)
    mapping_config, mapping_messages = load_yaml_file(class_mapping_path)
    messages.extend(system_messages)
    messages.extend(mapping_messages)

    if system_config is None or mapping_config is None:
        return messages

    messages.extend(validate_required_keys(system_config, mapping_config))
    messages.extend(validate_paths(system_config, base_dir))
    messages.extend(validate_cross_references(system_config, mapping_config))

    return messages


def has_failures(messages: list[CheckMessage]) -> bool:
    return any(message.level == "FAIL" for message in messages)


def print_messages(messages: list[CheckMessage]) -> None:
    for message in messages:
        print(f"[{message.level}] {message.message}")

    total_fail = sum(1 for message in messages if message.level == "FAIL")
    total_warn = sum(1 for message in messages if message.level == "WARN")
    total_pass = sum(1 for message in messages if message.level == "PASS")
    print(f"\nSummary: {total_pass} PASS, {total_warn} WARN, {total_fail} FAIL")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate FEMTO config files without importing Jetson hardware modules.",
    )
    parser.add_argument(
        "--system-config",
        type=Path,
        default=DEFAULT_SYSTEM_CONFIG,
        help="Path to system_config.yaml.",
    )
    parser.add_argument(
        "--class-mapping",
        type=Path,
        default=DEFAULT_CLASS_MAPPING,
        help="Path to class_mapping.yaml.",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=PROJECT_ROOT,
        help="Base directory used to resolve relative model/audio paths.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    messages = run_preflight(
        args.system_config,
        args.class_mapping,
        args.base_dir,
    )
    print_messages(messages)
    return 1 if has_failures(messages) else 0


if __name__ == "__main__":
    raise SystemExit(main())
