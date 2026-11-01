"""Property-based, differential, and exhaustive model tests for K-VL."""

import itertools
import unittest
from copy import deepcopy

from hypothesis import given, settings, strategies as st

import kvl
from kvl._oracle_ref import ref_find_objects, ref_get_distance, ref_get_enclosed_regions


@st.composite
def valid_grids(draw, min_side=1, max_side=12, min_color=0, max_color=5):
    height = draw(st.integers(min_value=min_side, max_value=max_side))
    width = draw(st.integers(min_value=min_side, max_value=max_side))
    return draw(
        st.lists(
            st.lists(st.integers(min_value=min_color, max_value=max_color), min_size=width, max_size=width),
            min_size=height,
            max_size=height,
        )
    )


class PropertyAndDifferentialTests(unittest.TestCase):
    @settings(max_examples=250, deadline=None)
    @given(grid=valid_grids(), diag=st.booleans(), bg=st.integers(min_value=0, max_value=2))
    def test_differential_find_objects_and_partition(self, grid, diag, bg):
        snapshot = deepcopy(grid)
        actual = kvl.find_objects(grid, diagonal_connectivity=diag, background_color=bg)
        expected = ref_find_objects(grid, diagonal_connectivity=diag, background_color=bg)
        self.assertEqual(actual, expected)
        self.assertEqual(grid, snapshot)

        height, width = kvl.get_dimensions(grid)
        all_coords = {(row, column) for row in range(height) for column in range(width)}
        bg_coords = {
            (row, column)
            for row in range(height)
            for column in range(width)
            if grid[row][column] == bg
        }
        object_coords = set()
        for obj in actual:
            points = {tuple(point) for point in obj["indices"]}
            self.assertTrue(object_coords.isdisjoint(points))
            object_coords |= points
        self.assertEqual(object_coords | bg_coords, all_coords)

    @settings(max_examples=200, deadline=None)
    @given(grid=valid_grids(), bg=st.integers(min_value=0, max_value=2))
    def test_differential_enclosed_regions(self, grid, bg):
        self.assertEqual(
            kvl.get_enclosed_regions(grid, background_color=bg),
            ref_get_enclosed_regions(grid, background_color=bg),
        )

    @settings(max_examples=200, deadline=None)
    @given(
        grid=valid_grids(min_color=0, max_color=3),
        dy=st.integers(min_value=-20, max_value=20),
        dx=st.integers(min_value=-20, max_value=20),
        new_color=st.integers(min_value=0, max_value=9),
    )
    def test_algebraic_laws_on_objects(self, grid, dy, dx, new_color):
        objects = kvl.find_objects(grid)
        if not objects:
            return
        obj = objects[0]
        self.assertEqual(kvl.mirror(kvl.mirror(obj, "vertical"), "vertical"), obj)
        self.assertEqual(kvl.mirror(kvl.mirror(obj, "horizontal"), "horizontal"), obj)
        self.assertEqual(kvl.rotate(kvl.rotate(obj, 90), 270), obj)
        self.assertEqual(kvl.shift(kvl.shift(obj, (dy, dx)), (-dy, -dx)), obj)
        self.assertEqual(
            kvl.shift(kvl.recolor(obj, new_color), (dy, dx)),
            kvl.recolor(kvl.shift(obj, (dy, dx)), new_color),
        )
        if len(objects) >= 2:
            self.assertEqual(
                kvl.get_distance(objects[0], objects[1]),
                ref_get_distance(objects[0], objects[1]),
            )

    def test_exhaustive_4x4_binary_grids(self):
        """Exhaustively verify all 2^16 binary 4x4 grids against the Python oracle."""
        for bits in itertools.product((0, 1), repeat=16):
            grid = [list(bits[row * 4:(row + 1) * 4]) for row in range(4)]
            self.assertEqual(kvl.find_objects(grid), ref_find_objects(grid))
            self.assertEqual(kvl.get_enclosed_regions(grid), ref_get_enclosed_regions(grid))


if __name__ == "__main__":
    unittest.main()
