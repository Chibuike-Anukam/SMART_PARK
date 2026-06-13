import heapq


# 1. Store the real-world coordinates (X, Y in meters) of each pylon/spot
# This is crucial for the A* heuristic (estimating distance to the goal)
node_coordinates = {
    'BL': (0.0, 0.0),
    'TL':  (0.0, 15.5),
    'TR':  (37.5, 15.5),
    'BR':  (37.5, 0.0),
    'P1E':  (5.625, 15.5),
    'P1':  (5.625, 10.875),
    'P2E':  (10.875, 15.5),
    'P2':  (10.875, 10.875),
    'P3E':  (16.125, 15.5),
    'P3':  (16.125, 10.875),
    'P4E':  (21.375, 15.5),
    'P4':  (21.375, 10.875),
    'P5E':  (26.625, 15.5),
    'P5':  (26.625, 10.875),
    'P6E':  (31.875, 15.5),
    'P6':  (31.875, 10.875),
    'P7E':  (5.625, 0.0),
    'P7':  (5.625, 4.625),
    'P8E':  (10.875, 0.0),
    'P8':  (10.875, 4.625),
    'P9E':  (16.125, 0.0),
    'P9':  (16.125, 4.625),
    'P10E':  (21.375, 0.0),
    'P10':  (21.375, 4.625),
    'P11E':  (26.625, 0.0),
    'P11':  (26.625, 4.625),
    'P12E':  (31.875, 0.0),
    'P12':  (31.875, 4.625),
}

# 2. Store the Adjacency List (The map of valid paths and their weights)
# Only connect pylons that have a straight, drivable lane between them!
parking_lot_graph = {
    'BL': {'TL': 15.5, 'P7E': 5.625},
    'TL':  {'BL': 15.5, 'P1E': 5.625},
    'TR':  {'P6E': 5.625, 'BR': 15.5},
    'BR':  {'TR': 15.5, 'P12E': 5.625},
    'P1E': {'TR': 5.625, 'P1': 4.625, 'P2E': 5.25},  
    'P2E': {'P1E': 5.25, 'P2': 4.625, 'P3E': 5.25},
    'P3E': {'P2E': 5.25, 'P3': 4.625, 'P4E': 5.25},
    'P4E': {'P3E': 5.25, 'P4': 4.625, 'P5E': 5.25},
    'P5E': {'P4E': 5.25, 'P5': 4.625, 'P6E': 5.25},
    'P6E': {'P5E': 5.25, 'P6': 4.625, 'TR': 5.625},
    'P7E': {'BL': 5.25, 'P7': 4.625, 'P8E': 5.25},
    'P8E': {'P7E': 5.25, 'P8': 4.625, 'P9E': 5.25},
    'P9E': {'P8E': 5.25, 'P9': 4.625, 'P10E': 5.25},
    'P10E': {'P9E': 5.25, 'P10': 4.625, 'P11E': 5.25},
    'P11E': {'P10E': 5.25, 'P11': 4.625, 'P12E': 5.25},
    'P12E': {'P11E': 5.25, 'P12': 4.625, 'BR': 5.625},
    'P1': {'P1E': 4.625},
    'P2': {'P2E': 4.625},
    'P3': {'P3E': 4.625},
    'P4': {'P4E': 4.625},
    'P5': {'P5E': 4.625},
    'P6': {'P6E': 4.625},
    'P7': {'P7E': 4.625},
    'P8': {'P8E': 4.625},
    'P9': {'P9E': 4.625},
    'P10': {'P10E': 4.625},
    'P11': {'P11E': 4.625},
    'P12': {'P12E': 4.625}

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
            if node in goal:
                return path, cost, node  # Returns the path, distance, and WHICH spot it chose

            # Check neighbors and add them to the priority queue
            for neighbor, distance in graph[node].items():
                if neighbor not in visited:
                    heapq.heappush(queue, (cost + distance, neighbor, path))

    return None, float("inf")

# --- SIMULATION ---
# A vacant spot detection algorithm flags Spot_42 as open
vacant_spot_set = {'P1', 'P4', 'P9', 'P12'}

best_path, total_meters, chosen_spot = dijkstra(parking_lot_graph, 'P8E', vacant_spot_set)

print(f"Navigation Path: {' -> '.join(best_path)}")
print(f"Total Distance: {total_meters:.2f} centimeters")
print(f"Chosen Spot: {chosen_spot}")