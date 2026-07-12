"""Load a parking-lot image, detect vacant/occupied spots, route, and draw the path."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.pathfinding.graph_maker import (
    dijkstra,
    node_coordinates,
    parking_lot_graph,
)

# -- Part 1: Predict parking spots -- #

predict_folder = ROOT / "runs/detect/predict"
model_weights = ROOT / "runs/detect/train-10/weights/best.pt"
test_image = ROOT / "moc_parking_lot_datatset/test/images/20260622_123826.jpg"

if not predict_folder.is_dir():
    model = YOLO(model_weights)
    model.predict(test_image, save=True, save_txt=True)


def get_box_centers(yolo_file_path, image_width, image_height):
    centers: list[dict] = []

    with open(yolo_file_path, "r") as file:
        for line in file.readlines():
            data = line.strip().split()
            if not data:
                continue

            class_id = int(data[0])
            x_center_norm = float(data[1])
            y_center_norm = float(data[2])

            pixel_x_center = int(x_center_norm * image_width)
            pixel_y_center = int(y_center_norm * image_height)

            centers.append(
                {
                    "class_id": class_id,
                    "center": (pixel_x_center, pixel_y_center),
                }
            )

    return centers


# -- Part 2: Convert world coords to pixel coords -- #

img = cv2.imread(str(predict_folder / "20260622_123826.jpg"))
img_height, img_width = img.shape[:2]

file_path = predict_folder / "labels/20260622_123826.txt"
detected_centers = get_box_centers(file_path, img_width, img_height)

real_img_width = 33.5
real_img_height = 18.4

SCALE_X: float = img_width / real_img_width
SCALE_Y: float = img_height / real_img_height

X_PAD: int = 3
Y_PAD: int = 1.5


def node_to_px(node_dict, node_name):
    x_cm, y_cm = node_dict[node_name]
    return (
        int((x_cm + X_PAD) * SCALE_X),
        int((y_cm + real_img_height - Y_PAD) * SCALE_Y),
    )


node_coordinates_px: dict[str, tuple[int, int]] = {}

for key in node_coordinates:
    node_coordinates_px[key] = node_to_px(node_coordinates, key)

print("\nnode_coordinates:", node_coordinates)
print("\nnode_coordinates_px:", node_coordinates_px)


# -- Part 3: Match vacant detections to graph nodes -- #

vacant_nodes: list[str] = []
accuracy: int = 50

for obj in detected_centers:
    if obj["class_id"] == 0:
        for node, coord in node_coordinates_px.items():
            if (
                abs(coord[0] - obj["center"][0]) <= accuracy
                and abs(coord[1] - obj["center"][1]) <= accuracy
            ):
                vacant_nodes.append(node)

print("\nvacant_nodes:", vacant_nodes)


# -- Part 4: Run pathfinding -- #

vacant_spot_set: set[str] = set(vacant_nodes)

best_path, total_meters, chosen_spot = dijkstra(
    parking_lot_graph, "TR", vacant_spot_set
)

print(f"\nNavigation Path: {' -> '.join(best_path)}")
print(f"Total Distance: {total_meters:.2f} centimeters")
print(f"Chosen Spot: {chosen_spot}")


# -- Part 5: Draw nodes and edges on the image -- #

for i in range(len(best_path) - 1):
    node1 = node_coordinates_px[best_path[i]]
    node2 = node_coordinates_px[best_path[i + 1]]
    cv2.line(img, node1, node2, (0, 0, 0), 40)

for i, node in enumerate(best_path):
    point = node_coordinates_px[node]
    if i == 0:
        cv2.circle(img, (point[0], point[1]), 48, (0, 255, 0), -1)
    elif i == len(best_path) - 1:
        cv2.circle(img, (point[0], point[1]), 48, (0, 0, 255), -1)
    else:
        cv2.circle(img, (point[0], point[1]), 48, (0, 255, 255), -1)
    cv2.putText(
        img,
        node,
        (point[0] + 64, point[1] + 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        5,
        (255, 255, 255),
        20,
    )

output = predict_folder / "path_overlay.png"
cv2.imwrite(str(output), img)
cv2.waitKey(0)
cv2.destroyAllWindows()
