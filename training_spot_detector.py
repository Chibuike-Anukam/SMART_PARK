from ultralytics import YOLO

if __name__ == '__main__':

    # Load a COCO-pretrained YOLO11n model
    model = YOLO("yolo11n.pt")

    # Train the model on the parking lot dataset for 100 epochs
    #results = model.train(data="C:/Projects/SMART_PARK/moc_parking_lot_datatset/dataset_config.yaml", epochs=100, imgsz=640, device=0, workers=0) # device = GPU

    # Run inference with the YOLO11n model on the 'bus.jpg' image
    results = model("path/to/bus.jpg")