import yaml

from tools.preflight_check import has_failures, run_preflight


def write_yaml(path, data):
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def make_valid_files(tmp_path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()

    for name in (
        "best.engine",
        "shutdown_alert.mp3",
        "start_alert.mp3",
        "recycle.mp3",
        "general.mp3",
    ):
        (assets_dir / name).write_text("placeholder test asset", encoding="utf-8")

    system_config = {
        "model": {
            "path": "assets/best.engine",
            "task": "detect",
            "confidence_threshold": 0.5,
        },
        "decision": {
            "buffer_size": 10,
            "result_delay_seconds": 2.0,
            "allow_multiple_objects": False,
        },
        "shutdown": {
            "class_name": "shutdown_card",
            "confidence_threshold": 0.7,
            "buffer_size": 40,
            "delay_seconds": 10.0,
            "sound_path": "assets/shutdown_alert.mp3",
        },
        "motion": {
            "enabled": True,
            "pixel_threshold": 1500,
            "yolo_awake_duration_seconds": 2.5,
            "frame_diff_threshold": 25,
            "blur_kernel_size": 21,
        },
        "camera": {
            "sensor_id": 0,
            "width": 1280,
            "height": 720,
            "flip_method": 0,
        },
        "audio": {
            "startup_alert": "assets/start_alert.mp3",
            "category_sounds": {
                "Recycle Waste": "assets/recycle.mp3",
                "General Waste": "assets/general.mp3",
            },
        },
        "servo": {
            "rotate_pin": 32,
            "tilt_pin": 33,
            "pwm_frequency": 50,
            "start_position": {
                "rotate_duty": 7.5,
                "tilt_duty": 4.12,
            },
            "category_positions": {
                "Recycle Waste": {
                    "rotate_duty": 5.0,
                    "tilt_duty": 7.5,
                },
                "General Waste": {
                    "rotate_duty": 10.5,
                    "tilt_duty": 1.78,
                },
            },
            "timing": {
                "rotate_step_seconds": 0.3,
                "tilt_return_seconds": 1.3,
                "rotate_return_seconds": 1.7,
                "cycle_done_seconds": 2.0,
                "startup_delay_seconds": 0.5,
                "release_rotate_pwm": True,
            },
        },
        "runtime": {
            "loop_sleep_seconds": 0.005,
            "camera_drop_sleep_seconds": 0.05,
        },
    }
    mapping_config = {
        "waste_classes": {
            "plastic_bottle": "Recycle Waste",
            "plastic_bag": "General Waste",
        },
        "special_classes": {
            "shutdown_card": "shutdown",
        },
    }

    system_path = tmp_path / "system_config.yaml"
    mapping_path = tmp_path / "class_mapping.yaml"
    write_yaml(system_path, system_config)
    write_yaml(mapping_path, mapping_config)
    return system_path, mapping_path, system_config, mapping_config


def test_preflight_passes_for_complete_temp_config(tmp_path):
    system_path, mapping_path, _, _ = make_valid_files(tmp_path)

    messages = run_preflight(system_path, mapping_path, tmp_path)

    assert not has_failures(messages)


def test_preflight_fails_for_placeholder_model_path(tmp_path):
    system_path, mapping_path, system_config, _ = make_valid_files(tmp_path)
    system_config["model"]["path"] = "path/to/best.engine"
    write_yaml(system_path, system_config)

    messages = run_preflight(system_path, mapping_path, tmp_path)

    assert has_failures(messages)
    assert any("placeholder" in message.message for message in messages)


def test_preflight_fails_for_missing_nested_key(tmp_path):
    system_path, mapping_path, system_config, _ = make_valid_files(tmp_path)
    del system_config["servo"]["timing"]["cycle_done_seconds"]
    write_yaml(system_path, system_config)

    messages = run_preflight(system_path, mapping_path, tmp_path)

    assert has_failures(messages)
    assert any("servo.timing.cycle_done_seconds" in message.message for message in messages)


def test_preflight_fails_for_category_without_servo_position(tmp_path):
    system_path, mapping_path, _, mapping_config = make_valid_files(tmp_path)
    mapping_config["waste_classes"]["battery"] = "Hazardous Waste"
    write_yaml(mapping_path, mapping_config)

    messages = run_preflight(system_path, mapping_path, tmp_path)

    assert has_failures(messages)
    assert any("Mapped category missing servo position: Hazardous Waste" == message.message for message in messages)
