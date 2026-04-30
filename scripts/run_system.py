from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from femto.app import FemtoApp
from femto.config import load_class_mapping, load_system_config


def main():
    system_config = load_system_config(PROJECT_ROOT / "configs" / "system_config.yaml")
    class_mapping = load_class_mapping(PROJECT_ROOT / "configs" / "class_mapping.yaml")

    app = FemtoApp(system_config, class_mapping)
    app.run()


if __name__ == "__main__":
    main()