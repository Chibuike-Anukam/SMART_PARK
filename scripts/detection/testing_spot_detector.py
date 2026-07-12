"""Run YOLO inference on a test parking-lot image."""

from __future__ import annotations

import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODEL = ROOT / "runs/detect/train-10/weights/best.pt"
TEST_IMAGE = ROOT / "moc_parking_lot_datatset/test/images/20260622_123826.jpg"

model = YOLO(MODEL)
model.predict(TEST_IMAGE, save=True, save_txt=True)
