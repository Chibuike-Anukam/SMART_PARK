## This script loads the stitched image and detect the vacant and occupied parking spots ##
from pathlib import Path
current_dir = Path(__file__).resolve().parent

"""
##### PART 1: Predict Parking Spots
# import YOLO
from ultralytics import YOLO


# Load trained model
model = YOLO(current_dir / "runs/detect/train-10/weights/best.pt")

# Run inference with the YOLO11n model on stitched image of parking lot
results = model.predict(current_dir / "moc_parking_lot_datatset/test/images/20260622_123826.jpg", save=True, save_txt=True)"""

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

# file_path = 'C:/Projects/SMART_PARK/runs/detect/predict-3/labels/20260622_123826.txt'
file_path = current_dir / "runs/detect/predict-3/labels/20260622_123826.txt"

detected_centers = get_box_centers(file_path, IMG_W, IMG_H)

# Note: Print all detected centers and their class status
# for obj in detected_centers:
#     print(f"Object Class {obj['class_id']} Center Pixel Coordinate: {obj['center']}")

#### Part 3: Convert the Location of the Nodes to Pixel Values
from graph_maker import*
import math

SCALE = 10
X_PAD = 30
Y_PAD = 15

def node_to_px(node_dict, node_name):
    x_cm, y_cm = node_dict[node_name]
    return (int(x_cm * SCALE + X_PAD), int(y_cm * SCALE + Y_PAD))


# adj_list = {"a" : [1, 2, 3, 4, 5], "b" : [0, 0, 0]}
# px_list = {}

# Converting node_coordinates dict to pixel values and saving them to a new dict (node_coordinates_px)
node_coordinates_px = {}

for key in node_coordinates:
    if key in node_coordinates_px:
        node_coordinates_px[key].append(node_to_px(node_coordinates, key))
    else:
        node_coordinates_px[key] = [node_to_px(node_coordinates, key)]

print()
print("node_coordinates:", node_coordinates)
print()
print("node_coordinates_px:", node_coordinates_px)


#### Part 4: Find the node in the node coordinate dict corresponding to the one from the image
cor_nodes = []
accuracy = 5

for obj in detected_centers: # detected_centers is a list of dicts, so obj is a dict!
    if obj['class_id'] == 0:
        for node, coord in node_coordinates_px.items():
            if abs(coord[0][0] - obj['center'][0]) <= accuracy and abs(coord[0][1] - obj['center'][1]) <= accuracy:
                cor_nodes.append(node)

print()
print("cor_nodes:", cor_nodes)


#### Part 5: Run path finding algorithm

# --- SIMULATION ---
# A vacant spot detection algorithm flags these spots as open
# vacant_spot_set = {'P1', 'P4', 'P9', 'P12'}
vacant_spot_set = set(cor_nodes)

best_path, total_meters, chosen_spot = dijkstra(parking_lot_graph, 'BL', vacant_spot_set)

print()
print(f"Navigation Path: {' -> '.join(best_path)}")
print(f"Total Distance: {total_meters:.2f} centimeters")
print(f"Chosen Spot: {chosen_spot}")

#### Part 6: Draw nodes and edges on the image
import cv2

# img = cv2.imread('stitched_topdown.png')
img = cv2.imread('runs/detect/predict/20260622_123826.jpg')

node_coordinates_2 = {}
for node, val in node_coordinates.items():
    temp = []
    temp.append((int(val[0]), int(val[1])))
    node_coordinates_2[node] = temp

for i in range(len(cor_nodes) - 1):
    node1 = node_coordinates_px[cor_nodes[i]][0]
    node2 = node_coordinates_px[cor_nodes[i + 1]][0]
    cv2.line(img, node1, node2, (0, 0, 255), 5) # Color = (Blue, Green, Red) or BGR

for node in cor_nodes:
    point = node_coordinates_px[cor_nodes[i]][0]
    cv2.circle(img, point, 8, (255, 255, 255), -1)
    cv2.putText(img, node, (point[0] + 10, point[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 5)

cv2.imwrite('path_overlay.png', img)
cv2.waitKey(0)
cv2.destroyAllWindows()


'''
#######CLAUDE'S RESPONSE:


import cv2

img = cv2.imread('stitched_topdown.png')

def node_to_px(node_name):
    x_cm, y_cm = nodes[node_name]
    return (int(x_cm * SCALE + PAD), int(y_cm * SCALE + PAD))

# Draw all edges in grey
for n1, n2 in edges:
    cv2.line(img, node_to_px(n1), node_to_px(n2), (100, 100, 100), 1)

# Draw shortest path in green
for i in range(len(path) - 1):
    cv2.line(img, node_to_px(path[i]), node_to_px(path[i+1]),
             (0, 255, 0), 3)

# Draw all nodes as circles
for name, _ in nodes.items():
    px = node_to_px(name)
    cv2.circle(img, px, 8, (255, 255, 255), -1)
    cv2.putText(img, name, (px[0]+10, px[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

# Draw start and end in distinct colors
cv2.circle(img, node_to_px(path[0]),  10, (0, 255, 0), -1)   # green = start
cv2.circle(img, node_to_px(path[-1]), 10, (0, 0, 255), -1)   # red = end

cv2.imwrite('path_overlay.png', img)
cv2.imshow('Dijkstra Path', cv2.resize(img, (900, 600)))
cv2.waitKey(0)
cv2.destroyAllWindows()
'''
