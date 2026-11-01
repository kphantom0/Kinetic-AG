"""Contract tests for K-VL's deterministic grid primitives."""

import unittest
from copy import deepcopy
import numpy as np

import kvl


class GridTests(unittest.TestCase):
    def test_dimensions_and_blank_grid(self):
        grid = [[1, 2, 3], [4, 5, 6]]
        self.assertEqual(kvl.get_dimensions(grid), (2, 3))
        self.assertEqual(kvl.create_blank_grid_like(grid, 7), [[7] * 3, [7] * 3])
        self.assertEqual(kvl.get_dimensions([]), (0, 0))
        self.assertEqual(kvl.create_blank_grid_like([]), [])
        with self.assertRaises(ValueError):
            kvl.create_blank_grid(0, 3)
        with self.assertRaises(ValueError):
            kvl.get_dimensions([[1], [2, 3]])
        with self.assertRaises(ValueError):
            kvl.get_dimensions([[1.5]])
        with self.assertRaises(ValueError):
            kvl.get_dimensions([[], []])
        with self.assertRaises(ValueError):
            kvl.paint_onto(np.empty((0, 0), dtype=int), kvl.find_objects([[1]])[0])
        with self.assertRaises(ValueError):
            kvl.create_blank_grid_like([], background_color="bad")
        with self.assertRaises(ValueError):
            kvl.create_blank_grid(1, 1, background_color=1 << 80)
        with self.assertRaises(ValueError):
            kvl.create_blank_grid(10**9, 10**9)
        with self.assertRaises(ValueError):
            kvl.create_blank_grid(4097, 1)
        with self.assertRaises(ValueError):
            kvl.get_dimensions([[1 << 80]])

    def test_find_objects_component_masks_and_connectivity(self):
        grid = [[1, 0, 0, 0, 0], [0, 0, 1, 0, 0], [1, 1, 1, 0, 0]]
        objects = kvl.find_objects(grid)
        self.assertEqual(len(objects), 2)
        self.assertEqual(len(objects[0]["indices"]), 1)
        self.assertEqual(objects[0]["mask"], [[1]])
        self.assertEqual(sum(sum(row) for row in objects[1]["mask"]), 4)
        self.assertEqual(len(kvl.find_objects([[1, 0], [0, 1]], diagonal_connectivity=True)), 1)
        self.assertEqual(len(kvl.find_objects([[1, 0], [0, 1]])), 2)
        self.assertEqual(len(kvl.find_objects([[0, 2]], background_color=2)), 1)
        with self.assertRaises(ValueError):
            kvl.find_objects([], diagonal_connectivity=1)
        with self.assertRaises(ValueError):
            kvl.find_objects([], background_color=1.5)
        base = kvl.find_objects([[1]])[0]
        for invalid_indices in (123, (point for point in [[0, 0]]), [{0: 0, 1: 0}], [{0, 1}], [[0, 0, 0]]):
            broken = deepcopy(base)
            broken["indices"] = invalid_indices
            with self.assertRaises(ValueError):
                kvl.get_com(broken)

    def test_filters_and_centroid(self):
        objects = kvl.find_objects([[1, 1, 0, 2], [1, 0, 0, 2]])
        self.assertEqual(len(kvl.filter_by_color(objects, 1)), 1)
        self.assertEqual(len(kvl.filter_by_size(objects, "largest")), 1)
        self.assertEqual(len(kvl.filter_by_size([], "largest")), 0)
        with self.assertRaises(ValueError):
            kvl.filter_by_size(objects, "middle")
        with self.assertRaises(ValueError):
            kvl.filter_by_size([], "middle")
        malformed = deepcopy(objects[0])
        malformed["indices"] = list(reversed(malformed["indices"]))
        with self.assertRaises(ValueError):
            kvl.filter_by_color([malformed], 1)
        padded = {"color": 1, "position": (0, 0), "dimensions": (3, 3),
                  "mask": [[0,0,0],[0,1,0],[0,0,0]], "indices": [[1,1]]}
        with self.assertRaises(ValueError):
            kvl.get_com(padded)
        float_mask = deepcopy(objects[0]); float_mask["mask"] = [[float(v) for v in row] for row in float_mask["mask"]]
        with self.assertRaises(ValueError):
            kvl.get_com(float_mask)
        self.assertEqual(kvl.get_com(objects[0]), (1 / 3, 1 / 3))
        filtered = kvl.filter_by_color(objects, 1)
        self.assertIsInstance(filtered[0]["position"], tuple)
        self.assertIsInstance(filtered[0]["mask"], list)
        filtered[0]["position"] = [0, 0]
        filtered[0]["mask"][0][0] = 0
        self.assertEqual(objects[0]["mask"][0][0], 1)
        custom = {"color": 1, "position": [0, 0], "dimensions": [1, 2],
                  "mask": ((True, 1),), "indices": ((0, 0), (0, 1))}
        canonical = kvl.recolor(custom, 5)
        self.assertEqual(canonical["position"], (0, 0))
        self.assertEqual(canonical["dimensions"], (1, 2))
        self.assertEqual(canonical["mask"], [[1, 1]])
        self.assertEqual(canonical["indices"], [[0, 0], [0, 1]])
        self.assertIsInstance(custom["position"], list)
        with self.assertRaises(ValueError):
            kvl.get_com({"indices": []})
        for bad_objects in (None, 123, (item for item in objects)):
            with self.assertRaises(ValueError):
                kvl.filter_by_color(bad_objects, 1)
            with self.assertRaises(ValueError):
                kvl.filter_by_size(bad_objects, "largest")

    def test_crop_distance_alignment_overlap(self):
        grid = [[0, 0, 0], [0, 1, 0], [0, 0, 2]]
        crop = kvl.find_crop_area(grid)
        self.assertEqual(crop["cropped_grid"], [[1, 0], [0, 2]])
        self.assertEqual(crop["offset"], (1, 1))
        one, two = kvl.find_objects(grid)
        self.assertEqual(kvl.get_distance(one, two), 2)
        far = 1 << 40
        far_a = {"color": 1, "position": (far, 0), "dimensions": (1, 1), "mask": [[1]], "indices": [[far, 0]]}
        far_b = {"color": 1, "position": (far + 1, 0), "dimensions": (1, 1), "mask": [[1]], "indices": [[far + 1, 0]]}
        self.assertEqual(kvl.get_distance(far_a, far_b), 1)
        too_far = deepcopy(far_b)
        too_far["position"] = (1 << 51, 0); too_far["indices"] = [[1 << 51, 0]]
        with self.assertRaises(ValueError):
            kvl.get_distance(far_a, too_far)
        self.assertEqual(kvl.is_aligned(one, two), {"horizontal": False, "vertical": False})
        self.assertFalse(kvl.has_overlap(one, two)["is_overlapping"])
        collision = kvl.has_overlap(one, kvl.shift(two, (-1, -1)))
        self.assertTrue(collision["is_overlapping"])
        self.assertEqual(collision["collision_pixels"], [(1, 1)])
        self.assertIsNone(kvl.find_crop_area([[0, 0], [0, 0]]))

    def test_transform_contracts(self):
        obj = kvl.find_objects([[1, 1, 0], [1, 0, 0]])[0]
        rotated = kvl.rotate(obj, 90)
        self.assertEqual(rotated["dimensions"], (2, 2))
        self.assertEqual(rotated["mask"], [[1, 1], [0, 1]])
        self.assertEqual(kvl.rotate(obj, 360)["mask"], obj["mask"])
        self.assertEqual(kvl.mirror(obj, "vertical")["mask"], [[1, 1], [0, 1]])
        self.assertEqual(kvl.mirror(obj, "horizontal")["mask"], [[1, 0], [1, 1]])
        with self.assertRaises(ValueError):
            kvl.rotate(obj, 45)
        with self.assertRaises(ValueError):
            kvl.mirror(obj, "diagonal")
        with self.assertRaises(ValueError):
            kvl.shift(obj, (5, 0), canvas_dimensions=(3, 3))
        with self.assertRaises(ValueError):
            kvl.shift(obj, None)
        for bad_dimensions in (123, {3: 3, 4: 4}):
            with self.assertRaises(ValueError):
                kvl.shift(obj, (0, 0), canvas_dimensions=bad_dimensions)
        self.assertEqual(kvl.shift(obj, (1, -2))["position"], (1, -2))

    def test_recolor_paint_and_flood_fill(self):
        obj = kvl.find_objects([[1, 1], [1, 0]])[0]
        changed = kvl.recolor(obj, 5)
        self.assertEqual(changed["color"], 5)
        self.assertEqual(obj["color"], 1)
        canvas = [[0] * 3 for _ in range(3)]
        self.assertEqual(kvl.paint_onto(canvas, kvl.shift(changed, (1, 1))),
                         [[0, 0, 0], [0, 5, 5], [0, 5, 0]])
        self.assertEqual(canvas, [[0] * 3 for _ in range(3)])
        self.assertEqual(kvl.paint_onto([[0, 0]], kvl.shift(changed, (0, -1))), [[5, 0]])
        changed["mask"][0][0] = 0
        self.assertEqual(obj["mask"][0][0], 1)
        grid = [[0, 0, 1], [0, 1, 1]]
        self.assertEqual(kvl.flood_fill_canvas(grid, (0, 0), 2), [[2, 2, 1], [2, 1, 1]])
        self.assertEqual(grid, [[0, 0, 1], [0, 1, 1]])
        with self.assertRaises(ValueError):
            kvl.flood_fill_canvas(grid, (9, 0), 2)

    def test_enclosed_regions_and_background_grid(self):
        grid = [[1, 1, 1, 0, 1, 1, 1], [1, 0, 1, 0, 1, 0, 1], [1, 1, 1, 0, 1, 1, 1]]
        holes = kvl.get_enclosed_regions(grid)
        self.assertEqual(len(holes), 2)
        self.assertTrue(all(hole["is_enclosed_hole"] for hole in holes))
        lattice = [[5, 5, 5, 5], [0, 0, 0, 0], [5, 5, 5, 5], [0, 0, 0, 0]]
        self.assertEqual(kvl.detect_background_grid(lattice)["row_period"], 2)
        self.assertIsNone(kvl.detect_background_grid([[0, 5, 0], [0, 0, 0]]))
        with self.assertRaises(ValueError):
            kvl.detect_background_grid(lattice, threshold=1.1)
        for bad_threshold in (True, "0.7", float("nan")):
            with self.assertRaises(ValueError):
                kvl.detect_background_grid(lattice, threshold=bad_threshold)


if __name__ == "__main__":
    unittest.main()
