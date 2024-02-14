from ultralytics import YOLO

model = YOLO("Models\yolov8m-seg.pt")

results = model.predict(source=0, show=True)