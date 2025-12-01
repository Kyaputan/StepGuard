from ultralytics import YOLO

model = YOLO("../model/food_bag.pt")  # load a custom trained model
model.export(format="onnx" , half=True)