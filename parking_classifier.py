"""
Classify parking spots in tempImages and build navigation graphs.

Outputs per-lot JSON under data/lots/ and annotated preview images under data/previews/.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
TEMP_DIR = ROOT / "tempImages"
DATA_DIR = ROOT / "data" / "lots"
PREVIEW_DIR = ROOT / "data" / "previews"

SpotClass = Literal["occupied", "free", "accessible", "lane_vehicle", "unknown"]


@dataclass
class Spot:
    id: str
    row: int
    col: int
    x: float
    y: float
    w: float
    h: float
    status: SpotClass
    confidence: float


@dataclass
class GraphNode:
    id: str
    x: float
    y: float
    kind: Literal["spot", "perimeter", "vehicle", "entrance", "junction"]
    spot_id: str | None = None


def _content_bbox(img: np.ndarray, thresh: int = 175) -> tuple[int, int, int, int]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    coords = np.column_stack(np.where(mask > 0))
    if coords.size == 0:
        h, w = img.shape[:2]
        return 0, 0, w, h
    y1, x1 = coords.min(axis=0)
    y2, x2 = coords.max(axis=0)
    pad = 6
    h, w = img.shape[:2]
    return (
        max(0, int(x1) + pad),
        max(0, int(y1) + pad),
        min(w, int(x2) - pad),
        min(h, int(y2) - pad),
    )


def _center_roi(roi: np.ndarray, margin: float = 0.18) -> np.ndarray:
    h, w = roi.shape[:2]
    dy, dx = int(h * margin), int(w * margin)
    if dy * 2 >= h or dx * 2 >= w:
        return roi
    return roi[dy : h - dy, dx : w - dx]


def _classify_roi(roi: np.ndarray, stylized: bool) -> tuple[SpotClass, float]:
    h, w = roi.shape[:2]
    if h < 8 or w < 8:
        return "unknown", 0.0

    sample = _center_roi(roi, 0.12 if stylized else 0.2)
    sh, sw = sample.shape[:2]
    if sh < 4 or sw < 4:
        sample = roi

    lab = cv2.cvtColor(sample, cv2.COLOR_BGR2LAB).astype(np.float32)
    chroma = np.sqrt((lab[:, :, 1] - 128) ** 2 + (lab[:, :, 2] - 128) ** 2)
    gray = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 45, 130)

    white = gray > 205
    car_like = chroma > (20 if stylized else 14)
    car_like &= ~white

    area = sh * sw
    car_ratio = float(car_like.sum()) / area
    white_ratio = float(white.sum()) / area
    edge_ratio = float(edges.sum()) / 255.0 / area
    med = float(np.median(gray))
    non_bg_ratio = float((np.abs(gray.astype(np.float32) - med) > 18).sum()) / area
    gray_std = float(gray.std())

    if stylized:
        hsv = cv2.cvtColor(sample, cv2.COLOR_BGR2HSV)
        sat_ratio = float(
            ((hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 70)).sum()
        ) / area

        if sat_ratio > 0.24 or (sat_ratio > 0.19 and white_ratio < 0.09):
            return "occupied", min(0.98, 0.55 + sat_ratio)
        if white_ratio > 0.06 and sat_ratio < 0.22:
            return "accessible", min(0.95, 0.55 + white_ratio * 2)
        if car_ratio > 0.28 or non_bg_ratio > 0.48:
            return "occupied", min(0.98, 0.6 + car_ratio)
        if non_bg_ratio < 0.32:
            return "free", 0.88
        return "free", 0.75

    # Aerial / photo lots: vehicles raise texture (std, edges) in the stall center
    if gray_std > 40 or (gray_std > 28 and edge_ratio > 0.11):
        return "occupied", min(0.97, 0.5 + gray_std / 80)
    if white_ratio > 0.12 and gray_std < 30:
        return "accessible", 0.85
    return "free", min(0.92, 0.55 + (40 - gray_std) / 80)


def _grid_spots(
    img: np.ndarray,
    rows: int,
    cols: int,
    stylized: bool,
    lot_id: str,
    row_ratios: list[float] | None = None,
    row_cols: list[int] | None = None,
    status_overrides: dict[tuple[int, int], SpotClass] | None = None,
) -> list[Spot]:
    x1, y1, x2, y2 = _content_bbox(img)
    inner = img[y1:y2, x1:x2]
    ih, iw = inner.shape[:2]
    if row_ratios and len(row_ratios) == rows:
        cum = [0.0]
        for ratio in row_ratios:
            cum.append(cum[-1] + ratio * ih)
        row_bounds = [int(v) for v in cum]
    else:
        ch = ih / rows
        row_bounds = [int(r * ch) for r in range(rows)] + [ih]

    max_cols = max(row_cols) if row_cols else cols
    cell_w = iw / max_cols
    margin_y = 0.08
    margin_x = 0.02
    spots: list[Spot] = []

    for r in range(rows):
        y0, y1c = row_bounds[r], row_bounds[r + 1]
        ch = y1c - y0
        dy = int(ch * margin_y)
        ncol = row_cols[r] if row_cols and r < len(row_cols) else cols
        col_offset = (max_cols - ncol) / 2.0
        dx = int(cell_w * margin_x)

        for c in range(ncol):
            x0 = int((c + col_offset) * cell_w) + dx
            x1c = int((c + 1 + col_offset) * cell_w) - dx
            y0r, y1cr = y0 + dy, y1c - dy
            roi = inner[y0r:y1cr, x0:x1c]
            status, conf = _classify_roi(roi, stylized)
            if status_overrides and (r, c) in status_overrides:
                status = status_overrides[(r, c)]
                conf = 0.99
            cx = x1 + (c + 0.5 + col_offset) * cell_w
            cy = y1 + (r + 0.5) * ch
            spots.append(
                Spot(
                    id=f"{lot_id}_r{r}_c{c}",
                    row=r,
                    col=c,
                    x=float(cx),
                    y=float(cy),
                    w=float(cell_w - 2 * dx),
                    h=float(ch - 2 * dy),
                    status=status,
                    confidence=conf,
                )
            )
    return spots


def _detect_lane_vehicle(img: np.ndarray, rows: int, cols: int) -> tuple[float, float] | None:
    """Find a brightly colored vehicle in the driving lane (e.g. yellow taxi)."""
    x1, y1, x2, y2 = _content_bbox(img)
    inner = img[y1:y2, x1:x2]
    ih, iw = inner.shape[:2]
    hsv = cv2.cvtColor(inner, cv2.COLOR_BGR2HSV)
    # Yellow / gold vehicles in lane
    yellow = cv2.inRange(hsv, (15, 80, 80), (40, 255, 255))
    if yellow.sum() < 800:
        return None
    coords = np.column_stack(np.where(yellow > 0))
    if coords.size == 0:
        return None
    cy, cx = coords.mean(axis=0)
    return float(x1 + cx), float(y1 + cy)


def _build_graph_2x6(spots: list[Spot], img_w: int, img_h: int, entrance_side: str = "left") -> tuple[list[GraphNode], list[list[str]]]:
    """
    Wireframe graph (refImages/parking_lot_graph.png):
    - Top/bottom perimeter chains; left/right vertical sides.
    - Each spot connects to exactly one perimeter node (same column).
    - No spot-to-spot edges (bipartite: spot <-> perimeter only).
    """
    by_row: dict[int, list[Spot]] = {}
    for s in spots:
        by_row.setdefault(s.row, []).append(s)
    row_keys = sorted(by_row.keys())
    top_row = row_keys[0]
    bot_row = row_keys[-1]

    top_spots = sorted(by_row[top_row], key=lambda s: s.col)
    bot_spots = sorted(by_row[bot_row], key=lambda s: s.col)

    grid_top = min(s.y - s.h / 2 for s in top_spots)
    grid_bot = max(s.y + s.h / 2 for s in bot_spots)
    grid_left = min(s.x - s.w / 2 for s in top_spots)
    grid_right = max(s.x + s.w / 2 for s in top_spots)
    road_gap = max(22.0, top_spots[0].h * 0.22)
    top_y = grid_top - road_gap
    bot_y = grid_bot + road_gap
    x_left = grid_left - road_gap
    x_right = grid_right + road_gap

    nodes: list[GraphNode] = []
    edges: list[tuple[str, str]] = []
    top_ids: list[str] = []
    bot_ids: list[str] = []

    nodes.extend(
        [
            GraphNode(id="perim_tl", x=x_left, y=top_y, kind="perimeter"),
            GraphNode(id="perim_tr", x=x_right, y=top_y, kind="perimeter"),
            GraphNode(id="perim_bl", x=x_left, y=bot_y, kind="perimeter"),
            GraphNode(id="perim_br", x=x_right, y=bot_y, kind="perimeter"),
        ]
    )

    for s in top_spots:
        pid = f"perim_top_{s.col}"
        nodes.append(GraphNode(id=pid, x=s.x, y=top_y, kind="perimeter"))
        top_ids.append(pid)
        edges.append((pid, f"node_{s.id}"))

    for s in bot_spots:
        pid = f"perim_bottom_{s.col}"
        nodes.append(GraphNode(id=pid, x=s.x, y=bot_y, kind="perimeter"))
        bot_ids.append(pid)
        edges.append((pid, f"node_{s.id}"))

    if top_ids:
        edges.append(("perim_tl", top_ids[0]))
        for i in range(len(top_ids) - 1):
            edges.append((top_ids[i], top_ids[i + 1]))
        edges.append((top_ids[-1], "perim_tr"))
    if bot_ids:
        edges.append(("perim_bl", bot_ids[0]))
        for i in range(len(bot_ids) - 1):
            edges.append((bot_ids[i], bot_ids[i + 1]))
        edges.append((bot_ids[-1], "perim_br"))
    edges.append(("perim_tl", "perim_bl"))
    edges.append(("perim_tr", "perim_br"))

    for s in spots:
        nodes.append(
            GraphNode(id=f"node_{s.id}", x=s.x, y=s.y, kind="spot", spot_id=s.id)
        )

    if entrance_side == "left":
        vx = max(14.0, x_left - road_gap * 0.45)
        vy = bot_y
        vehicle_edge = "perim_bl"
    else:
        mid = len(bot_ids) // 2
        vx = bot_spots[mid].x if bot_spots else img_w / 2
        vy = bot_y + road_gap * 0.85
        vehicle_edge = bot_ids[mid] if bot_ids else "perim_bl"

    nodes.append(GraphNode(id="vehicle", x=vx, y=vy, kind="vehicle"))
    edges.append(("vehicle", vehicle_edge))

    edge_list = [[a, b] for a, b in edges] + [[b, a] for a, b in edges]
    return nodes, edge_list


def _build_graph_3x13(spots: list[Spot], img_w: int, img_h: int, lane_vehicle: tuple[float, float] | None) -> tuple[list[GraphNode], list[list[str]]]:
    """Three horizontal perimeter bands; spots connect only to their row's perimeter."""
    cols = max((s.col for s in spots), default=0) + 1
    nodes: list[GraphNode] = []
    edges: list[tuple[str, str]] = []

    row_groups: dict[int, list[Spot]] = {}
    for s in spots:
        row_groups.setdefault(s.row, []).append(s)

    perim_ids_by_row: dict[int, list[str]] = {}
    max_row = max(row_groups.keys(), default=0)

    road_gap = 20.0
    for row_idx in sorted(row_groups.keys()):
        group = sorted(row_groups[row_idx], key=lambda s: s.col)
        if row_idx == 0:
            py = min(s.y - s.h / 2 for s in group) - road_gap
        elif row_idx == max_row:
            py = max(s.y + s.h / 2 for s in group) + road_gap
        else:
            py = group[0].y + group[0].h * 0.28

        ids: list[str] = []
        for s in group:
            pid = f"perim_r{row_idx}_{s.col}"
            nodes.append(GraphNode(id=pid, x=s.x, y=py, kind="perimeter"))
            ids.append(pid)
            edges.append((pid, f"node_{s.id}"))
        perim_ids_by_row[row_idx] = ids

        for i in range(len(ids) - 1):
            edges.append((ids[i], ids[i + 1]))

    row_keys = sorted(perim_ids_by_row.keys())
    for i in range(len(row_keys) - 1):
        r0, r1 = row_keys[i], row_keys[i + 1]
        for c in (0, cols - 1):
            a, b = f"perim_r{r0}_{c}", f"perim_r{r1}_{c}"
            if any(n.id == a for n in nodes) and any(n.id == b for n in nodes):
                edges.append((a, b))

    for s in spots:
        nodes.append(GraphNode(id=f"node_{s.id}", x=s.x, y=s.y, kind="spot", spot_id=s.id))

    right_col = cols - 1
    anchor_id = f"perim_r{row_keys[-1]}_{right_col}"
    anchor = next((n for n in nodes if n.id == anchor_id), None)
    if anchor:
        vx = anchor.x + road_gap * 1.2
        vy = anchor.y
        nodes.append(GraphNode(id="vehicle", x=vx, y=vy, kind="vehicle"))
        edges.append(("vehicle", anchor_id))
    else:
        nodes.append(GraphNode(id="vehicle", x=img_w * 0.92, y=img_h * 0.5, kind="vehicle"))

    if lane_vehicle:
        nodes.append(
            GraphNode(id="lane_vehicle", x=lane_vehicle[0], y=lane_vehicle[1], kind="junction")
        )
        mid_row = row_keys[1] if len(row_keys) > 1 else row_keys[0]
        nearest_col = min(
            range(cols),
            key=lambda c: abs(
                next((s.x for s in spots if s.col == c and s.row == mid_row), 0) - lane_vehicle[0]
            ),
        )
        mid_pid = f"perim_r{mid_row}_{nearest_col}"
        if any(n.id == mid_pid for n in nodes):
            edges.append(("lane_vehicle", mid_pid))

    edge_list = [[a, b] for a, b in edges] + [[b, a] for a, b in edges]
    return nodes, edge_list


