# loam-pr-safety

PR-safety gate engine for loam. Reads a v0.1.8-authored banded ODD contract, classifies a git diff against the contract's confidence-banded ACs, and emits a `GateDecision` per the 3-band × 4-shape × 3-profile decision matrix. Composes with `loam-odd-extractor` (banded contract types), `loam-per-project-pm` (override-ratification flow), and `loam-workspace-bootstrap` (`safety_profile` field).

**Cycle 1 (v0.1.9):** engine without delivery wrapping. CLI invocation only (`loam pr-safety gate <repo>`).

**Cycle 2 (v0.1.9):** delivery wrapping. Pre-commit + pre-push hook installers (idempotent + husky-aware + halt-on-conflict) + three CI templates (GitHub Actions / GitLab CI / CircleCI) + provenance-traceable PR description template (auto-populates from gate output + audit-log) + install ergonomics CLI (`loam pr-safety install <surface>`).

**Cycle 3 (v0.1.9):** Six dev-sdlc SKILLs second pass + audit-allowlist cleanup.

## Cycle 2 install surfaces

| CLI verb | Function | Standard target | Husky variant target |
|---|---|---|---|
| `install pre-commit <repo>` | install_pre_commit | `<repo>/.git/hooks/pre-commit` | `<repo>/.husky/pre-commit` |
| `install pre-push <repo>` | install_pre_push | `<repo>/.git/hooks/pre-push` | `<repo>/.husky/pre-push` |
| `install ci github-actions <repo>` | install_ci_github_actions | `<repo>/.github/workflows/loam-pr-safety.yml` | n/a |
| `install ci gitlab-ci <repo>` | install_ci_gitlab_ci | `<repo>/.gitlab-ci.yml` (sentinel-block-delimited region) | n/a |
| `install ci circleci <repo>` | install_ci_circleci | `<repo>/.circleci/config.yml` (sentinel-block-delimited region) | n/a |
| `install pr-template <repo>` | install_pr_template | `<repo>/.github/pull_request_template.md` + `<repo>/.loam/pr-safety/pr_description.template.md` | n/a |
| `install all <repo>` | all above | all above | husky-routed where applicable |

**Idempotency** — every loam-managed file carries a sentinel comment (`# loam-pr-safety:managed:<version>`); re-installs are no-ops at matching version, refresh on version change, halt-on-conflict for non-loam content (use `--force` to replace with backup).

**Husky detection** — pre-commit/pre-push install routes to `.husky/<hook>` when EITHER `<repo>/.husky/_/husky.sh` exists (v6+) OR `<repo>/package.json` has a top-level `"husky"` key (v4-v5). Other hook-managers (`pre-commit` Python, `lefthook`) fall through to standard `.git/hooks/<hook>` install — conflict detection catches collisions.

**Hook-fire dispatcher** — installed hooks invoke `loam pr-safety hook-fire <repo> --hook <name>` which honours `LOAM_PR_SAFETY_BYPASS=1` ONLY under dev/research profiles. Under production-stake the env var is ignored; the bypass attempt is audit-logged. `git commit --no-verify` bypasses loam at the git level (out-of-band; the gate catches it on subsequent push or CI run).

**PR description rendering** — `loam pr-safety gate <repo> --render-pr-description` renders the gate decision + ACs touched + novel candidates + override history + audit-log excerpt as markdown to stdout. CI templates pipe this to `pr-description.md` artefact for upload. Body-overflow strategy: when total exceeds 60,000 chars, deterministic truncation (per-AC provenance trimmed to ~200 chars; audit-log excerpt truncated to last 1 entry; novel-candidates section dropped); truncation footer always cites the workspace audit-log path.

## What this component does

1. **Reads the banded contract.** `<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml` — the odd-extractor's sidecar — is the authority for the repo's confidence-banded ACs. `read_contract` returns a typed `BandedContract`; per-band evidence rules from `loam_odd_extractor.bands.BandedAC` are enforced at read time.

2. **Classifies a diff.** `parse_diff(repo, sha1, sha2)` wraps `git diff --unified=0 --no-color`; `classify(diff, contract)` runs the line-overlap + symbol-overlap heuristic and returns `(touched_acs, untouched, novel)`.

