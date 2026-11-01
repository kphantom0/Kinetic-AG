"""Self-contained demonstration of exact training-pair checking."""

import json
import os
import tempfile

import verify_engine


def deliberately_wrong_solver(grid):
    return [[0 for _ in row] for row in grid]


task = {
    "train": [
        {"input": [[1, 2], [2, 1]], "output": [[2, 1], [1, 2]]},
        {"input": [[3]], "output": [[3]]},
    ]
}

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as task_file:
    json.dump(task, task_file)
    task_path = task_file.name

print("=== Running callable verification demo with intentionally wrong logic ===")
try:
    print(f"Verification verdict: {verify_engine.verify_solution(task_path, deliberately_wrong_solver)}")
finally:
    os.unlink(task_path)
