const canvas = document.getElementById("mapCanvas");
const ctx = canvas.getContext("2d");
const lotSelect = document.getElementById("lotSelect");
const summaryEl = document.getElementById("summary");
const routeInfo = document.getElementById("routeInfo");

let lotData = null;
let bgImage = null;
let selectedSpotNodeId = null;
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
  perimeter: "#facc15",
  vehicle: "#3b82f6",
  entrance: "#3b82f6",
  junction: "#a78bfa",
};

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

function vehicleNodeId() {
  if (!lotData) return null;
  if (lotData.vehicle_id) return lotData.vehicle_id;
  const vehicle = lotData.nodes.find(
    (n) => n.kind === "vehicle" || n.kind === "entrance"
  );
  return vehicle?.id ?? null;
}

function pathLength(path, nodeMap) {
  let length = 0;
  for (let i = 1; i < path.length; i++) {
    length += dist(nodeMap.get(path[i - 1]), nodeMap.get(path[i]));
  }
  return length;
}

function findSpotNodeAt(px, py, scale) {
  if (!lotData) return null;
  const hitRadius = 16 / scale;
  for (const node of lotData.nodes) {
    if (node.kind !== "spot") continue;
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
  const startId = vehicleNodeId();
  if (!startId || !lotData) {
    return { path: [], targetId: null, length: 0 };
  }

  const nodeMap = new Map(lotData.nodes.map((n) => [n.id, n]));
  let best = null;

  for (const targetId of freeSpotNodeIds()) {
    const path = astar(startId, targetId, lotData.nodes, lotData.edges);
    if (!path) continue;
    const length = pathLength(path, nodeMap);
    if (!best || length < best.length) {
      best = { path, targetId, length };
    }
  }

  return best ?? { path: [], targetId: null, length: 0 };
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
    if (node.kind === "perimeter") {
      ctx.beginPath();
      ctx.arc(node.x, node.y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(250, 204, 21, 0.85)";
      ctx.fill();
      continue;
    }

    if (node.kind === "vehicle" || node.kind === "entrance") {
      const highlight = routeHighlight(node.id);
      ctx.beginPath();
      ctx.arc(node.x, node.y, 10, 0, Math.PI * 2);
      ctx.fillStyle =
        highlight === "green"
          ? "#22c55e"
          : highlight === "orange"
            ? "#f97316"
            : NODE_COLORS.vehicle;
      ctx.fill();
      ctx.strokeStyle = "#1e3a8a";
      ctx.lineWidth = 2;
      ctx.stroke();
      continue;
    }

    if (node.kind !== "spot") continue;

    const isSelected = node.id === selectedSpotNodeId;
    const highlight = routeHighlight(node.id);
    ctx.beginPath();
    ctx.arc(node.x, node.y, isSelected ? 9 : 7, 0, Math.PI * 2);
    ctx.fillStyle =
      highlight === "green"
        ? "#22c55e"
        : highlight === "orange"
          ? "#f97316"
          : NODE_COLORS.spot;
    ctx.fill();
    ctx.strokeStyle = isSelected ? "#3b82f6" : "rgba(15, 23, 42, 0.85)";
    ctx.lineWidth = isSelected ? 3 : 1.5;
    ctx.stroke();
  }
}

async function loadLot(lotId) {
  lotData = await fetch(`../data/lots/${lotId}.json?v=${Date.now()}`).then(
    (r) => r.json()
  );
  selectedSpotNodeId = null;
  routePath = [];

  const nearest = computeNearestFreeRoute();
  defaultRoutePath = nearest.path;
  defaultRouteTargetId = nearest.targetId;

  bgImage = await new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = `../${lotData.image}`;
  });

  const { free, occupied, total_spots } = lotData.summary;
  summaryEl.textContent = `${total_spots} spots · ${free} free · ${occupied} occupied`;
  const defaultSpot = defaultRouteTargetId
    ? spotForNode(defaultRouteTargetId)
    : null;
  const defaultHint = defaultSpot
    ? `Orange path: nearest free spot at <strong>${spotLabel(defaultSpot)}</strong>. `
    : "No free spots available. ";

  routeInfo.innerHTML =
    `${defaultHint}Click a <strong>spot node</strong> for a green route from the <strong>blue vehicle</strong>. Occupied spots show a message only.`;

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

  const nodeId = findSpotNodeAt(x, y, scale);
  if (!nodeId) return;

  selectedSpotNodeId = nodeId;
  const spot = spotForNode(nodeId);
  if (!spot) return;

  if (spot.status === "occupied") {
    routePath = [];
    routeInfo.innerHTML = `Spot <strong>${spotLabel(spot)}</strong> is <strong>occupied</strong>. Choose a free or accessible stall.`;
    draw();
    return;
  }

  const startId = vehicleNodeId();
  if (!startId) {
    routePath = [];
    routeInfo.textContent = "No vehicle node defined for this lot.";
    draw();
    return;
  }

  const path = astar(startId, nodeId, lotData.nodes, lotData.edges);
  if (!path) {
    routePath = [];
    routeInfo.innerHTML = `No drivable route from the vehicle to <strong>${spotLabel(spot)}</strong>.`;
    draw();
    return;
  }

  routePath = path;
  const nodeMap = new Map(lotData.nodes.map((n) => [n.id, n]));
  const length = pathLength(path, nodeMap);
  routeInfo.innerHTML = `Route from <strong>vehicle</strong> → <strong>${spotLabel(spot)}</strong> (${spot.status})<br>${path.length} nodes · ~${Math.round(length)} px`;
  draw();
});

canvas.style.cursor = "crosshair";

init().catch((err) => {
  routeInfo.textContent = `Failed to load: ${err.message}. Run: py -3 serve_parking.py`;
  console.error(err);
});
