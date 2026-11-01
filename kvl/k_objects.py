# kvl/k_objects.py

import numpy as np
from scipy.ndimage import label, binary_fill_holes
from ._validation import as_grid, as_int, as_object, canonicalize_object

def find_objects(grid, diagonal_connectivity=False, background_color=0):
    """
    Scans a 2D grid and extracts all distinct objects.
    Returns a list of dictionaries containing object metadata.
    """
    if not isinstance(diagonal_connectivity, (bool, np.bool_)):
        raise ValueError("diagonal_connectivity must be a boolean")
    background_color = as_int(background_color, name="background_color")
    grid = as_grid(grid)
    if grid.size == 0:
        return []
    detected_objects = []
    
    if diagonal_connectivity:
        structure = np.ones((3, 3), dtype=int)
    else:
        structure = np.array([[0, 1, 0],
                              [1, 1, 1],
                              [0, 1, 0]])
        
    unique_colors = np.unique(grid)
    unique_colors = unique_colors[unique_colors != background_color]
    
    for color in unique_colors:
        color_mask = (grid == color).astype(int)
        labeled_mask, num_features = label(color_mask, structure=structure)
        
        for feature_id in range(1, num_features + 1):
            obj_indices = np.argwhere(labeled_mask == feature_id)
            min_y, min_x = obj_indices.min(axis=0)
            max_y, max_x = obj_indices.max(axis=0)
            
            obj_height = int(max_y - min_y + 1)
            obj_width = int(max_x - min_x + 1)
            local_mask = (labeled_mask[min_y:max_y+1, min_x:max_x+1] == feature_id).astype(int)
            
            detected_objects.append({
                "color": int(color),
                "position": (int(min_y), int(min_x)),
                "dimensions": (obj_height, obj_width),
                "indices": obj_indices.tolist(),
                "mask": local_mask.tolist()
            })
            
    return detected_objects

def filter_by_color(objects, color):
    """Returns a filtered list of objects matching a specific color integer."""
    color = as_int(color, name="color")
    if not isinstance(objects, (list, tuple)):
        raise ValueError("objects must be a list or tuple of object records")
    validated = [(obj, as_object(obj)[0]) for obj in objects]
    return [canonicalize_object(obj) for obj, obj_color in validated if obj_color == color]

def filter_by_size(objects, condition="largest"):
    """Filters objects based on the total pixel count size footprint."""
    if condition not in ("largest", "smallest"):
        raise ValueError("condition must be 'largest' or 'smallest'")
    if not isinstance(objects, (list, tuple)):
        raise ValueError("objects must be a list or tuple of object records")
    validated = [(obj, len(as_object(obj)[3])) for obj in objects]
    if not validated:
        return []
    sizes = [size for _, size in validated]
    
    if condition == "largest":
        target_size = max(sizes)
    elif condition == "smallest":
        target_size = min(sizes)
    return [canonicalize_object(obj) for obj, size in validated if size == target_size]

def get_com(obj):
    """
    Calculates the exact Center of Mass (centroid) of a shape.
    Returns (y, x) as standard Python floats.
    """
    _, _, _, indices, _ = as_object(obj)
    indices = np.asarray(indices)
    com_y, com_x = np.mean(indices, axis=0)
    return (float(com_y), float(com_x))

def get_enclosed_regions(grid, background_color=0):
    """
    Detects hollow containers (like a box of pixels) and isolates 
    the empty space completely enclosed inside them using binary hole filling.
    Returns a list of 'invisible' object dictionaries.
    """
    background_color = as_int(background_color, name="background_color")
    matrix = as_grid(grid)
    if matrix.size == 0:
        return []
    # 1. Create a binary mask where walls (non-background) are 1, and empty space is 0
    walls_mask = (matrix != background_color).astype(int)

    # 2. Fill the holes inside the walls
    filled_walls = binary_fill_holes(walls_mask).astype(int)

    # 3. The enclosed regions are the pixels that were 0 in the walls_mask but 1 in the filled_walls
    enclosed_mask = (filled_walls & ~walls_mask)

    # 4. Extract these trapped holes as manipulatable objects
    labeled_mask, num_features = label(enclosed_mask, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    enclosed_objects = []
    
    for feature_id in range(1, num_features + 1):
        obj_indices = np.argwhere(labeled_mask == feature_id)
        min_y, min_x = obj_indices.min(axis=0)
        max_y, max_x = obj_indices.max(axis=0)
        
        local_mask = (labeled_mask[min_y:max_y+1, min_x:max_x+1] == feature_id).astype(int)
        
        enclosed_objects.append({
            "color": int(background_color), 
            "position": (int(min_y), int(min_x)),
            "dimensions": (int(max_y - min_y + 1), int(max_x - min_x + 1)),
            "indices": obj_indices.tolist(),
            "mask": local_mask.tolist(),
            "is_enclosed_hole": True
        })
        
    return enclosed_objects
