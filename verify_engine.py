"""Training-example checker for trusted, already-imported solver callables.

This module deliberately does not execute source strings and is not a sandbox.
Model output must be parsed as a restricted DSL by a future dedicated executor.
"""

import json
from collections.abc import Callable
from copy import deepcopy

import numpy as np

from kvl._validation import as_grid


def verify_solution(task_file_path, solve_func: Callable):
    """Check a trusted callable against every training pair in a task JSON file.

    Returns True only when the callable returns an exact integer grid for each
    training input. This establishes training-pair agreement only.
    """
    if not callable(solve_func):
        raise ValueError("solve_func must be a callable; source code strings are never executed")

    with open(task_file_path, "r", encoding="utf-8") as task_file:
        task_data = json.load(task_file)
    examples = task_data.get("train")
    if not isinstance(examples, list) or not examples:
        raise ValueError("task data must contain a non-empty 'train' list")

    print(f"--- Checking callable against {len(examples)} training examples ---")
    for index, example in enumerate(examples, start=1):
        try:
            expected = as_grid(example["output"])
            predicted = as_grid(solve_func(deepcopy(example["input"])))
        except Exception as exc:
            print(f"    [-] Example {index}: invalid input/output or solver error: {exc}")
            return False
        if not np.array_equal(predicted, expected):
            print(f"    [-] Example {index}: output mismatch.")
            return False
        print(f"    [+] Example {index}: passed.")

    print("[SUCCESS] Training examples match. Hidden-input correctness is not established.")
    return True
