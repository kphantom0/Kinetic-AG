# Kinetic-AG contributor instructions

These instructions apply to the whole repository.

## Project goals and status

- Kinetic-AG is a neuro-symbolic visual reasoning project. An AI model proposes discrete K-VL operations; deterministic library code validates and executes them.
- Treat K-VL correctness, explicit semantics, bounded resource use, and stable public behavior as the priority.
- The repository is experimental. Do not describe it as production-ready or claim general ARC-solving ability without evidence.
- Local ARC-AGI-2 copies are held out for later evaluation. Do not use them for routine development, tuning, or quality claims until the user explicitly starts that benchmark phase.

## Change workflow

1. Inspect the relevant implementation, public exports, contract, tests, and repository status before editing. Treat AI-generated or legacy code as unverified.
2. Prefer the smallest change that resolves the demonstrated defect. Preserve documented behavior unless a contract change is deliberate and reviewed.
3. Keep the public API deterministic. Validate untrusted inputs at the boundary, avoid silent coercion, bound allocations and work, and do not execute model-produced Python or shell code.
4. Add or update focused regression/property tests for behavior changes. Run the relevant existing tests and report the exact commands and outcomes; never claim checks that were not run.
5. For every code or project change, create a separate dated `.txt` traceability log under `Kinetic-AG Database/Fixed Issues/`. Include date, purpose, affected files, behavior/risk, and verification. These logs are local records and must not be committed.
6. Review the final diff for accidental dataset, generated, local-review, credential, or unrelated files before committing or opening a PR.

## Repository hygiene

- Keep `Kinetic-AG Database/`, ARC dataset copies, audit outputs, source snapshots, private contracts, external review packets, and local notes out of GitHub. Preserve the ignore rules that cover them.
- Never commit secrets. If a credential is exposed, tell the user to revoke/rotate it; removing it from the current tree or rewriting a branch does not invalidate it or guarantee erasure from clones and caches.
- Do not weaken validation, resource limits, or tests merely to make a check pass. Explain any unavoidable compatibility or semantic tradeoff.
- For substantial architecture decisions, document alternatives and evidence and invite the user's requested external engineering review before treating the design as settled.

## Testing and benchmark boundaries

- Core unit and property-based tests are the normal correctness checks. Keep independent reference-oracle comparisons where useful.
- ARC dataset evaluation is a distinct later phase. Do not report parsing, object extraction, or a smoke test as task-solving performance.
- Include limitations, skipped checks, and dependency requirements in handoffs and pull request descriptions.
