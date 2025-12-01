import os
from ultralytics import YOLO
from config import WEIGHTS_DIR, MODEL_NAME, MODEL_CONF

def load_model():
    model_path = os.path.join(WEIGHTS_DIR, MODEL_NAME)
    model = YOLO(model_path , task="detect")
    return model

def infer(model, frame):
    return model(frame, conf=MODEL_CONF)[0]

def parse_results(results, margin: int = 10):
    parsed = []
    names = results.names
    h, w = results.orig_shape
    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls_id = int(box.cls[0])
        cls_name = names[cls_id]
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(w - 1, x2 + margin)
        y2 = min(h - 1, y2 + margin)
        parsed.append({"bbox": (x1, y1, x2, y2),"class": cls_name})
    return parsed

def debug_detection():
    print("[INFO] Detection")
    model = load_model()
    print(model.names)

if __name__ == "__main__":
    debug_detection()