3. **Decides per the 3-band × 4-shape × 3-profile decision matrix.** `decide(classification, safety_profile)` runs the matrix:
   - VERIFIED-touched → HARD-BLOCK (Cycle 1 simplification: VERIFIED-touched ≡ regression-suspect).
   - PLAUSIBLE-touched → SURFACE-DECISION through PM batch (one-question-at-a-time per Decision Q).
   - HYPOTHESISED-touched → DOCS-ONLY annotation.
   - Novel-only → SURFACE-DECISION (offer "promote to PLAUSIBLE / HYPOTHESISED / skip").
   - Pre-emption order: HARD-BLOCK > SURFACE-DECISION > DOCS-ONLY > PASS.

4. **Recognises override commits.** Commits with `contract-update:` subject prefix OR `Loam-Override: <rationale>` trailer trigger the override flow when the `--override` CLI flag is present (Decision I default-no — both commit-shape AND flag required). The override flow ratifies through PM (`RatificationBatch` + `surface_next_questions_batch(n=1)`); approved overrides record an additive overlay at `<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml` (no in-place mutation of the odd-extractor's contract sidecar).

5. **Records every decision in an audit log.** SOC-2 audit-trail floor (Decision P): `<workspace>/.loam/pr-safety/audit-log/<YYYY-MM-DD>-<NNNN>.yaml`. One entry per gate invocation; override flows write three entries (proposed / approved-or-rejected / gate-decision-that-triggered-override).

6. **Honours `safety_profile`.** Under `production-stake`, every SURFACE-DECISION sets `requires_ratification=True` (no auto-pass). Under `dev` / `research`, PLAUSIBLE-touched + novel-only default to `requires_ratification=False` (proceed-with-warning); `--require-ratification` opts in to strict behaviour for a one-off run.

## Cycle 1 scope

| Concern | In scope | Deferred |
|---|---|---|
| CLI (`loam pr-safety gate`) | Yes | — |
| Banded-contract reader | Yes | — |
| Diff classifier | Yes (line + symbol overlap; ≥90% accuracy bar) | AST-aware extension (escape hatch only) |
| Per-band gating engine | Yes (full 3×4×3 decision matrix) | Test-execution integration for VERIFIED-touched |
| Override-commit recognition | Yes (prefix + trailer + flag) | — |
| Override-application | Yes (additive overlay) | In-place sidecar mutation (cross-component) |
| SOC-2 audit log | Yes | — |
| Production-stake integration | Yes | — |
| Pre-commit / pre-push hooks | — | Cycle 2 |
| GitHub Actions / GitLab CI / CircleCI templates | — | Cycle 2 |
| PR description template | — | Cycle 2 |
| 6 dev-sdlc SKILLs second pass | — | Cycle 3 |
| Audit-allowlist cleanup | — | Cycle 3 |
| Continuous codebase-watch | — | v0.2.0+ |
| Eric's actual codebases (real OSS smoke) | — | v0.2.1 fresh-user smoke gate |

## CLI surface

```
loam pr-safety gate <repo>            # gate HEAD vs origin/main (default)
loam pr-safety gate <repo> --diff <sha1>..<sha2>
loam pr-safety gate <repo> --override # opts into override-flow recognition (Decision I)
loam pr-safety gate <repo> --dry-run  # default under production-stake
loam pr-safety gate <repo> --json     # structured output instead of human-readable
loam pr-safety gate <repo> --workspace-root <path>
loam pr-safety gate <repo> --repo-id <id>
loam pr-safety gate <repo> --require-ratification  # forces strict behaviour under dev profile
```

Exit codes: `0` PASS, `2` HARD-BLOCK, `3` SURFACE-DECISION, `4` OVERRIDE-REJECTED, `5` ContractMissing or other PRSafetyError.

## Composition (read-only imports)

- `loam_odd_extractor.bands.{BandedAC, Evidence, ConfidenceBand}` — the banded contract types.
- `loam_odd_extractor.state.compute_repo_id` — same repo-id formula as the extractor (so the gate reads from the right contract).
- `loam.per_project_pm.{PMRuntime, RatificationBatch, PendingResponseError, RecordedResponse}` — override-ratification flow.
- `loam.workspace_bootstrap.load_manifest` — reads `safety_profile` field.

No edits to those upstream components in Cycle 1 — single-component fence on `plugins/dev-sdlc/`.

## Plan-doc

`docs/rebuild/plans/v0-1-9-cycle-1-pr-safety-gate-engine.md` — full AC ladder (`AC.PRSG.1..9`), single-component fence, decision-matrix coverage, halt triggers, F2 RF gaps, provenance trail.
