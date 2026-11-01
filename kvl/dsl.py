"""Deterministic, resource-budgeted SSA DSL executor for Kinetic-AG."""

from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any

import kvl
from kvl._validation import as_grid, as_int, as_object


class KVLExecutionError(ValueError):
    """Structured error raised during DSL validation or execution."""

    def __init__(
        self,
        code: str,
        message: str,
        step_index: int | None = None,
        op: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.step_index = step_index
        self.op = op

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.code,
            "message": self.message,
            "step_index": self.step_index,
            "op": self.op,
        }


@dataclass
class ExecutionBudget:
    """Deterministic execution limits and counters."""

    max_steps: int = 64
    max_grid_dim: int = 128
    max_objects_per_list: int = 256
    max_pixel_work: int = 500_000
    consumed_steps: int = 0
    consumed_pixel_work: int = 0

    def charge(self, pixel_work: int, step_index: int, op: str) -> None:
        self.consumed_steps += 1
        self.consumed_pixel_work += max(1, int(pixel_work))
        if self.consumed_steps > self.max_steps:
            raise KVLExecutionError(
                "STEP_LIMIT_EXCEEDED", "Program exceeded max_steps", step_index, op
            )
        if self.consumed_pixel_work > self.max_pixel_work:
            raise KVLExecutionError(
                "WORK_LIMIT_EXCEEDED", "Program exceeded max_pixel_work", step_index, op
            )


@dataclass(frozen=True)
class StepTrace:
    step_index: int
    bind: str
    op: str
    value_type: str
    state_hash: str
    summary: dict[str, Any] = field(default_factory=dict)


def _hash_and_summarize(value: Any) -> tuple[str, str, dict[str, Any]]:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()[:16]
    if isinstance(value, dict) and "mask" in value and "indices" in value:
        return "Object", digest, {
            "color": value["color"],
            "position": list(value["position"]),
            "mass": len(value["indices"]),
        }
    if isinstance(value, list) and value and isinstance(value[0], dict) and "mask" in value[0]:
        return "ObjectList", digest, {
            "count": len(value),
            "colors": sorted({obj["color"] for obj in value}),
        }
    if isinstance(value, list) and (not value or isinstance(value[0], list)):
        dimensions = kvl.get_dimensions(value) if value else (0, 0)
        return "Grid", digest, {"dimensions": list(dimensions)}
    return type(value).__name__, digest, {"value": value}


def _dsl_select_index(objects: list[dict[str, Any]], index: int) -> dict[str, Any]:
    if not isinstance(objects, (list, tuple)) or not objects:
        raise ValueError("select_index requires a non-empty object list")
    object_index = as_int(index, name="index")
    if not -len(objects) <= object_index < len(objects):
        raise ValueError("object index out of range")
    obj = objects[object_index]
    as_object(obj)
    return kvl.recolor(obj, obj["color"])


def _dsl_paint_all(canvas: list[list[int]], objects: list[dict[str, Any]]) -> list[list[int]]:
    if not isinstance(objects, (list, tuple)):
        raise ValueError("objects must be a list or tuple")
    out = as_grid(canvas, allow_empty=False).tolist()
    for obj in objects:
        out = kvl.paint_onto(out, obj)
    return out


def _dsl_map_shift(
    objects: list[dict[str, Any]], vector: list[int] | tuple[int, int]
) -> list[dict[str, Any]]:
    if not isinstance(objects, (list, tuple)):
        raise ValueError("objects must be a list or tuple")
    return [kvl.shift(obj, vector) for obj in objects]


def _dsl_map_recolor(objects: list[dict[str, Any]], new_color: int) -> list[dict[str, Any]]:
    if not isinstance(objects, (list, tuple)):
        raise ValueError("objects must be a list or tuple")
    return [kvl.recolor(obj, new_color) for obj in objects]


ALLOWED_OPS = MappingProxyType(
    {
        "find_objects": kvl.find_objects,
        "filter_by_color": kvl.filter_by_color,
        "filter_by_size": kvl.filter_by_size,
        "get_com": kvl.get_com,
        "get_enclosed_regions": kvl.get_enclosed_regions,
        "get_dimensions": kvl.get_dimensions,
        "create_blank_grid": kvl.create_blank_grid,
        "create_blank_grid_like": kvl.create_blank_grid_like,
        "get_distance": kvl.get_distance,
        "is_aligned": kvl.is_aligned,
        "detect_background_grid": kvl.detect_background_grid,
        "find_crop_area": kvl.find_crop_area,
        "has_overlap": kvl.has_overlap,
        "shift": kvl.shift,
        "rotate": kvl.rotate,
        "mirror": kvl.mirror,
        "recolor": kvl.recolor,
        "paint_onto": kvl.paint_onto,
        "flood_fill_canvas": kvl.flood_fill_canvas,
        "select_index": _dsl_select_index,
        "paint_all": _dsl_paint_all,
        "map_shift": _dsl_map_shift,
        "map_recolor": _dsl_map_recolor,
    }
)


