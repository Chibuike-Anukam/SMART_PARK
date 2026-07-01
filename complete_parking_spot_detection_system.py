## This script loads the stitched image and detect the vacant and occupied parking spots
## 
'''
##### PART 1: Predict Parking Spots
# import YOLO
from ultralytics import YOLO

# Load trained model
model = YOLO("C:/Projects/SMART_PARK/runs/detect/train-10/weights/best.pt")

# Run inference with the YOLO11n model on stitched image of parking lot
results = model.predict("C:/Projects/SMART_PARK/moc_parking_lot_datatset/test/images/20260622_123826.jpg", save=True, save_txt=True)

'''
##### Part 2: Find centre of vacant spots
from rectify_and_stitch import*

def get_box_centers(yolo_file_path, image_width, image_height):
    centers = []
    
    # 1. Open and read the text file line by line
    with open(yolo_file_path, 'r') as file:
        lines = file.readlines()
        
        for line in lines:
            # Clean up whitespace and split into a list of strings
            data = line.strip().split()
            
            # Skip empty lines if any exist
            if not data:
                continue
                
            # 2. Extract and parse the values (YOLO uses floats for coordinates)
            class_id = int(data[0])
            x_center_norm = float(data[1])
            y_center_norm = float(data[2])
            box_width_norm = float(data[3])
            box_height_norm = float(data[4])
            
            # 3. Denormalize to get the exact pixel locations
            pixel_x_center = int(x_center_norm * image_width)
            pixel_y_center = OUTPUT_H - int(y_center_norm * image_height)
            
            # Store the result (keeping track of the class can be helpful)
            centers.append({
                "class_id": class_id,
                "center": (pixel_x_center, pixel_y_center)
            })
            
    return centers

# set image size to size of stitched image
IMG_W = OUTPUT_W
IMG_H = OUTPUT_H
file_path = 'C:/Projects/SMART_PARK/runs/detect/predict-3/labels/20260622_123826.txt'

detected_centers = get_box_centers(file_path, IMG_W, IMG_H)

for obj in detected_centers:
    print(f"Object Class {obj['class_id']} Center Pixel Coordinate: {obj['center']}")

#### Part 3: Convert the Location of the Nodes to Pixel Values
from graph_maker import*
import math

SCALE = 10
X_PAD = 30
Y_PAD = 15

def node_to_px(node_dict, node_name):
    x_cm, y_cm = node_dict[node_name]
    return (int(x_cm * SCALE + X_PAD), int(y_cm * SCALE + Y_PAD))


#adj_list = {"a" : [1, 2, 3, 4, 5], "b" : [0, 0, 0]}
#px_list = {}

# Converting node_coordinates dict to pixel values and saving them to a new dict (node_coordinates_px)
node_coordinates_px = {}

for key in node_coordinates:
    if key in node_coordinates_px:
        node_coordinates_px[key].append(node_to_px(node_coordinates, key))
    else:
        node_coordinates_px[key] = [node_to_px(node_coordinates, key)]

print(node_coordinates)
print()
print(node_coordinates_px)
