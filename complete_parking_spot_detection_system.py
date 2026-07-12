"""This script loads the stitched image and detect the vacant and occupied parking spots"""

# -- Part 1: Predict Parking Spots -- #

from pathlib import Path
current_dir = Path(__file__).resolve().parent

from ultralytics import YOLO

predict_folder = current_dir / "runs/detect/predict"

if not predict_folder.is_dir():
    # Load trained model
    model = YOLO(current_dir / "runs/detect/train-10/weights/best.pt")

    # Run inference with the YOLO11n model on stitched image of parking lot
    results = model.predict(current_dir / "moc_parking_lot_datatset/test/images/20260622_123826.jpg", save=True, save_txt=True)

# -- Part 2: Find centre of all parking spots -- #

from rectify_and_stitch import*


def get_box_centers(yolo_file_path, image_width, image_height):
    centers: list[dict] = []

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
            pixel_y_center = int(y_center_norm * image_height)

            # Store the result (keeping track of the class can be helpful)
            centers.append({
                "class_id": class_id,
                "center": (pixel_x_center, pixel_y_center)
            })

    return centers

# -- Part 3: Convert World Coords to Pixel Coords -- #

import cv2

img = cv2.imread(str(predict_folder / "20260622_123826.jpg"))
img_height, img_width = img.shape[:2]
# print(img_width, img_height)

file_path = current_dir / predict_folder / "labels/20260622_123826.txt"
detected_centers = get_box_centers(file_path, img_width, img_height)

# Print all detected centers and their class status
# for obj in detected_centers:
#     print(f"Object Class {obj['class_id']} Center Pixel Coordinate: {obj['center']}")

from graph_maker import*

real_img_width = 33.5
real_img_height = 18.4

SCALE_X: float = img_width / real_img_width
SCALE_Y: float = img_height / real_img_height

X_PAD: int = 3
Y_PAD: int = 1.5

def node_to_px(node_dict, node_name):
    x_cm, y_cm = node_dict[node_name]
    return (int((x_cm + X_PAD) * SCALE_X), int((y_cm + real_img_height - Y_PAD) * SCALE_Y))

# Convert node_coordinates dict to pixel values and save them to node_coordinates_px
node_coordinates_px: dict[list[tuple]] = {}

for key in node_coordinates:
    if key in node_coordinates_px:
        node_coordinates_px[key].append(node_to_px(node_coordinates, key))
    else:
        node_coordinates_px[key] = node_to_px(node_coordinates, key)

print("\nnode_coordinates:", node_coordinates)
print("\nnode_coordinates_px:", node_coordinates_px)


# -- Part 4: Based on accuracy, get the vacant nodes from node_coordinates -- #
vacant_nodes: list[str] = []
accuracy: int = 50

for obj in detected_centers:
    if obj['class_id'] == 0:
        for node, coord in node_coordinates_px.items():
            if abs(coord[0] - obj['center'][0]) <= accuracy and abs(coord[1] - obj['center'][1]) <= accuracy:
                vacant_nodes.append(node)

print("\nvacant_nodes:", vacant_nodes)


# -- Part 5: Run path finding algorithm -- #

vacant_spot_set: set[str] = set(vacant_nodes)

best_path, total_meters, chosen_spot = dijkstra(parking_lot_graph, 'TR', vacant_spot_set)

print(f"\nNavigation Path: {' -> '.join(best_path)}")
print(f"Total Distance: {total_meters:.2f} centimeters")
print(f"Chosen Spot: {chosen_spot}")

# -- Part 6: Draw nodes and edges on the image -- #

for i in range(len(best_path) - 1):
    node1 = node_coordinates_px[best_path[i]]
    node2 = node_coordinates_px[best_path[i + 1]]
    cv2.line(img, node1, node2, (0, 0, 0), 40) # Color = (Blue, Green, Red) or BGR

for i, node in enumerate(best_path):
    point = node_coordinates_px[node]
    if i == 0:
        cv2.circle(img, (point[0], point[1]), 48, (0, 255, 0), -1)
    elif i == len(best_path) - 1:
        cv2.circle(img, (point[0], point[1]), 48, (0, 0, 255), -1)
    else:
        cv2.circle(img, (point[0], point[1]), 48, (0, 255, 255), -1)
    cv2.putText(img, node, (point[0] + 64, point[1] + 50), cv2.FONT_HERSHEY_SIMPLEX, 5, (255,255,255), 20)

output = str(predict_folder / "path_overlay.png")
cv2.imwrite(output, img)
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
