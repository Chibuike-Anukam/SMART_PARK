import heapq


# 1. Store the real-world coordinates (X, Y in meters) of each pylon/spot
# This is crucial for the A* heuristic (estimating distance to the goal)
node_coordinates = {
    'Entrance': (0.0, 0.0),
    'Pylon_A':  (0.0, 15.5),
    'Pylon_B':  (20.2, 15.5),
    'Pylon_C':  (20.2, 0.0),
    'Spot_42':  (25.0, 5.0)  # The vacant spot discovered by your system
}

# 2. Store the Adjacency List (The map of valid paths and their weights)
# Only connect pylons that have a straight, drivable lane between them!
parking_lot_graph = {
    'Entrance': {'Pylon_A': 15.5, 'Pylon_C': 20.2},
    'Pylon_A':  {'Entrance': 15.5, 'Pylon_B': 20.2},
    'Pylon_B':  {'Pylon_A': 20.2, 'Pylon_C': 15.5, 'Spot_42': 11.5},
    'Pylon_C':  {'Entrance': 20.2, 'Pylon_B': 15.5},
    'Spot_42':  {'Pylon_B': 11.5}
}


def dijkstra(graph, start, goal):
    # Queue stores tuples of: (total_distance_so_far, current_node, path_taken)
    queue = [(0, start, [])]
    visited = set()

    while queue:
        (cost, node, path) = heapq.heappop(queue)

        if node not in visited:
            visited.add(node)
            path = path + [node]

            # If we reached the vacant spot, return the path and total distance
            if node == goal:
                return path, cost

            # Check neighbors and add them to the priority queue
            for neighbor, distance in graph[node].items():
                if neighbor not in visited:
                    heapq.heappush(queue, (cost + distance, neighbor, path))

    return None, float("inf")

# --- SIMULATION ---
# A vacant spot detection algorithm flags Spot_42 as open
vacant_spot = 'Spot_42'

best_path, total_meters = dijkstra(parking_lot_graph, 'Entrance', vacant_spot)

print(f"Navigation Path: {' -> '.join(best_path)}")
print(f"Total Distance: {total_meters:.2f} meters")