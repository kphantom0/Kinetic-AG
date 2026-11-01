"""Zero-dependency pure-Python reference oracle for K-VL differential testing."""

from collections import deque
from typing import Any


def ref_find_objects(
    grid: list[list[int]], diagonal_connectivity: bool = False, background_color: int = 0
) -> list[dict[str, Any]]:
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    colors = sorted({cell for row in grid for cell in row if cell != background_color})
    neighbors = (
        [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        if diagonal_connectivity
        else [(-1, 0), (1, 0), (0, -1), (0, 1)]
    )
    results: list[dict[str, Any]] = []

    for color in colors:
        visited = [[False] * width for _ in range(height)]
        for row in range(height):
            for column in range(width):
                if grid[row][column] != color or visited[row][column]:
                    continue
                queue = deque([(row, column)])
                visited[row][column] = True
                points = []
                while queue:
                    current_y, current_x = queue.popleft()
                    points.append((current_y, current_x))
                    for dy, dx in neighbors:
                        next_y, next_x = current_y + dy, current_x + dx
                        if (
                            0 <= next_y < height
                            and 0 <= next_x < width
                            and not visited[next_y][next_x]
                            and grid[next_y][next_x] == color
                        ):
                            visited[next_y][next_x] = True
                            queue.append((next_y, next_x))
                points.sort()
                min_y = min(y for y, _ in points)
                max_y = max(y for y, _ in points)
                min_x = min(x for _, x in points)
                max_x = max(x for _, x in points)
                object_height, object_width = max_y - min_y + 1, max_x - min_x + 1
                point_set = set(points)
                mask = [
                    [
                        1 if (min_y + mask_y, min_x + mask_x) in point_set else 0
                        for mask_x in range(object_width)
                    ]
                    for mask_y in range(object_height)
                ]
                results.append(
                    {
                        "color": int(color),
                        "position": (min_y, min_x),
                        "dimensions": (object_height, object_width),
                        "indices": [[y, x] for y, x in points],
                        "mask": mask,
                    }
                )
    return results


def ref_get_enclosed_regions(
    grid: list[list[int]], background_color: int = 0
) -> list[dict[str, Any]]:
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    outside = [[False] * width for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()
    for row in range(height):
        for column in range(width):
            if (
                (row in (0, height - 1) or column in (0, width - 1))
                and grid[row][column] == background_color
            ):
                outside[row][column] = True
                queue.append((row, column))

    while queue:
        current_y, current_x = queue.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next_y, next_x = current_y + dy, current_x + dx
            if (
                0 <= next_y < height
                and 0 <= next_x < width
                and not outside[next_y][next_x]
                and grid[next_y][next_x] == background_color
            ):
                outside[next_y][next_x] = True
                queue.append((next_y, next_x))

    hole_grid = [
        [1 if grid[row][column] == background_color and not outside[row][column] else 0
         for column in range(width)]
        for row in range(height)
    ]
    holes = ref_find_objects(hole_grid)
    for hole in holes:
        hole["color"] = int(background_color)
        hole["is_enclosed_hole"] = True
    return holes


def ref_get_distance(obj1: dict[str, Any], obj2: dict[str, Any]) -> int:
    return min(
        abs(y1 - y2) + abs(x1 - x2)
        for y1, x1 in obj1["indices"]
        for y2, x2 in obj2["indices"]
    )
