from ultralytics import YOLO

model = YOLO("path/to/best.pt", task = "detect")

model.export(
    format = "engine",
    half = True,
    device = 0,
    batch = 1,
)