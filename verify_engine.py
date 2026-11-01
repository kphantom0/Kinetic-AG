"""Training-example checker for trusted callables and the restricted K-VL DSL."""

import json
from collections.abc import Callable
from copy import deepcopy

import numpy as np

from kvl._validation import as_grid
from kvl.dsl import execute_program


def verify_solution(task_file_path, solve_func: Callable | dict):
    """Check a trusted callable or DSL program against each training pair.

    Returns True only when the callable returns an exact integer grid for each
    training input. This establishes training-pair agreement only.
    """
    if not callable(solve_func) and not isinstance(solve_func, dict):
        raise ValueError("solve_func must be a callable or a JSON SSA program dictionary")

    with open(task_file_path, "r", encoding="utf-8") as task_file:
        task_data = json.load(task_file)
    examples = task_data.get("train")
    if not isinstance(examples, list) or not examples:
        raise ValueError("task data must contain a non-empty 'train' list")

    print(f"--- Checking callable against {len(examples)} training examples ---")
    for index, example in enumerate(examples, start=1):
        try:
            expected = as_grid(example["output"])
            if isinstance(solve_func, dict):
                predicted_grid, _ = execute_program(solve_func, deepcopy(example["input"]))
            else:
                predicted_grid = solve_func(deepcopy(example["input"]))
            predicted = as_grid(predicted_grid)
        except Exception as exc:
            print(f"    [-] Example {index}: invalid input/output or solver error: {exc}")
            return False
        if not np.array_equal(predicted, expected):
            print(f"    [-] Example {index}: output mismatch.")
            return False
        print(f"    [+] Example {index}: passed.")

    print("[SUCCESS] Training examples match. Hidden-input correctness is not established.")
    return True
