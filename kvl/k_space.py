# kvl/k_space.py

import numpy as np
from scipy.spatial import cKDTree
from numbers import Real
import math
from ._validation import MAX_GRID_CELLS, MAX_GRID_DIM, as_grid, as_int, as_object

def get_dimensions(grid):
    """Returns the (height, width) of a given grid matrix."""
    matrix = as_grid(grid)
    if matrix.size == 0:
        return (0, 0)
    return matrix.shape

def create_blank_grid(height, width, background_color=0):
    """Generates a blank 2D matrix filled completely with a background color."""
    height, width = as_int(height, name="height"), as_int(width, name="width")
    background_color = as_int(background_color, name="background_color")
    if height <= 0 or width <= 0:
        raise ValueError("height and width must be positive")
    if height > MAX_GRID_DIM or width > MAX_GRID_DIM or height * width > MAX_GRID_CELLS:
        raise ValueError(f"grid allocation exceeds limits ({MAX_GRID_DIM} per dimension, {MAX_GRID_CELLS} cells total)")
    return np.full((height, width), int(background_color), dtype=int).tolist()

def create_blank_grid_like(grid, background_color=0):
    """Generates a blank canvas that perfectly matches the sizing of a reference grid."""
    background_color = as_int(background_color, name="background_color")
    height, width = get_dimensions(grid)
    if height == 0 or width == 0:
        return []
    return create_blank_grid(height, width, background_color)

def get_distance(obj1, obj2):
    """
    Calculates the minimum Manhattan distance between any pixel of obj1 
    and any pixel of obj2. Manhattan distance is defined as |y1 - y2| + |x1 - x2|.
    Returns an integer representing the shortest block distance.
    """
    _, _, _, points1, _ = as_object(obj1)
    _, _, _, points2, _ = as_object(obj2)
    # as_object bounds coordinates so float64 represents every coordinate and
    # the maximum Manhattan distance exactly in this nearest-neighbor index.
    tree = cKDTree(np.asarray(points1, dtype=np.float64))
    distances, _ = tree.query(np.asarray(points2, dtype=np.float64), k=1, p=1)
    return int(np.min(distances))

def is_aligned(obj1, obj2):
    """
    Checks if two objects are vertically or horizontally aligned based on their bounding boxes.
    Returns a dictionary indicating alignment type.
    """
    _, (y1_start, x1_start), (h1, w1), _, _ = as_object(obj1)
    y1_end, x1_end = y1_start + h1 - 1, x1_start + w1 - 1
    
    _, (y2_start, x2_start), (h2, w2), _, _ = as_object(obj2)
    y2_end, x2_end = y2_start + h2 - 1, x2_start + w2 - 1
    
    # Check horizontal alignment (sharing or overlapping row spans / Y-coordinates)
    horizontal_align = not (y1_end < y2_start or y2_end < y1_start)
    
    # Check vertical alignment (sharing or overlapping column spans / X-coordinates)
    vertical_align = not (x1_end < x2_start or x2_end < x1_start)
    
    return {
        "horizontal": bool(horizontal_align),
        "vertical": bool(vertical_align)
    }

def detect_background_grid(grid, threshold=0.7, ignore_color=0):
    """
    Detects if the grid contains a recurring background lattice or mesh pattern,
    even if foreground shapes are partially covering or overlapping the lines.
    """
    matrix = as_grid(grid)
    if isinstance(threshold, bool) or not isinstance(threshold, Real) or not math.isfinite(float(threshold)):
        raise ValueError("threshold must be a finite real number between 0 and 1")
    threshold = float(threshold)
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    ignore_color = as_int(ignore_color, name="ignore_color")
    height, width = get_dimensions(matrix)
    
    if height == 0 or width == 0:
        return None
        
    unique_colors = np.unique(matrix)
    
    for color in unique_colors:
        # CRITICAL FIX: Use continue instead of return None to keep evaluating other colors
        if color == ignore_color:  
            continue 
            
        # Calculate what percentage of each row/column matches this color
        row_counts = [np.sum(matrix[y, :] == color) / width for y in range(height)]
        col_counts = [np.sum(matrix[:, x] == color) / height for x in range(width)]
        
        # Identify lines that cross our density threshold (standard Python ints via enumerate)
        matching_rows = [int(y) for y, ratio in enumerate(row_counts) if ratio >= threshold]
        matching_cols = [int(x) for x, ratio in enumerate(col_counts) if ratio >= threshold]
        
        # If we find a matching intersecting lattice pattern
        if len(matching_rows) >= 2 or len(matching_cols) >= 2:
            # Safely cast np.diff results to pure python integers
            row_diffs = np.diff(matching_rows)
            col_diffs = np.diff(matching_cols)
            row_period = int(row_diffs[0]) if len(row_diffs) and np.all(row_diffs == row_diffs[0]) else None
            col_period = int(col_diffs[0]) if len(col_diffs) and np.all(col_diffs == col_diffs[0]) else None
            
            return {
                "grid_color": int(color),
                "row_indices": matching_rows,
                "column_indices": matching_cols,
                "row_period": row_period,
                "column_period": col_period
            }
            
    return None