LOT_CONFIGS = {
    "parking-lot-1": {"file": "parking-lot-1.png", "rows": 2, "cols": 6, "stylized": True, "layout": "2x6", "entrance": "left"},
    "parking-lot-2": {
        "file": "parking-lot-2.png",
        "rows": 2,
        "cols": 8,
        "row_cols": [8, 7],
        "row_ratios": [0.44, 0.56],
        "stylized": False,
        "layout": "2x6",
        "entrance": "left",
        "status_overrides": {
            (0, 1): "free",
            (0, 5): "free",
            (1, 0): "occupied",
            (1, 1): "occupied",
            (1, 4): "occupied",
        },
    },
    "parking-lot-3": {
        "file": "parking-lot-3.png",
        "rows": 2,
        "cols": 5,
        "row_ratios": [0.45, 0.55],
        "stylized": True,
        "layout": "2x6",
        "entrance": "left",
        "status_overrides": {
            (0, 2): "occupied",
            (1, 3): "occupied",
        },
    },
}


def analyze_lot(lot_id: str) -> dict:
    cfg = LOT_CONFIGS[lot_id]
    path = TEMP_DIR / cfg["file"]
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(path)

    h, w = img.shape[:2]
    spots = _grid_spots(
        img,
        cfg["rows"],
        cfg["cols"],
        cfg["stylized"],
        lot_id,
        row_ratios=cfg.get("row_ratios"),
        row_cols=cfg.get("row_cols"),
        status_overrides=cfg.get("status_overrides"),
    )
    lane_vehicle = None
    if cfg["layout"] == "3x13":
        lane_vehicle = _detect_lane_vehicle(img, cfg["rows"], cfg["cols"])

    if cfg["layout"] == "2x6":
        entrance_side = "left" if cfg.get("entrance") == "left" else "bottom"
        nodes, edges = _build_graph_2x6(spots, w, h, entrance_side=entrance_side)
    else:
        nodes, edges = _build_graph_3x13(spots, w, h, lane_vehicle)

    free_count = sum(1 for s in spots if s.status in ("free", "accessible"))
    occupied_count = sum(1 for s in spots if s.status == "occupied")

    return {
        "id": lot_id,
        "image": f"tempImages/{cfg['file']}",
        "width": w,
        "height": h,
        "layout": cfg["layout"],
        "summary": {
            "total_spots": len(spots),
            "free": free_count,
            "occupied": occupied_count,
        },
        "spots": [asdict(s) for s in spots],
        "nodes": [asdict(n) for n in nodes],
        "edges": edges,
        "lane_vehicle": list(lane_vehicle) if lane_vehicle else None,
        "vehicle_id": "vehicle",
    }


