import yaml

from femto.class_mapper import ClassMapper
from femto.config import load_class_mapping


def test_class_mapper_maps_waste_and_special_classes_from_yaml(tmp_path):
    mapping_path = tmp_path / "class_mapping.yaml"
    mapping_path.write_text(
        yaml.safe_dump(
            {
                "waste_classes": {
                    "plastic_bottle": "Recycle Waste",
                    "battery": "Hazardous Waste",
                },
                "special_classes": {
                    "shutdown_card": "shutdown",
                },
            }
        ),
        encoding="utf-8",
    )

    mapper = ClassMapper(load_class_mapping(mapping_path))

    assert mapper.get_waste_type("plastic_bottle") == "Recycle Waste"
    assert mapper.get_waste_type("battery") == "Hazardous Waste"
    assert mapper.get_waste_type("unknown") is None
    assert mapper.is_shutdown_class("shutdown_card") is True
    assert mapper.is_shutdown_class("plastic_bottle") is False
    assert mapper.get_special_action("shutdown_card") == "shutdown"


def test_class_mapper_defaults_missing_special_classes(tmp_path):
    mapping_path = tmp_path / "class_mapping.yaml"
    mapping_path.write_text(
        yaml.safe_dump({"waste_classes": {"can": "Recycle Waste"}}),
        encoding="utf-8",
    )

    mapper = ClassMapper(load_class_mapping(mapping_path))

    assert mapper.get_waste_type("can") == "Recycle Waste"
    assert mapper.is_shutdown_class("shutdown_card") is False
    assert mapper.get_special_action("shutdown_card") is None
