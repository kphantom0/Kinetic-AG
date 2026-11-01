# kvl/k_transform.py

import numpy as np
from ._validation import as_grid, as_int, as_object, canonicalize_object

def shift(obj, vector, canvas_dimensions=None):
    """Shifts an object by a given (Y, X) vector and updates its structural indices."""
    _, position, _, indices, _ = as_object(obj)
    if not isinstance(vector, (list, tuple)) or len(vector) != 2:
        raise ValueError("vector must contain two integers (dy, dx)")
    dy, dx = (as_int(v, name="vector component") for v in vector)
    shifted_obj = canonicalize_object(obj)
    y, x = position
    shifted_obj["position"] = (int(y + dy), int(x + dx))
    
    new_indices = []
    for iy, ix in indices:
        new_indices.append([int(iy + dy), int(ix + dx)])
    shifted_obj["indices"] = new_indices
    
    if canvas_dimensions is not None:
        if not isinstance(canvas_dimensions, (list, tuple)) or len(canvas_dimensions) != 2:
            raise ValueError("canvas_dimensions must contain (height, width)")
        height, width = (as_int(v, name="canvas dimension") for v in canvas_dimensions)
        if height <= 0 or width <= 0:
            raise ValueError("canvas dimensions must be positive")
        if any(not (0 <= y < height and 0 <= x < width) for y, x in shifted_obj["indices"]):
            raise ValueError("shifted object would extend outside canvas_dimensions")
    as_object(shifted_obj)
    return shifted_obj

def rotate(obj, degrees=90):
    """Rotates an object's mask clockwise by increments of 90 degrees."""
    _, position, _, _, _ = as_object(obj)
    rotated_obj = canonicalize_object(obj)
    degrees = as_int(degrees, name="degrees")
    if degrees % 90:
        raise ValueError("degrees must be a multiple of 90")
    k = (degrees // 90) % 4
    
    mask = np.array(rotated_obj["mask"])
    rotated_mask = np.rot90(mask, k=-k)
    rotated_obj["mask"] = rotated_mask.tolist()
    rotated_obj["dimensions"] = rotated_mask.shape
    
    # Recalculate physical indices based on the new mask orientation
    y_start, x_start = position
    new_indices = []
    for r in range(rotated_mask.shape[0]):
        for c in range(rotated_mask.shape[1]):
            if rotated_mask[r, c] != 0:
                new_indices.append([int(y_start + r), int(x_start + c)])
    rotated_obj["indices"] = new_indices
    
    return rotated_obj

def mirror(obj, axis="vertical"):
    """Mirrors an object horizontally (left/right) or vertically (up/down)."""
    _, position, _, _, _ = as_object(obj)
    if axis not in ("vertical", "horizontal"):
        raise ValueError("axis must be 'vertical' or 'horizontal'")
    mirrored_obj = canonicalize_object(obj)
    mask = np.array(mirrored_obj["mask"])
    
    if axis == "vertical": 
        mirrored_mask = np.fliplr(mask)
    else: 
        mirrored_mask = np.flipud(mask)
        
    mirrored_obj["mask"] = mirrored_mask.tolist()
    
    y_start, x_start = position
    new_indices = []
    for r in range(mirrored_mask.shape[0]):
        for c in range(mirrored_mask.shape[1]):
            if mirrored_mask[r, c] != 0:
                new_indices.append([int(y_start + r), int(x_start + c)])
    mirrored_obj["indices"] = new_indices
    
    return mirrored_obj

def find_crop_area(grid, background_color=0):
    """
    Scans a grid and automatically trims away all outer dead space.
    Returns the tightest possible bounding box containing all active pixels.
    """
    background_color = as_int(background_color, name="background_color")
    matrix = as_grid(grid)
    if matrix.size == 0:
        return None

    # Find all coordinates that are NOT the background color
    active_coords = np.argwhere(matrix != background_color)
    
    if active_coords.size == 0:
        return None

    min_y, min_x = active_coords.min(axis=0)
    max_y, max_x = active_coords.max(axis=0)

    cropped_matrix = matrix[min_y:max_y+1, min_x:max_x+1]
    
    return {
        "cropped_grid": cropped_matrix.tolist(),
        "offset": (int(min_y), int(min_x)),
        "dimensions": (int(max_y - min_y + 1), int(max_x - min_x + 1))
    }

def has_overlap(obj1, obj2):
    """
    Compares the exact pixel coordinates of two objects to detect collisions.
    Operates in O(1) time complexity using set intersections.
    """
    # Convert list of lists to sets of tuples for instant math intersection
    _, _, _, indices1, _ = as_object(obj1)
    _, _, _, indices2, _ = as_object(obj2)
    set1 = set(indices1)
    set2 = set(indices2)
    
    overlap = set1.intersection(set2)
    
    return {
        "is_overlapping": len(overlap) > 0,
        "collision_pixels": sorted(overlap)
    }
