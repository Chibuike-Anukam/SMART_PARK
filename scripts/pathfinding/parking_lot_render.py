"""Pygame render of the makeshift parking lot from graph_maker.py."""

import sys
import math
import heapq

import pygame

# Data from graph_maker.py

NODE_COORDS = {
    "BL": (0.0, 0.0),
    "TL": (0.0, 15.5),
    "TR": (37.5, 15.5),
    "BR": (37.5, 0.0),
    "P1E": (5.625, 15.5),
    "P1": (5.625, 10.875),
    "P2E": (10.875, 15.5),
    "P2": (10.875, 10.875),
    "P3E": (16.125, 15.5),
    "P3": (16.125, 10.875),
    "P4E": (21.375, 15.5),
    "P4": (21.375, 10.875),
    "P5E": (26.625, 15.5),
    "P5": (26.625, 10.875),
    "P6E": (31.875, 15.5),
    "P6": (31.875, 10.875),
    "P7E": (5.625, 0.0),
    "P7": (5.625, 4.625),
    "P8E": (10.875, 0.0),
    "P8": (10.875, 4.625),
    "P9E": (16.125, 0.0),
    "P9": (16.125, 4.625),
    "P10E": (21.375, 0.0),
    "P10": (21.375, 4.625),
    "P11E": (26.625, 0.0),
    "P11": (26.625, 4.625),
    "P12E": (31.875, 0.0),
    "P12": (31.875, 4.625),
}

GRAPH = {
    "BL": {"TL": 15.5, "P7E": 5.625},
    "TL": {"BL": 15.5, "P1E": 5.625},
    "TR": {"P6E": 5.625, "BR": 15.5},
    "BR": {"TR": 15.5, "P12E": 5.625},
    "P1E": {"TR": 5.625, "P1": 4.625, "P2E": 5.25},
    "P2E": {"P1E": 5.25, "P2": 4.625, "P3E": 5.25},
    "P3E": {"P2E": 5.25, "P3": 4.625, "P4E": 5.25},
    "P4E": {"P3E": 5.25, "P4": 4.625, "P5E": 5.25},
    "P5E": {"P4E": 5.25, "P5": 4.625, "P6E": 5.25},
    "P6E": {"P5E": 5.25, "P6": 4.625, "TR": 5.625},
    "P7E": {"BL": 5.25, "P7": 4.625, "P8E": 5.25},
    "P8E": {"P7E": 5.25, "P8": 4.625, "P9E": 5.25},
    "P9E": {"P8E": 5.25, "P9": 4.625, "P10E": 5.25},
    "P10E": {"P9E": 5.25, "P10": 4.625, "P11E": 5.25},
    "P11E": {"P10E": 5.25, "P11": 4.625, "P12E": 5.25},
    "P12E": {"P11E": 5.25, "P12": 4.625, "BR": 5.625},
    "P1": {"P1E": 4.625},
    "P2": {"P2E": 4.625},
    "P3": {"P3E": 4.625},
    "P4": {"P4E": 4.625},
    "P5": {"P5E": 4.625},
    "P6": {"P6E": 4.625},
    "P7": {"P7E": 4.625},
    "P8": {"P8E": 4.625},
    "P9": {"P9E": 4.625},
    "P10": {"P10E": 4.625},
    "P11": {"P11E": 4.625},
    "P12": {"P12E": 4.625},
}

SPOT_IDS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11", "P12"]
ENTRY_IDS = ["P1E", "P2E", "P3E", "P4E", "P5E", "P6E", "P7E", "P8E", "P9E", "P10E", "P11E", "P12E"]
CORNER_IDS = ["BL", "TL", "TR", "BR"]
ROAD_IDS = CORNER_IDS + ENTRY_IDS

# Spot widths/heights (in meters) for drawing rectangles
SPOT_W = 5.25
SPOT_H = 4.625

# Spot status: Free spots from the simulation
VACANT_SPOTS = {"P1", "P4", "P9", "P12"}

