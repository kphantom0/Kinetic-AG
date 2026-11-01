"""Shared input validation for K-VL's public operations."""

from numbers import Integral

import numpy as np

INT64_MIN = -(1 << 63)
INT64_MAX = (1 << 63) - 1
EXACT_DISTANCE_COORD_LIMIT = 1 << 50
MAX_GRID_DIM = 4096
MAX_GRID_CELLS = 1_000_000


def as_grid(grid, *, name="grid", allow_empty=True):
    """Return a validated 2D integer array without silently coercing values."""
    try:
        array = np.asarray(grid)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a rectangular 2D grid") from exc

    if array.size == 0:
        is_empty_sequence = isinstance(grid, (list, tuple)) and len(grid) == 0
        is_empty_matrix = (array.ndim == 2 and array.shape == (0, 0)
                           and np.issubdtype(array.dtype, np.integer)
                           and not np.issubdtype(array.dtype, np.bool_))
        if allow_empty and (is_empty_sequence or is_empty_matrix):
            return np.empty((0, 0), dtype=np.int64)
        if not allow_empty and array.ndim == 2 and array.shape == (0, 0):
            raise ValueError(f"{name} must not be empty")
        raise ValueError(f"{name} must be a non-empty rectangular 2D integer grid")
    if array.ndim != 2:
        raise ValueError(f"{name} must be a 2D grid; got {array.ndim} dimensions")
    if array.dtype == object:
        values = list(array.flat)
        if any(isinstance(v, bool) or not isinstance(v, Integral) for v in values):
            raise ValueError(f"{name} cells must be integers")
        if any(int(v) < INT64_MIN or int(v) > INT64_MAX for v in values):
            raise ValueError(f"{name} cell value exceeds signed 64-bit range")
        array = np.asarray(grid, dtype=np.int64)
    if not np.issubdtype(array.dtype, np.integer) or np.issubdtype(array.dtype, np.bool_):
        raise ValueError(f"{name} cells must be integers")
    if np.issubdtype(array.dtype, np.unsignedinteger) and array.size and int(array.max()) > np.iinfo(np.int64).max:
        raise ValueError(f"{name} cell value exceeds the supported signed 64-bit range")
    return array.astype(np.int64, copy=False)


def as_int(value, *, name):
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    value = int(value)
    if not INT64_MIN <= value <= INT64_MAX:
        raise ValueError(f"{name} exceeds signed 64-bit integer range")
    return value


def as_object(obj):
    """Validate a K-VL object dictionary and return its canonical parts."""
    if not isinstance(obj, dict):
        raise ValueError("object must be a dictionary returned by find_objects")
    try:
        color = as_int(obj["color"], name="object color")
        if not isinstance(obj["position"], (list, tuple)) or not isinstance(obj["dimensions"], (list, tuple)):
            raise ValueError("object position and dimensions must be two-item lists or tuples")
        position = tuple(as_int(v, name="object position") for v in obj["position"])
        dimensions = tuple(as_int(v, name="object dimensions") for v in obj["dimensions"])
        if not isinstance(obj["indices"], (list, tuple)):
            raise ValueError("object indices must be a list or tuple of coordinates")
        indices = []
        for point in obj["indices"]:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                raise ValueError("each object coordinate must be a two-item list or tuple")
            indices.append(tuple(as_int(v, name="object coordinate") for v in point))
        try:
            mask = np.asarray(obj["mask"])
        except (TypeError, ValueError) as exc:
            raise ValueError("object mask must be a rectangular 2D binary matrix") from exc
    except (KeyError, TypeError) as exc:
        raise ValueError("object is missing valid color, position, dimensions, indices, or mask") from exc
    if len(position) != 2 or len(dimensions) != 2 or any(v <= 0 for v in dimensions):
        raise ValueError("object position and positive dimensions must each contain two integers")
    if (mask.ndim != 2 or mask.shape != dimensions
            or not (np.issubdtype(mask.dtype, np.integer) or np.issubdtype(mask.dtype, np.bool_))
            or not np.isin(mask, (0, 1)).all()):
        raise ValueError("object mask must be a 2D binary array matching dimensions")
    if not indices:
        raise ValueError("object must contain at least one pixel")
    local_points = np.argwhere(mask == 1)
    if (not local_points.size or local_points[:, 0].min() != 0 or local_points[:, 1].min() != 0
            or local_points[:, 0].max() != dimensions[0] - 1 or local_points[:, 1].max() != dimensions[1] - 1):
        raise ValueError("object mask must have a tight bounding box")
    expected = [(position[0] + int(y), position[1] + int(x)) for y, x in local_points]
    if indices != expected:
        raise ValueError("object indices do not match its position and mask")
    if any(abs(value) > EXACT_DISTANCE_COORD_LIMIT for point in indices for value in point):
        raise ValueError(f"object coordinates must be within +/-{EXACT_DISTANCE_COORD_LIMIT}")
    return color, position, dimensions, indices, mask.astype(bool)


def canonicalize_object(obj):
    """Return a deep-copied object with canonical built-in container types."""
    from copy import deepcopy

    color, position, dimensions, indices, mask = as_object(obj)
    result = deepcopy(obj)
    result["color"] = color
    result["position"] = position
    result["dimensions"] = dimensions
    result["indices"] = [[row, column] for row, column in indices]
    result["mask"] = mask.astype(np.int8).tolist()
    return result
