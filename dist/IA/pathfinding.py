import heapq

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(grid, start, goal):
    rows = len(grid)
    cols = len(grid[0])

    if not (0 <= start[1] < rows and 0 <= start[0] < cols):
        return []
    if not (0 <= goal[1] < rows and 0 <= goal[0] < cols):
        return []
    if grid[goal[1]][goal[0]] == 1:
        return []

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        # 4 directions : haut, bas, gauche, droite
        for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
            nx, ny = current[0] + dx, current[1] + dy

            if not (0 <= ny < rows and 0 <= nx < cols):
                continue
            if grid[ny][nx] == 1:
                continue

            tentative_g = g_score[current] + 1
            neighbor = (nx, ny)

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return []  # Pas de chemin trouvé