# Vehicle starting position
VEHICLE_START = "P8E"

# Pygame setup

WINDOW_W = 1300
WINDOW_H = 760
PANEL_W = 280
MARGIN = 50

# Parking lot real-world dimensions
LOT_W = 37.5
LOT_H = 15.5

# Drawing area
VIEW_X = MARGIN
VIEW_Y = MARGIN
VIEW_W = WINDOW_W - PANEL_W - MARGIN * 2
VIEW_H = WINDOW_H - MARGIN * 2

SCALE = min(VIEW_W / LOT_W, VIEW_H / LOT_H)
OFFSET_X = VIEW_X + (VIEW_W - LOT_W * SCALE) / 2
OFFSET_Y = VIEW_Y + (VIEW_H - LOT_H * SCALE) / 2

# Colors

COLOR = {
    "bg": (26, 28, 34),
    "asphalt": (42, 44, 50),
    "asphalt_edge": (82, 85, 96),
    "road_mark": (100, 105, 115),
    "occupied": (239, 68, 68),
    "occupied_fill": (* (239, 68, 68), 90),
    "free": (34, 197, 94),
    "free_fill": (* (34, 197, 94), 90),
    "accessible": (56, 189, 248),
    "accessible_fill": (* (56, 189, 248), 90),
    "road_node": (250, 204, 21),
    "road_node_fill": (* (250, 204, 21), 200),
    "road_node_border": (15, 23, 42),
    "spot_node": (248, 250, 252),
    "spot_border": (30, 35, 45),
    "vehicle": (59, 130, 246),
    "vehicle_border": (30, 58, 138),
    "route_orange": (249, 115, 22),
    "route_green": (34, 197, 94),
    "route_orange_dim": (249, 115, 22),
    "route_green_dim": (34, 197, 94),
    "text": (226, 232, 240),
    "text_dim": (120, 130, 145),
    "text_highlight": (250, 204, 21),
    "panel_bg": (18, 20, 25),
    "panel_divider": (40, 44, 55),
    "title": (250, 204, 21),
}


def rgba(c, a=None):
    r, g, b = c[0], c[1], c[2]
    if a is not None:
        return (r, g, b, a)
    if len(c) == 4:
        return c
    return (r, g, b, 255)


# Coordinate transforms

def to_screen(rx: float, ry: float) -> tuple[float, float]:
    sx = OFFSET_X + rx * SCALE
    sy = OFFSET_Y + (LOT_H - ry) * SCALE  # flip Y
    return (sx, sy)


def to_screen_int(rx: float, ry: float) -> tuple[int, int]:
    return tuple(map(int, to_screen(rx, ry)))


# Dijkstra

def dijkstra(graph, start, goals):
    queue = [(0, start, [])]
    visited = set()
    while queue:
        cost, node, path = heapq.heappop(queue)
        if node not in visited:
            visited.add(node)
            path = path + [node]
            if node in goals:
                return path, cost, node
            for neighbor, distance in graph[node].items():
                if neighbor not in visited:
                    heapq.heappush(queue, (cost + distance, neighbor, path))
    return None, float("inf"), None


def astar_single(graph, start, goal, coords):
    """A* for pathfinding between two specific nodes."""
    queue = [(0, 0, start, [])]
    visited = set()
    while queue:
        _, cost, node, path = heapq.heappop(queue)
        if node not in visited:
            visited.add(node)
            path = path + [node]
            if node == goal:
                return path, cost
            for neighbor, distance in graph[node].items():
                if neighbor not in visited:
                    nx, ny = coords[neighbor]
                    gx, gy = coords[goal]
                    h = math.hypot(nx - gx, ny - gy)
                    heapq.heappush(queue, (cost + distance + h, cost + distance, neighbor, path))
    return None, float("inf")


# Drawing helpers