def execute_program(
    program: dict[str, Any],
    input_grid: list[list[int]],
    budget: ExecutionBudget | None = None,
) -> tuple[list[list[int]], list[StepTrace]]:
    """Validate and execute a JSON SSA program deterministically over input_grid."""
    budget = budget or ExecutionBudget()
    validated_input = as_grid(input_grid, allow_empty=False)
    height, width = (int(value) for value in validated_input.shape)
    if height > budget.max_grid_dim or width > budget.max_grid_dim:
        raise KVLExecutionError(
            "BOUNDS_ERROR", f"Input grid exceeds max_grid_dim ({budget.max_grid_dim})"
        )
    if not isinstance(program, dict) or program.get("dsl_version") != "0.1":
        raise KVLExecutionError("SCHEMA_ERROR", "Program must be a dict with dsl_version == '0.1'")
    steps = program.get("steps")
    output_ref = program.get("output")
    if not isinstance(steps, list) or not steps or not isinstance(output_ref, str):
        raise KVLExecutionError(
            "SCHEMA_ERROR", "Program requires a non-empty 'steps' list and 'output' ref"
        )

    env: dict[str, Any] = {"$in": validated_input.tolist()}
    traces: list[StepTrace] = []

    def resolve(argument: Any, step_index: int, op_name: str) -> Any:
        if isinstance(argument, str) and argument.startswith("$"):
            if argument not in env:
                raise KVLExecutionError(
                    "UNDEFINED_VAR", f"Unknown variable reference '{argument}'", step_index, op_name
                )
            return env[argument]
        return argument

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise KVLExecutionError("SCHEMA_ERROR", "Each step must be a dictionary", index)
        bind = step.get("bind")
        op_name = step.get("op")
        raw_args = step.get("args", {})
        if not isinstance(bind, str) or not bind.isidentifier() or f"${bind}" in env:
            raise KVLExecutionError(
                "SSA_VIOLATION", f"Invalid or duplicate SSA binding '{bind}'", index, str(op_name)
            )
        if not isinstance(op_name, str) or op_name not in ALLOWED_OPS:
            raise KVLExecutionError(
                "UNKNOWN_OP", f"Operation '{op_name}' is not in ALLOWED_OPS", index, str(op_name)
            )
        if not isinstance(raw_args, dict) or any(not isinstance(key, str) for key in raw_args):
            raise KVLExecutionError("SCHEMA_ERROR", "'args' must be a keyword dictionary", index, op_name)
        resolved_kwargs = {
            key: resolve(value, index, op_name) for key, value in raw_args.items()
        }

        if op_name == "create_blank_grid":
            blank_height = as_int(resolved_kwargs.get("height", 0), name="height")
            blank_width = as_int(resolved_kwargs.get("width", 0), name="width")
            if blank_height > budget.max_grid_dim or blank_width > budget.max_grid_dim:
                raise KVLExecutionError(
                    "BOUNDS_ERROR", "Requested blank grid exceeds max_grid_dim", index, op_name
                )
        for value in resolved_kwargs.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                if len(value) > budget.max_objects_per_list:
                    raise KVLExecutionError(
                        "RESOURCE_LIMIT", "Object list exceeds max_objects_per_list", index, op_name
                    )

        try:
            result = ALLOWED_OPS[op_name](**resolved_kwargs)
        except KVLExecutionError:
            raise
        except Exception as exc:
            raise KVLExecutionError("OP_EXECUTION_ERROR", str(exc), index, op_name) from exc

        if (
            isinstance(result, list)
            and result
            and isinstance(result[0], dict)
            and len(result) > budget.max_objects_per_list
        ):
            raise KVLExecutionError(
                "RESOURCE_LIMIT", "Object list exceeds max_objects_per_list", index, op_name
            )
        budget.charge(height * width, index, op_name)
        env[f"${bind}"] = result
        value_type, digest, summary = _hash_and_summarize(result)
        traces.append(StepTrace(index, f"${bind}", op_name, value_type, digest, summary))

    if output_ref not in env:
        raise KVLExecutionError(
            "UNDEFINED_VAR", f"Output reference '{output_ref}' was never bound"
        )
    try:
        final_grid = as_grid(env[output_ref], allow_empty=False).tolist()
    except Exception as exc:
        raise KVLExecutionError("OUTPUT_TYPE_ERROR", "Program output must be a non-empty grid") from exc
    return final_grid, traces
