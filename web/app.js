const canvas = document.getElementById("mapCanvas");
const ctx = canvas.getContext("2d");
const lotSelect = document.getElementById("lotSelect");
const summaryEl = document.getElementById("summary");
const routeInfo = document.getElementById("routeInfo");

let lotData = null;
let bgImage = null;
let selectedSpotNodeId = null;
let vehicleAnchorId = null;
let routePath = [];
let defaultRoutePath = [];
let defaultRouteTargetId = null;

const STATUS_COLORS = {
  occupied: "rgba(239, 68, 68, 0.45)",
  free: "rgba(34, 197, 94, 0.45)",
  accessible: "rgba(34, 211, 238, 0.45)",
  unknown: "rgba(148, 163, 184, 0.35)",
};

const NODE_COLORS = {
  spot: "#f8fafc",
  occupied: "#ef4444",
  perimeter: "#facc15",
  vehicle: "#3b82f6",
  junction: "#a78bfa",
};

const ROAD_KINDS = new Set(["perimeter", "aisle", "junction"]);

function dist(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function buildAdjacency(nodes, edges) {
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const adj = new Map();
  for (const n of nodes) adj.set(n.id, []);
  for (const [from, to] of edges) {
    const a = nodeMap.get(from);
    const b = nodeMap.get(to);
    if (!a || !b) continue;
    const w = dist(a, b);
    adj.get(from).push({ id: to, weight: w });
    adj.get(to).push({ id: from, weight: w });
  }
  return { adj, nodeMap };
}

function astar(startId, goalId, nodes, edges) {
  const { adj, nodeMap } = buildAdjacency(nodes, edges);
  const start = nodeMap.get(startId);
  const goal = nodeMap.get(goalId);
  if (!start || !goal) return null;

  const open = new Set([startId]);
  const cameFrom = new Map();
  const gScore = new Map([[startId, 0]]);
  const fScore = new Map([[startId, dist(start, goal)]]);

  while (open.size > 0) {
    let current = null;
    let bestF = Infinity;
    for (const id of open) {
      const f = fScore.get(id) ?? Infinity;
      if (f < bestF) {
        bestF = f;
        current = id;
      }
    }
    if (current === goalId) {
      const path = [current];
      while (cameFrom.has(current)) {
        current = cameFrom.get(current);
        path.push(current);
      }
      return path.reverse();
    }
    open.delete(current);
    for (const edge of adj.get(current) || []) {
      const tentative = (gScore.get(current) ?? Infinity) + edge.weight;
      if (tentative < (gScore.get(edge.id) ?? Infinity)) {
        cameFrom.set(edge.id, current);
        gScore.set(edge.id, tentative);
        fScore.set(edge.id, tentative + dist(nodeMap.get(edge.id), goal));
        open.add(edge.id);
      }
    }
  }
  return null;
}

function pathLength(path, nodeMap) {
  let length = 0;
  for (let i = 1; i < path.length; i++) {
    length += dist(nodeMap.get(path[i - 1]), nodeMap.get(path[i]));
  }
  return length;
}

function initialVehicleAnchorId() {
  const vehicleId = lotData.vehicle_id || "vehicle";
  for (const [from, to] of lotData.edges) {
    if (from === vehicleId && ROAD_KINDS.has(nodeKind(to))) return to;
    if (to === vehicleId && ROAD_KINDS.has(nodeKind(from))) return from;
  }
  const road = lotData.nodes.find((n) => ROAD_KINDS.has(n.kind));
  return road?.id ?? null;
}

function nodeKind(id) {
  return lotData.nodes.find((n) => n.id === id)?.kind;
}

function vehicleAnchorNode() {
  return lotData.nodes.find((n) => n.id === vehicleAnchorId) ?? null;
}

function findSpotNodeAt(px, py, scale) {
  const hitRadius = 16 / scale;
  for (const node of lotData.nodes) {
    if (node.kind !== "spot") continue;
    const spot = spotForNode(node.id);
    if (spot?.status === "occupied") continue;
    if (Math.hypot(px - node.x, py - node.y) <= hitRadius) return node.id;
  }
  return null;
}

function findRoadNodeAt(px, py, scale) {
  const hitRadius = 14 / scale;
  for (const node of lotData.nodes) {
    if (!ROAD_KINDS.has(node.kind)) continue;
    if (Math.hypot(px - node.x, py - node.y) <= hitRadius) return node.id;
  }
  return null;
}

function spotForNode(nodeId) {
  const node = lotData.nodes.find((n) => n.id === nodeId);
  if (!node?.spot_id) return null;
  return lotData.spots.find((s) => s.id === node.spot_id) ?? null;
}

function spotLabel(spot) {
  return `row ${spot.row + 1}, col ${spot.col + 1}`;
}

function freeSpotNodeIds() {
  return lotData.spots
    .filter((s) => s.status === "free" || s.status === "accessible")
    .map((s) => `node_${s.id}`);
}

function computeNearestFreeRoute() {
  if (!vehicleAnchorId || !lotData) {
    return { path: [], targetId: null, length: 0 };
  }

  const nodeMap = new Map(lotData.nodes.map((n) => [n.id, n]));
  let best = null;

  for (const targetId of freeSpotNodeIds()) {
    const path = astar(vehicleAnchorId, targetId, lotData.nodes, lotData.edges);
    if (!path) continue;
    const length = pathLength(path, nodeMap);
    if (!best || length < best.length) {
      best = { path, targetId, length };
    }
  }

  return best ?? { path: [], targetId: null, length: 0 };
}

function refreshDefaultRoute() {
  const nearest = computeNearestFreeRoute();
  defaultRoutePath = nearest.path;
  defaultRouteTargetId = nearest.targetId;
}

function refreshGreenRoute() {
  if (!selectedSpotNodeId || !vehicleAnchorId) {
    routePath = [];
    return null;
  }
  const spot = spotForNode(selectedSpotNodeId);
  if (!spot || spot.status === "occupied") {
    routePath = [];
    return null;
  }
  const path = astar(selectedSpotNodeId, vehicleAnchorId, lotData.nodes, lotData.edges);
  routePath = path ?? [];
  return spot;
}

function updateRouteInfo(extra = "") {
  const defaultSpot = defaultRouteTargetId
    ? spotForNode(defaultRouteTargetId)
    : null;
  const defaultHint = defaultSpot
    ? `Orange: vehicle → nearest free at <strong>${spotLabel(defaultSpot)}</strong>. `
    : "No free spots available. ";

  if (!extra && selectedSpotNodeId) {
    const spot = spotForNode(selectedSpotNodeId);
    if (spot?.status === "occupied") {
      extra = `Spot <strong>${spotLabel(spot)}</strong> is <strong>occupied</strong>.`;
    } else if (spot && routePath.length > 1) {
      const nodeMap = new Map(lotData.nodes.map((n) => [n.id, n]));
      const length = pathLength(routePath, nodeMap);
      extra = `Green: <strong>${spotLabel(spot)}</strong> → vehicle (${routePath.length} nodes, ~${Math.round(length)} px).`;
    }
  }

  routeInfo.innerHTML =
    `${defaultHint}${extra || "Click a <strong>road node</strong> to move the vehicle. Click a <strong>spot node</strong> for a green path to the vehicle."}`;
}

function drawRouteLine(path, color, shadowColor) {
  if (!path || path.length < 2) return;
  const nodeMap = new Map(lotData.nodes.map((n) => [n.id, n]));
  const first = nodeMap.get(path[0]);
  if (!first) return;

  ctx.strokeStyle = color;
  ctx.lineWidth = 5;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.shadowColor = shadowColor;
  ctx.shadowBlur = 8;
  ctx.beginPath();
  ctx.moveTo(first.x, first.y);
  for (let i = 1; i < path.length; i++) {
    const n = nodeMap.get(path[i]);
    if (n) ctx.lineTo(n.x, n.y);
  }
  ctx.stroke();
  ctx.shadowBlur = 0;
}

function routeHighlight(nodeId) {
  if (routePath.includes(nodeId)) return "green";
  if (defaultRoutePath.includes(nodeId)) return "orange";
  return null;
}

function draw() {
  if (!lotData || !bgImage) return;

  const w = lotData.width;
  const h = lotData.height;
  canvas.width = w;
  canvas.height = h;

  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(bgImage, 0, 0, w, h);

  for (const spot of lotData.spots) {
    const color = STATUS_COLORS[spot.status] || STATUS_COLORS.unknown;
    const x0 = spot.x - spot.w / 2;
    const y0 = spot.y - spot.h / 2;
    ctx.fillStyle = color;
    ctx.fillRect(x0, y0, spot.w, spot.h);
    ctx.strokeStyle = color.replace("0.45", "0.9");
    ctx.lineWidth = 1.5;
    ctx.strokeRect(x0, y0, spot.w, spot.h);
  }

  const nodeMap = new Map(lotData.nodes.map((n) => [n.id, n]));
  const isSpot = (id) => nodeMap.get(id)?.kind === "spot";

  ctx.strokeStyle = "rgba(148, 163, 184, 0.5)";
  ctx.lineWidth = 2;
  for (const [from, to] of lotData.edges) {
    const a = nodeMap.get(from);
    const b = nodeMap.get(to);
    if (!a || !b) continue;
    if (isSpot(from) && isSpot(to)) continue;
    if (from === "vehicle" || to === "vehicle") continue;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  }

  ctx.strokeStyle = "rgba(148, 163, 184, 0.22)";
  ctx.lineWidth = 1;
  for (const [from, to] of lotData.edges) {
    const a = nodeMap.get(from);
    const b = nodeMap.get(to);
    if (!a || !b) continue;
    if (!(isSpot(from) ^ isSpot(to))) continue;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  }

  drawRouteLine(defaultRoutePath, "#f97316", "#c2410c");
  drawRouteLine(routePath, "#22c55e", "#16a34a");

  for (const node of lotData.nodes) {
    if (node.kind === "vehicle" || node.kind === "entrance") continue;

    if (ROAD_KINDS.has(node.kind)) {
      const isAnchor = node.id === vehicleAnchorId;
      const highlight = isAnchor ? null : routeHighlight(node.id);
      const roadR = 7;
      ctx.beginPath();
      ctx.arc(node.x, node.y, roadR, 0, Math.PI * 2);
      if (highlight === "green") ctx.fillStyle = "#22c55e";
      else if (highlight === "orange") ctx.fillStyle = "#f97316";
      else ctx.fillStyle = "rgba(250, 204, 21, 0.9)";
      ctx.fill();
      if (isAnchor) {
        ctx.strokeStyle = "#3b82f6";
        ctx.lineWidth = 2;
        ctx.stroke();
      } else {
        ctx.strokeStyle = "rgba(15, 23, 42, 0.85)";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
      continue;
    }

    if (node.kind !== "spot") continue;

    const spot = spotForNode(node.id);
    const isOccupied = spot?.status === "occupied";
    const isSelected = node.id === selectedSpotNodeId;
    const highlight = routeHighlight(node.id);
    ctx.beginPath();
    ctx.arc(node.x, node.y, isSelected ? 9 : 7, 0, Math.PI * 2);
    if (isOccupied) {
      ctx.fillStyle = NODE_COLORS.occupied;
    } else if (highlight === "green") {
      ctx.fillStyle = "#22c55e";
    } else if (highlight === "orange") {
      ctx.fillStyle = "#f97316";
    } else {
      ctx.fillStyle = NODE_COLORS.spot;
    }
    ctx.fill();
    ctx.strokeStyle = isSelected
      ? "#3b82f6"
      : isOccupied
        ? "#991b1b"
        : "rgba(15, 23, 42, 0.85)";
    ctx.lineWidth = isSelected ? 3 : 1.5;
    ctx.stroke();
  }

  const anchor = vehicleAnchorNode();
  if (anchor) {
    ctx.beginPath();
    ctx.arc(anchor.x, anchor.y, 11, 0, Math.PI * 2);
    ctx.fillStyle = NODE_COLORS.vehicle;
    ctx.fill();
    ctx.strokeStyle = "#1e3a8a";
    ctx.lineWidth = 2.5;
    ctx.stroke();
  }
}

async function loadLot(lotId) {
  lotData = await fetch(`../data/lots/${lotId}.json?v=${Date.now()}`).then(
    (r) => r.json()
  );
  selectedSpotNodeId = null;
  routePath = [];
  vehicleAnchorId = initialVehicleAnchorId();

  refreshDefaultRoute();

  bgImage = await new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = `../${lotData.image}`;
  });

  const { free, occupied, total_spots } = lotData.summary;
  summaryEl.textContent = `${total_spots} spots · ${free} free · ${occupied} occupied`;
  updateRouteInfo();
  draw();
}

