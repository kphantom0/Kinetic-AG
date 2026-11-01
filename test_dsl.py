"""Contract checks for the bounded K-VL JSON DSL executor."""

import unittest
from copy import deepcopy

from kvl.dsl import ExecutionBudget, KVLExecutionError, execute_program


class DSLExecutionTests(unittest.TestCase):
    def test_find_and_paint_round_trip_is_deterministic_and_non_mutating(self):
        grid = [[0, 2, 0], [0, 2, 2]]
        original = deepcopy(grid)
        program = {
            "dsl_version": "0.1",
            "steps": [
                {"bind": "objects", "op": "find_objects", "args": {"grid": "$in"}},
                {
                    "bind": "canvas",
                    "op": "create_blank_grid_like",
                    "args": {"grid": "$in", "background_color": 0},
                },
                {
                    "bind": "result",
                    "op": "paint_all",
                    "args": {"canvas": "$canvas", "objects": "$objects"},
                },
            ],
            "output": "$result",
        }

        result, traces = execute_program(program, grid)

        self.assertEqual(result, grid)
        self.assertEqual(grid, original)
        self.assertEqual([trace.op for trace in traces], ["find_objects", "create_blank_grid_like", "paint_all"])
        self.assertEqual(len({trace.state_hash for trace in traces}), 3)

    def test_unknown_operation_is_rejected(self):
        program = {
            "dsl_version": "0.1",
            "steps": [{"bind": "x", "op": "python", "args": {}}],
            "output": "$x",
        }
        with self.assertRaisesRegex(KVLExecutionError, "not in ALLOWED_OPS") as caught:
            execute_program(program, [[1]])
        self.assertEqual(caught.exception.code, "UNKNOWN_OP")

    def test_step_budget_is_enforced(self):
        program = {
            "dsl_version": "0.1",
            "steps": [
                {"bind": "canvas", "op": "create_blank_grid_like", "args": {"grid": "$in"}},
                {"bind": "again", "op": "create_blank_grid_like", "args": {"grid": "$in"}},
            ],
            "output": "$again",
        }
        with self.assertRaises(KVLExecutionError) as caught:
            execute_program(program, [[1]], ExecutionBudget(max_steps=1))
        self.assertEqual(caught.exception.code, "STEP_LIMIT_EXCEEDED")
        self.assertEqual(caught.exception.step_index, 1)


if __name__ == "__main__":
    unittest.main()
