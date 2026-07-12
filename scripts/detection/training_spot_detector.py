"""Train a YOLO spot detector on the mock parking-lot dataset."""

from __future__ import annotations

import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATASET_CONFIG = ROOT / "moc_parking_lot_datatset/dataset_config.yaml"
BASE_MODEL = ROOT / "yolo11n.pt"

if __name__ == "__main__":
    model = YOLO(BASE_MODEL)

    # Uncomment to train on GPU (device=0) or CPU (device="cpu"):
    # model.train(
    #     data=str(DATASET_CONFIG),
    #     epochs=100,
    #     imgsz=640,
    #     device=0,
    #     workers=0,
    # )

    # Example single-image inference (replace with a real image path):
    # results = model.predict(ROOT / "moc_parking_lot_datatset/test/images/20260622_123826.jpg")
