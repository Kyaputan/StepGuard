from ultralytics import YOLO

model = YOLO("../model/guard.pt")  # load a custom trained model
model.export(format="onnx" , half=True)