async function init() {
  const index = await fetch("../data/lots/index.json").then((r) => r.json());
  lotSelect.innerHTML = "";
  for (const lot of index.lots) {
    const opt = document.createElement("option");
    opt.value = lot.id;
    opt.textContent = lot.id.replace("parking-lot-", "Lot ");
    lotSelect.appendChild(opt);
  }
  lotSelect.addEventListener("change", () => loadLot(lotSelect.value));
  await loadLot(lotSelect.value);
}

canvas.addEventListener("click", (e) => {
  if (!lotData) return;
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = (e.clientX - rect.left) * scaleX;
  const y = (e.clientY - rect.top) * scaleY;
  const scale = Math.max(scaleX, scaleY);

  const spotId = findSpotNodeAt(x, y, scale);
  const roadId = findRoadNodeAt(x, y, scale);

  if (spotId) {
    handleSpotClick(spotId);
    return;
  }

  if (roadId) {
    vehicleAnchorId = roadId;
    refreshDefaultRoute();
    if (selectedSpotNodeId) {
      const spot = refreshGreenRoute();
      if (spot) updateRouteInfo();
      else if (spotForNode(selectedSpotNodeId)?.status === "occupied") {
        updateRouteInfo(
          `Spot <strong>${spotLabel(spotForNode(selectedSpotNodeId))}</strong> is <strong>occupied</strong>.`
        );
      }
    } else {
      updateRouteInfo("Vehicle moved along the road.");
    }
    draw();
    return;
  }
});

function handleSpotClick(spotId) {
  if (!lotData) return;

  if (selectedSpotNodeId === spotId && routePath.length > 0) {
    selectedSpotNodeId = null;
    routePath = [];
    updateRouteInfo();
    draw();
    return;
  }

  selectedSpotNodeId = spotId;
  const spot = spotForNode(spotId);
  if (!spot) return;

  if (!vehicleAnchorId) {
    routePath = [];
    routeInfo.textContent = "No vehicle position on the road network.";
    draw();
    return;
  }

  const path = astar(spotId, vehicleAnchorId, lotData.nodes, lotData.edges);
  if (!path) {
    routePath = [];
    updateRouteInfo(
      `No drivable route from <strong>${spotLabel(spot)}</strong> to the vehicle.`
    );
    draw();
    return;
  }

  routePath = path;
  updateRouteInfo();
  draw();
}

canvas.style.cursor = "crosshair";

init().catch((err) => {
  routeInfo.textContent = `Failed to load: ${err.message}. Run: py -3 serve_parking.py`;
  console.error(err);
});
