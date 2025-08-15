import os
from ultralytics import YOLO
from config import WEIGHTS_DIR, MODEL_NAME, MODEL_CONF

def load_model():
    model_path = os.path.join(WEIGHTS_DIR, MODEL_NAME)
    model = YOLO(model_path)
    return model

def infer(model, frame):
    return model(frame, conf=MODEL_CONF)[0]

def parse_results(results):
    parsed = []
    names = results.names  # class index -> name
    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls_id = int(box.cls[0])
        cls_name = names[cls_id]
        parsed.append({"bbox": (x1, y1, x2, y2), "class": cls_name})
    return parsed