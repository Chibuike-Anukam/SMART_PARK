from ultralytics import YOLO

# Load trained model
model = YOLO("C:/Projects/SMART_PARK/runs/detect/train-10/weights/best.pt")

# Run inference with the YOLO11n model on an image from the test set
results = model("C:/Projects/SMART_PARK/moc_parking_lot_datatset/test/images/20260622_123826.jpg", save=True)