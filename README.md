# Kinetic-AG

**A research prototype for model-guided visual-spatial reasoning with deterministic grid operations.**

Kinetic-AG explores a neuro-symbolic approach to ARC-style puzzles and related visual tasks. An AI model is intended to propose symbolic operations; K-VL, the Kinetic Visual Language library, applies those operations to discrete grids with explicit, testable semantics.

The project is being rebuilt from an early AI-assisted prototype. The current repository focuses on the K-VL foundation: grid validation, connected-component extraction, spatial measurements, transformations, and rendering. It does not yet include the planned restricted DSL executor, model adapter, or ARC task-solving system. The current implementation and contract are experimental and should not be described as production-ready.

## Current K-VL operations

- Validate integer grids and object records.
- Extract monochrome connected components with four-way or eight-way connectivity.
- Measure object centroids, Manhattan distance, bounding-box alignment, and pixel overlap.
- Crop, shift, rotate, and mirror object masks.
- Recolor and paint objects, detect enclosed regions, and flood-fill connected areas.

These operations are deterministic under their documented inputs. Some helpers, including dense-line grid detection, are heuristics and do not establish semantic truth about a puzzle.

## Run locally

Python 3.12 with NumPy and SciPy is the currently exercised environment. Install the runtime dependencies, then run the contract tests:

```powershell
python -m pip install numpy scipy
python -m unittest -v test_kvl_unit
```

The print-based `test_kvl.py` and `test_master_kvl.py` scripts are illustrative diagnostics, not a substitute for the unit suite.

## Safety and roadmap

The legacy Python `exec` verifier has been replaced by a checker that accepts trusted callables only. It is not a sandbox. The intended model boundary is a future validated JSON DSL interpreted by a bounded, allowlisted executor; model-produced Python must not be executed.

Near-term engineering work is to deepen contract testing, settle enclosure and transform semantics, establish packaging and CI, and then design the DSL executor. Model integration and ARC-AGI-2 evaluation come after those foundations.

## AI assistance

This project has been developed with AI coding assistance. Changes are treated as proposals and checked against the written contract and tests; passing tests cover only the implemented cases and do not prove general ARC-solving ability.
