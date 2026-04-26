from multiprocessing import freeze_support
from ultralytics import YOLO

if __name__ == "__main__":
    freeze_support()

    # -------------------------
    # base model
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
    name = "model__name"

    model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch_size,
            workers=workers,
            optimizer= "auto",

    # ---- Use augmentation default to make strong pattern model ----
            augment=True,

            project=project,
            name=name,
            exist_ok=True
        )