# Kinetic-AG

**A research prototype for model-guided visual-spatial reasoning with deterministic grid operations.**

Kinetic-AG explores a neuro-symbolic approach to ARC-style puzzles and related visual tasks. An AI model is intended to propose symbolic operations; K-VL, the Kinetic Visual Language library, applies those operations to discrete grids with explicit, testable semantics.

The project is being rebuilt from an early AI-assisted prototype. The repository contains the K-VL core and an early bounded JSON DSL executor. It does not yet include a model adapter or a complete ARC task-solving system. The implementation remains experimental and is not claimed to be production-ready.

## Current K-VL capabilities

- Validate integer grids and object records.
- Extract monochrome connected components with four-way or eight-way connectivity.
- Measure object centroids, Manhattan distance, bounding-box alignment, and pixel overlap.
- Crop, shift, rotate, and mirror object masks.
- Recolor and paint objects, detect enclosed regions, and flood-fill connected areas.
- Execute an allowlisted SSA-style JSON program with deterministic resource budgets and step traces.

These operations are deterministic under their implemented inputs. Some helpers, including dense-line grid detection, are heuristics and do not establish semantic truth about a puzzle.

## Development status

Run the unit and property-based suites to check the current implementation. Passing tests cover only the tested cases and do not establish general ARC-solving ability. The local ARC-AGI-2 copy is reserved for a later held-out benchmark; no benchmark result is claimed here.

```powershell
python -m pip install -e ".[dev]"
python -m unittest -v test_kvl_unit test_kvl_properties
```

The print-based `test_kvl.py` and `test_master_kvl.py` scripts are illustrative diagnostics, not substitutes for the unit suite. Local engineering contracts, review packets, change logs, and dataset copies are intentionally not part of the public repository.

## Safety and roadmap

The verifier accepts trusted callables only and is not a sandbox. The DSL executor validates a JSON program and dispatches only allowlisted operations; model-produced Python must never be executed. Continue hardening validation, resource limits, semantics, tests, packaging, and CI before model integration or ARC-AGI-2 evaluation.

## AI assistance

This project has been developed with AI coding assistance. Changes are treated as proposals and checked against tests and the local contract. Passing tests do not prove general ARC-solving ability.
