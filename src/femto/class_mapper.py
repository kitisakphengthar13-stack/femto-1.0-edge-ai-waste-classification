class ClassMapper:
    """
    Maps YOLO class names to high-level waste categories.

    Example:
        plastic_bottle -> Recycle Waste
        battery -> Hazardous Waste
        shutdown_card -> shutdown special class
    """

    def __init__(self, mapping_config: dict):
        self.waste_classes = mapping_config["waste_classes"]
        self.special_classes = mapping_config.get("special_classes", {})

    def get_waste_type(self, class_name: str) -> str | None:
        return self.waste_classes.get(class_name)

    def is_shutdown_class(self, class_name: str) -> bool:
        return class_name in self.special_classes

    def get_special_action(self, class_name: str) -> str | None:
        return self.special_classes.get(class_name)