def draw_rounded_rect(surf, rect, color, radius=8):
    """Draw a filled rounded rectangle."""
    r = rect
    pygame.draw.rect(surf, color, (r[0] + radius, r[1], r[2] - 2 * radius, r[3]))
    pygame.draw.rect(surf, color, (r[0], r[1] + radius, r[2], r[3] - 2 * radius))
    pygame.draw.circle(surf, color, (r[0] + radius, r[1] + radius), radius)
    pygame.draw.circle(surf, color, (r[0] + r[2] - radius, r[1] + radius), radius)
    pygame.draw.circle(surf, color, (r[0] + radius, (r[1] + r[3] - radius)), radius)
    pygame.draw.circle(surf, color, (r[0] + r[2] - radius, (r[1] + r[3] - radius)), radius)


def draw_arrow(surf, start, end, color, size=6):
    """Draw an arrowhead at the end of a line."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle = math.atan2(dy, dx)
    p1 = (end[0] - size * math.cos(angle - 0.4), end[1] - size * math.sin(angle - 0.4))
    p2 = (end[0] - size * math.cos(angle + 0.4), end[1] - size * math.sin(angle + 0.4))
    pygame.draw.polygon(surf, color, [end, p1, p2])


# Main renderer

class ParkingLotRender:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        pygame.display.set_caption("SMART_PARK — Parking Lot Render")
        self.clock = pygame.time.Clock()
        self.font_sm = pygame.font.Font(None, 13)
        self.font_md = pygame.font.Font(None, 16)
        self.font_lg = pygame.font.Font(None, 22)
        self.font_title = pygame.font.Font(None, 30)
        self.font_label = pygame.font.Font(None, 14)

        # Interactive state
        self.vehicle_node = VEHICLE_START
        self.selected_spot = None
        self.route_path = []
        self.default_route = []

        # Generate default route
        self.refresh_default_route()
        self.running = True

    def spot_status(self, spot_id):
        return "free" if spot_id in VACANT_SPOTS else "occupied"

    def spot_bounds(self, spot_id):
        """Get approximate rectangle bounds for a spot."""
        idx = SPOT_IDS.index(spot_id)
        row = 0 if idx < 6 else 1
        col = idx % 6
        x = 5.625 + col * SPOT_W
        y = 10.875 if row == 0 else 4.625
        return (x - SPOT_W / 2, y - SPOT_H / 2, SPOT_W, SPOT_H)

    def free_spot_ids(self):
        return [s for s in SPOT_IDS if s in VACANT_SPOTS]

    def refresh_default_route(self):
        goals = self.free_spot_ids()
        if goals:
            path, dist, target = dijkstra(GRAPH, self.vehicle_node, goals)
            self.default_route = path or []
            self.default_target = target
        else:
            self.default_route = []
            self.default_target = None

    def refresh_selected_route(self):
        if self.selected_spot is None:
            self.route_path = []
            return
        goals = {self.selected_spot}
        path, dist, target = dijkstra(GRAPH, self.vehicle_node, goals)
        self.route_path = path or []

    def route_color(self, node_id):
        if node_id in self.route_path:
            return "green"
        if node_id in self.default_route:
            return "orange"
        return None

    def draw_lot_surface(self, surf):
        """Draw the parking lot asphalt and markings."""
        corners = ["BL", "BR", "TR", "TL"]
        poly = [to_screen_int(*NODE_COORDS[c]) for c in corners]
        pygame.draw.polygon(surf, COLOR["asphalt"], poly)
        pygame.draw.polygon(surf, COLOR["asphalt_edge"], poly, 3)

        # Horizontal lane dividers
        y_top = to_screen_int(0, 13.5)[1]
        y_bot = to_screen_int(0, 2.0)[1]
        x_l = to_screen_int(0, 0)[0]
        x_r = to_screen_int(37.5, 0)[0]
        dash_len = 15
        gap = 10
        for yy in (y_top, y_bot):
            x = x_l
            while x < x_r:
                end = min(x + dash_len, x_r)
                pygame.draw.line(surf, COLOR["road_mark"], (x, yy), (end, yy), 2)
                x += dash_len + gap

        # Vertical spot dividers
        for col in range(1, 6):
            cx = 5.625 + col * SPOT_W
            for row_y in [10.875, 4.625]:
                top = to_screen_int(cx, row_y + SPOT_H / 2)
                bot = to_screen_int(cx, row_y - SPOT_H / 2)
                pygame.draw.line(surf, COLOR["road_mark"], top, bot, 1)

    def draw_spots(self, surf):
        """Draw the parking spot rectangles."""
        for spot_id in SPOT_IDS:
            bx, by, bw, bh = self.spot_bounds(spot_id)
            status = self.spot_status(spot_id)

            sx = int(OFFSET_X + bx * SCALE)
            sy = int(OFFSET_Y + (LOT_H - (by + bh)) * SCALE)
            sw = int(bw * SCALE)
            sh = int(bh * SCALE)
            rect = pygame.Rect(sx, sy, sw, sh)

            if status == "free":
                fill = (*COLOR["free"], 60)
                border = COLOR["free"]
            elif status == "accessible":
                fill = (*COLOR["accessible"], 60)
                border = COLOR["accessible"]
            else:
                fill = (*COLOR["occupied"], 60)
                border = COLOR["occupied"]

            fill_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            fill_surf.fill(fill)
            surf.blit(fill_surf, (sx, sy))

            pygame.draw.rect(surf, border, rect, 2)

            label = spot_id
            if status == "free":
                label += " FREE"
            label_surf = self.font_label.render(label, True, border)
            lx = rect.centerx - label_surf.get_width() // 2
            ly = rect.centery - label_surf.get_height() // 2
            surf.blit(label_surf, (lx, ly))

    def draw_edges(self, surf):
        """Draw road edges and spot connectors."""
        for node_id in GRAPH:
            for neighbor in GRAPH[node_id]:
                if node_id < neighbor:
                    continue
                a_screen = to_screen(*NODE_COORDS[node_id])
                b_screen = to_screen(*NODE_COORDS[neighbor])
                a_is_road = node_id in ROAD_IDS
                b_is_road = neighbor in ROAD_IDS

                if a_is_road and b_is_road:
                    pygame.draw.line(surf, (148, 163, 184, 160), a_screen, b_screen, 2)
                elif a_is_road or b_is_road:
                    pygame.draw.line(surf, (148, 163, 184, 50), a_screen, b_screen, 1)

    def draw_route(self, surf):
        """Draw the route overlay lines."""
        for route, color_key, shadow_key in [
            (self.default_route, "route_orange", "route_orange_dim"),
            (self.route_path, "route_green", "route_green_dim"),
        ]:
            if not route or len(route) < 2:
                continue
            pts = [to_screen(*NODE_COORDS[n]) for n in route if n in NODE_COORDS]

            # Shadow
            shadow_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            pygame.draw.lines(shadow_surf, (*COLOR[color_key], 80), False, pts, 7)
            surf.blit(shadow_surf, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

            # Main line
            pygame.draw.lines(surf, COLOR[color_key], False, pts, 3)

            # Arrowheads at each segment
            for i in range(len(pts) - 1):
                draw_arrow(surf, pts[i], pts[i + 1], COLOR[color_key], 5)

    def draw_nodes(self, surf):
        """Draw all graph nodes."""
        for node_id, (rx, ry) in NODE_COORDS.items():
            screen_pos = to_screen_int(rx, ry)
            route_hl = self.route_color(node_id)

            if node_id in ROAD_IDS:
                r = 7
                if route_hl == "green":
                    fill = COLOR["route_green"]
                elif route_hl == "orange":
                    fill = COLOR["route_orange"]
                else:
                    fill = COLOR["road_node"]
                pygame.draw.circle(surf, fill, screen_pos, r)
                is_anchor = node_id == self.vehicle_node
                border = COLOR["vehicle"] if is_anchor else COLOR["road_node_border"]
                bw = 2 if is_anchor else 1
                pygame.draw.circle(surf, border, screen_pos, r, bw)

            elif node_id in SPOT_IDS:
                status = self.spot_status(node_id)
                is_selected = node_id == self.selected_spot
                r = 9 if is_selected else 7
                if status == "occupied":
                    fill = COLOR["occupied"]
                elif route_hl == "green":
                    fill = COLOR["route_green"]
                elif route_hl == "orange":
                    fill = COLOR["route_orange"]
                else:
                    fill = COLOR["spot_node"]
                pygame.draw.circle(surf, fill, screen_pos, r)
                border = (153, 27, 27) if status == "occupied" else COLOR["spot_border"]
                bw = 2 if is_selected else 1
                pygame.draw.circle(surf, border, screen_pos, r, bw)

    def draw_vehicle(self, surf):
        """Draw the vehicle marker."""
        if self.vehicle_node in NODE_COORDS:
            pos = to_screen_int(*NODE_COORDS[self.vehicle_node])
            pygame.draw.circle(surf, COLOR["vehicle"], pos, 11)
            pygame.draw.circle(surf, COLOR["vehicle_border"], pos, 11, 3)

            # Vehicle icon triangle
            pts = [
                (pos[0], pos[1] - 5),
                (pos[0] - 4, pos[1] + 3),
                (pos[0] + 4, pos[1] + 3),
            ]
            pygame.draw.polygon(surf, (255, 255, 255), pts)

    def draw_panel(self, surf):
        """Draw the info panel on the right side."""
        px = WINDOW_W - PANEL_W
        panel_rect = pygame.Rect(px, 0, PANEL_W, WINDOW_H)
        draw_rounded_rect(surf, panel_rect, COLOR["panel_bg"])

        # Title
        title = self.font_title.render("SMART_PARK", True, COLOR["title"])
        surf.blit(title, (px + 20, 25))

        subtitle = self.font_sm.render("Parking Lot Visualization", True, COLOR["text_dim"])
        surf.blit(subtitle, (px + 20, 58))

        # Divider
        pygame.draw.line(surf, COLOR["panel_divider"], (px + 20, 82), (px + PANEL_W - 20, 82), 1)

        # Legend
        y = 105
        legend_items = [
            (COLOR["vehicle"], "Vehicle position"),
            (COLOR["road_node"], "Road/perimeter node"),
            (COLOR["spot_node"], "Free spot node"),
            (COLOR["occupied"], "Occupied spot"),
            (COLOR["free"], "Free spot"),
            (COLOR["route_orange"], "Nearest free route"),
            (COLOR["route_green"], "Selected spot route"),
        ]
        for color, label in legend_items:
            pygame.draw.circle(surf, color, (px + 30, y), 5)
            txt = self.font_sm.render(label, True, COLOR["text"])
            surf.blit(txt, (px + 45, y - 5))
            y += 24

        # Divider
        pygame.draw.line(surf, COLOR["panel_divider"], (px + 20, y + 5),
                         (px + PANEL_W - 20, y + 5), 1)
        y += 25

        # Vehicle info
        veh_label = self.font_md.render("Vehicle", True, COLOR["text_highlight"])
        surf.blit(veh_label, (px + 20, y))
        y += 22
        veh_txt = self.font_sm.render(f"Node: {self.vehicle_node}", True, COLOR["text"])
        surf.blit(veh_txt, (px + 20, y))
        y += 20

        # Spot status
        y += 10
        status_label = self.font_md.render("Spot Status", True, COLOR["text_highlight"])
        surf.blit(status_label, (px + 20, y))
        y += 25

        for spot_id in SPOT_IDS:
            status = self.spot_status(spot_id)
            color = COLOR["free"] if status == "free" else COLOR["occupied"]
            icon = "●" if status == "free" else "○"
            txt = self.font_sm.render(f"{spot_id}: {status.upper()}", True, color)
            surf.blit(txt, (px + 25, y))
            y += 18
            if y > WINDOW_H - 40:
                break

        # Route info
        y = max(y + 10, 540)
        pygame.draw.line(surf, COLOR["panel_divider"], (px + 20, y),
                         (px + PANEL_W - 20, y), 1)
        y += 20
        route_label = self.font_md.render("Route Info", True, COLOR["text_highlight"])
        surf.blit(route_label, (px + 20, y))
        y += 22

        if self.default_target:
            def_route = self.font_sm.render(
                f"Orange: vehicle → {self.default_target}",
                True, COLOR["route_orange"],
            )
            surf.blit(def_route, (px + 20, y))
            y += 18
            def_dist = self.font_sm.render(
                f"  {len(self.default_route)} nodes in path",
                True, COLOR["text_dim"],
            )
            surf.blit(def_dist, (px + 20, y))
            y += 22
        else:
            no_free = self.font_sm.render("No free spots available", True, COLOR["occupied"])
            surf.blit(no_free, (px + 20, y))
            y += 22

        if self.selected_spot:
            sel = self.font_sm.render(
                f"Green: {self.selected_spot} → vehicle",
                True, COLOR["route_green"],
            )
            surf.blit(sel, (px + 20, y))
            y += 18
            sel_dist = self.font_sm.render(
                f"  {len(self.route_path)} nodes in path",
                True, COLOR["text_dim"],
            )
            surf.blit(sel_dist, (px + 20, y))
            y += 22
        else:
            hint = self.font_sm.render("Click a spot to select it", True, COLOR["text_dim"])
            surf.blit(hint, (px + 20, y))
            y += 22

        # Instructions
        y = max(y + 10, WINDOW_H - 120)
        pygame.draw.line(surf, COLOR["panel_divider"], (px + 20, y),
                         (px + PANEL_W - 20, y), 1)
        y += 15
        controls = [
            "Click road node → move vehicle",
            "Click free spot → show route",
            "Click selected spot → deselect",
            "R → Cycle vacant spots",
            "ESC → Quit",
        ]
        for ctrl in controls:
            c = self.font_sm.render(ctrl, True, COLOR["text_dim"])
            surf.blit(c, (px + 20, y))
            y += 18

    def handle_click(self, pos):
        """Handle mouse clicks for interaction."""
        mx, my = pos
        best_dist = 20
        best_node = None

        for node_id, (rx, ry) in NODE_COORDS.items():
            sx, sy = to_screen(rx, ry)
            dist = math.hypot(mx - sx, my - sy)
            if dist < best_dist:
                best_dist = dist
                best_node = node_id

        if best_node is None:
            return

        if best_node in ROAD_IDS:
            self.vehicle_node = best_node
            self.refresh_default_route()
            self.refresh_selected_route()
        elif best_node in SPOT_IDS:
            if self.selected_spot == best_node:
                self.selected_spot = None
                self.route_path = []
            else:
                self.selected_spot = best_node
                self.refresh_selected_route()

    def cycle_vacant(self):
        """Cycle through a different set of vacant spots for demo."""
        import random
        global VACANT_SPOTS
        all_spots = set(SPOT_IDS)
        n_free = random.randint(3, 6)
        VACANT_SPOTS = set(random.sample(list(all_spots), n_free))
        self.refresh_default_route()
        self.refresh_selected_route()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r:
                        self.cycle_vacant()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and event.pos[0] < WINDOW_W - PANEL_W:
                        self.handle_click(event.pos)

            # Draw frame
            self.screen.fill(COLOR["bg"])
            main_surf = pygame.Surface((WINDOW_W - PANEL_W, WINDOW_H), pygame.SRCALPHA)
            main_surf.fill(COLOR["bg"])

            self.draw_lot_surface(main_surf)
            self.draw_spots(main_surf)
            self.draw_edges(main_surf)
            self.draw_route(main_surf)
            self.draw_nodes(main_surf)
            self.draw_vehicle(main_surf)

            self.screen.blit(main_surf, (0, 0))
            self.draw_panel(self.screen)

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = ParkingLotRender()
    app.run()
