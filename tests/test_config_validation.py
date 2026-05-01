import pytest
import yaml

from femto.config import load_class_mapping, load_system_config


def test_example_system_config_matches_loader_expectations():
    config = load_system_config("configs/system_config.example.yaml")

    assert "model" in config
    assert "servo" in config
    assert "runtime" in config


def test_load_system_config_rejects_missing_top_level_section(tmp_path):
    config_path = tmp_path / "system_config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "model": {},
                "decision": {},
                "shutdown": {},
                "motion": {},
                "camera": {},
                "audio": {},
                "servo": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(KeyError, match="runtime"):
        load_system_config(config_path)


def test_load_class_mapping_requires_waste_classes(tmp_path):
    mapping_path = tmp_path / "class_mapping.yaml"
    mapping_path.write_text(yaml.safe_dump({"special_classes": {}}), encoding="utf-8")

    with pytest.raises(KeyError, match="waste_classes"):
        load_class_mapping(mapping_path)