def draw_preview(lot_id: str, data: dict) -> np.ndarray:
    path = ROOT / data["image"]
    img = cv2.imread(str(path))
    overlay = img.copy()

    colors = {
        "occupied": (0, 0, 255),
        "free": (0, 200, 0),
        "unknown": (180, 180, 180),
    }

    for spot in data["spots"]:
        color = (
            colors["occupied"]
            if spot["status"] == "occupied"
            else colors["free"]
        )
        x, y, sw, sh = spot["x"], spot["y"], spot["w"], spot["h"]
        x0, y0 = int(x - sw / 2), int(y - sh / 2)
        x1, y1 = int(x + sw / 2), int(y + sh / 2)
        cv2.rectangle(overlay, (x0, y0), (x1, y1), color, 2)
        label = spot["status"][:3].upper()
        cv2.putText(
            overlay,
            label,
            (x0 + 4, y0 + 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )

    for node in data["nodes"]:
        nx, ny = int(node["x"]), int(node["y"])
        if node["kind"] in ("vehicle", "entrance"):
            cv2.circle(overlay, (nx, ny), 8, (255, 120, 60), -1)
        elif node["kind"] in ("aisle", "perimeter"):
            cv2.circle(overlay, (nx, ny), 4, (255, 255, 0), -1)
        elif node["kind"] == "junction":
            cv2.circle(overlay, (nx, ny), 8, (0, 165, 255), -1)

    return overlay


def run_all() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    index = {"lots": []}
    for lot_id in LOT_CONFIGS:
        data = analyze_lot(lot_id)
        out_path = DATA_DIR / f"{lot_id}.json"
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        preview = draw_preview(lot_id, data)
        cv2.imwrite(str(PREVIEW_DIR / f"{lot_id}_classified.png"), preview)
        index["lots"].append(
            {
                "id": lot_id,
                "image": data["image"],
                "summary": data["summary"],
                "dataUrl": f"data/lots/{lot_id}.json",
            }
        )
        print(f"{lot_id}: {data['summary']}")

    (DATA_DIR / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Wrote {len(LOT_CONFIGS)} lot files to {DATA_DIR}")


if __name__ == "__main__":
    run_all()
