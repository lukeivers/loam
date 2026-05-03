# FBE.4 sub-plan — In-tree resolution via `install-from-source.{txt,md}` (Path B + fence-three-no-edit)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.4 row in §1 + AC ladder in §4 + §8 register).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.1 sealed at `21b9480`; FBE.2 sealed at `8d2b770`; FBE.7 sealed at `a102bde`; FBE.3 sealed at `becf183`.
**BASELINE (pre-build tip):** `d645ed5` — current canonical pos-v2 HEAD (the FBE.3 §8-backfill commit).

---

## 1. Summary / TLDR

The parent plan's Decision C2 (rewrite 16 inter-component bare-name deps as `<name> @ file://${PROJECT_ROOT}/<comp>` path-specs) is **non-functional on pip 26.0.1** — empirically verified at the prior FBE.4 dispatch (status file `<workspace>/.scratch/claude-output/fbe4-status-2026-05-03.md`, Probes 1–7). The dispatcher has ruled **Path B + fence-three-no-edit**:

- Bare-name inter-component deps STAY in `framework/workspace-bootstrap/pyproject.toml` (12 deps), `plugins/dev-sdlc/pyproject.toml` (3 deps), `framework/loam-init/pyproject.toml` (1 dep). **Zero edits to those pyprojects.**
- A NEW top-level file `install-from-source.txt` carries ordered `-e ./<comp>` lines that pip walks in order; later bare-name deps are satisfied by earlier editable installs in the same `pip install -r` invocation.
- A NEW doc `docs/install-from-source.md` describes the install path in prose + names the one-command shortcut.
- The three sealed components (`workspace-bootstrap`, `dev-sdlc`, `loam-init`) bump their sidecars to record FBE.4's architectural ratification ("deps stay bare-name; in-tree resolution lives in install-from-source.{txt,md}") — pyproject content stays byte-identical.

This is a strict superset of parent plan Decision C3 (per-component install order doc). It preserves the parent plan's stranger-perspective intent (no PyPI 404 on first install) without depending on pip's `${PROJECT_ROOT}` substitution, which pip 26.0 narrowed from earlier behaviour.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; pip 26.0.1 empirically rejects parent plan's Decision C2 path-spec form)

The prior dispatch verified five `pip install --dry-run` rejections against pip 26.0.1 / Python 3.13.12 (the build-machine shipping versions). Documented in `<workspace>/.scratch/claude-output/fbe4-status-2026-05-03.md` Probes 1–5:

- `${PROJECT_ROOT}` in `[project.dependencies]` → `ValueError: non-local file URIs are not supported on this platform`.
- `${PROJECT_ROOT}` in `requirements.txt` → same `ValueError` (pip 26.0 narrowed substitution to `pip freeze --all` output only).
- `file:../a` relative in `[project.dependencies]` → resolves relative to CWD, not the pyproject's directory; broken.
- `file:///abs/...` works but isn't portable across machines.
- `[tool.uv.sources]` ignored by pip.

Two paths verified working (Probes 6 + 7 in the same status file): per-component install order (Path A); `pip install -r install-from-source.txt` walking ordered `-e` lines (Path B). Path B is the dispatcher's chosen path.

This surface is recorded as the empirical anchor that justifies tightening AC.FBE.4.{1,2,3} away from the parent plan's path-spec language and dropping AC.FBE.4.5 entirely (no `${PROJECT_ROOT}` mechanism).

### Surface #2 (no halt — recorded; sealed-component fence preserves audit trail without source edits)

The dispatcher ruled **fence-three-no-edit** over fence-zero. Trade-off: three sidecar bumps + one apply commit + one seal commit cost ~5 min of bookkeeping overhead, in exchange for an explicit audit-trail entry recording that FBE.4's architectural decision was "ratify bare-name deps as the v0.1.0 shape; in-tree resolution lives in install-from-source.{txt,md}". Mirrors FBE.6's seal-without-source-edit pattern (per parent plan §4 FBE.6.S "Sealed-component fence: NONE — this is a sweep + smoke + review amendment with no source-side delta") but applied with three-sidecar fence to record a substantive amendment-trail decision rather than a null-delta sweep.

### Surface #3 (no halt — recorded; v0.2 PyPI publish gate)

The dispatcher captured "v0.2 PyPI publish gate — once components publish, install-from-source.txt becomes optional rather than primary; README entry-point switches to `pip install loam-cli loam-init loam-workspace-bootstrap loam-plugin-dev-sdlc`" to FIDRAFT. Out of FBE.4 scope; recorded here for traceability.

### Surface #4 (no halt — recorded; install-order is topological)

Pip walks `-r requirements.txt` lines in declaration order. Each `-e ./<comp>` install registers the package + its console-scripts before the next line is processed. Bare-name inter-component deps in later lines hit the already-installed wheel first (bypassing PyPI lookup), so PyPI 404s are avoided.

Topological order for the four components:
1. `framework/tools/loam` — depends only on `PyYAML>=6` (no inter-component dep). Installs first to make the `loam` console-script available.
2. `framework/workspace-bootstrap` — depends on 12 inter-component packages (none of which appear in this list yet); but those 12 components are NOT in install-from-source.txt because they're individual sub-components of the framework, not user-visible install targets at v0.1.0 stranger-clone time. The bare-name deps will fail PyPI lookup on dry-run but the smoke verification approach acknowledges this — see §6 Smoke verification.
3. `framework/loam-init` — depends on `loam-workspace-bootstrap` (now installed).
4. `plugins/dev-sdlc` — depends on `loam-scope-of-work`, `loam-objective-tracker`, `loam-workspace-bootstrap` (third now satisfied; first two are again bare-name PyPI-future).

**Updated reading after empirical re-check:** the smoke can NOT pass `--dry-run` cleanly without ALSO installing the underlying components (`loam-scope-of-work`, `loam-objective-tracker`, `loam-orchestrator`, etc.). Either (a) the install-from-source.txt enumerates ALL 15+ components (workspace-bootstrap deps + dev-sdlc deps + loam-init dep), or (b) the file enumerates only the 4 user-visible entry points and the doc explicitly says "this command depends on PyPI publishing for transitive deps; v0.1.0 stranger-clone needs manual per-component install of dependent components".

**Build-time decision:** enumerate ALL components topologically — see §6 Smoke verification. The full ordered list appears in §4 AC.FBE.4.2 below.

### Surface #5 (no halt — recorded; install-from-source.txt is at REPO ROOT, NOT under a directory)

The prior dispatch's path-spec C2 approach would have lived inside individual pyproject.toml files (per-component). Path B's `install-from-source.txt` lives at canonical pos-v2 repo root (alongside README.md, LICENSE, etc.). Manifest admission via `universal_paths.files: [install-from-source.txt]` — a NEW file at repo root needs explicit admission since the partition manifest defaults to `dev_only` for un-admitted top-level files.

The actual partition admission for shipping the file in synth tree is governed by `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` — a separate concern from `loam amend`'s manifest admission. **For v0.1.0 the file MUST also be admitted to the synth pipeline as `dev_and_public`** so strangers cloning the synth get it. This is potentially in-fence (touches the partition manifest, which is owned by `framework/tools/pos-publish-framework-only/`).

**Decision (autonomous, builder's call):** add the partition-manifest admission as part of FBE.4's source-side delta. The partition manifest is an authored data file, not within any of the three named-fence components, but FBE.{2,3} both touched it through the `pos-publish-framework-only` sidecar. **Verify at build time** whether `pos-publish-framework-only` is part of the FBE.4 fence per the dispatcher's "fence-three-no-edit" ruling. If yes, that's a fourth component (fence-four). If no, the partition admission is still needed but happens via universal_paths admission of the `publish-mode-manifest.yaml` file path.

**Resolution after re-reading dispatch:** the dispatcher named THREE components in the fence: workspace-bootstrap + dev-sdlc + loam-init. NO mention of `pos-publish-framework-only`. So:
- Either skip the partition admission (let the file ship via partition default — but default is `dev_only`, breaking the smoke for stranger-clone)
- OR admit the partition manifest edit via `universal_paths.files` (admitting `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` as a per-amendment universal admission, mirroring `CLAUDE.md` / `docs/odd-in-loam.md` precedent in the FBE.7 manifest).

**Builder's call:** admit `publish-mode-manifest.yaml` and `docs/install-from-source.md` and `install-from-source.txt` via `universal_paths.files` for FBE.4 only. This adds one line to the partition manifest (`path: install-from-source.txt` under `dev_and_public:`) and one line for the docs file (`path: docs/install-from-source.md` under `dev_and_public:`). Document this in the manifest YAML provenance.

If `loam amend apply` rejects this admission shape (e.g. `extra_allowed_files` inside a component is the only allowed mechanism, not a per-amendment universal_paths.files) → halt + surface; that's an FBE.4 manifest-shape question.

### Surface #6 (no halt — recorded; smoke verification scope)

The dispatch acceptance criterion #4 says "Smoke: `pip install --dry-run -r install-from-source.txt` from canonical resolves clean (no PyPI 404s on inter-component deps)." With the topological ordering of all 16+ components, dry-run pip will:

1. Walk lines top-to-bottom.
2. For each `-e ./<comp>` line, attempt to resolve its declared deps.
3. Bare-name deps that match an EARLIER `-e ./<comp>` line in the same file are satisfied by the in-progress install set (pip's resolver tracks them in-memory per `pip install -r` invocation).
4. The smoke is the verification.

If the smoke fails on dry-run (e.g. pip's --dry-run path doesn't see the in-flight installs and tries PyPI), this is an FBE.4 halt-and-surface — it would mean `pip install -r install-from-source.txt` (without dry-run) would also need a fundamentally different shape. Per the prior status's Probe 7, this works for the two-component synthetic fixture; full-scale verification at build time.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — closing the "stranger clones the repo and `pip install -e workspace-bootstrap` hits PyPI 404 on `loam-orchestrator`" failure mode that the M11a-3 reviewer flagged as BLOCKER 3.
- **Reviewer foldback BLOCKER 3** (per parent plan §2.3) — "pip deps don't resolve". FBE.4 closes the resolution path without requiring PyPI publish (deferred to v0.2 per FUTURE_IDEAS gate).
- **AC.FBE.4.* tightened from parent plan §4 FBE.4 row** — the parent's path-spec language is replaced by Path B's requirements-file + doc shape (justified empirically per Surface #1).

**Ladders to:** AC.FBE.4.* → AC.OSS-M11a.* (FBE.6 reviewer GO) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.4.*)

AC family `AC.FBE.4.*` — collision-safe (verified: existing AC.FBE.4 entries in parent plan are tightened/dropped/rewritten per the dispatcher ruling and per parent plan §6 Risk #9 force-replan trigger 4 — "pip path-spec doesn't work cross-platform → FBE.4 rewrites to Decision C3").

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.4.1** (rewritten) | `framework/workspace-bootstrap/pyproject.toml`'s 12 inter-component deps are PRESERVED as bare-name strings (byte-identical to BASELINE). The in-tree resolution mechanism for these deps in stranger-clone v0.1.0 install is `install-from-source.txt` + `docs/install-from-source.md`, NOT pyproject path-specs. | `git diff BASELINE..SEAL_COMMIT -- framework/workspace-bootstrap/pyproject.toml` is empty. |
| **AC.FBE.4.2** (rewritten) | `plugins/dev-sdlc/pyproject.toml`'s 3 inter-component deps + `framework/loam-init/pyproject.toml`'s 1 inter-component dep are PRESERVED as bare-name strings. | `git diff BASELINE..SEAL_COMMIT -- plugins/dev-sdlc/pyproject.toml framework/loam-init/pyproject.toml` is empty. |
| **AC.FBE.4.3** (rewritten) | A NEW file `install-from-source.txt` at canonical pos-v2 repo root carries ordered `-e ./<path>` lines covering every component a stranger needs to install for fresh-clone v0.1.0 to work end-to-end. Order is topological: leaves first, then components that depend on leaves, then user-facing entry points last. The file's full contents are documented in §6. | `cat install-from-source.txt` shows the topologically-ordered editable-install lines; line count + leaf-first ordering verifiable. |
| **AC.FBE.4.4** (kept) | `pip install --dry-run -r install-from-source.txt` from a clean venv resolves cleanly: no PyPI 404 errors on inter-component bare-name deps. (Pip walks the file in order; each `-e ./<comp>` install registers the package so later bare-name deps in dependent components are satisfied in-memory.) | Direct invocation from canonical pos-v2 with a fresh venv: `python3.13 -m venv /tmp/fbe4-smoke-venv && /tmp/fbe4-smoke-venv/bin/pip install --dry-run -r install-from-source.txt` exits 0. |
| **AC.FBE.4.5** (DROPPED) | (Was: path-specs use `${PROJECT_ROOT}` or pip-compatible relative form.) Empirically rejected per Surface #1; no `${PROJECT_ROOT}` mechanism in FBE.4. | N/A — AC dropped. |
| **AC.FBE.4.6** (kept, unchanged) | Negative AC: zero changes to `[project.entry-points.loam.bootstrap.contributions]` block in workspace-bootstrap. | `git diff BASELINE..SEAL_COMMIT -- framework/workspace-bootstrap/pyproject.toml` is empty (subsumed by AC.FBE.4.1). |
| **AC.FBE.4.7** (kept + EXPANDED) | A NEW file `docs/install-from-source.md` covers: (a) prereqs (Python 3.13, fresh venv); (b) the one-command shortcut `pip install -r install-from-source.txt`; (c) the per-component fallback (the same ordered list as install-from-source.txt, expanded as discrete `pip install -e <path>` invocations); (d) troubleshooting common pip behaviour (resolver order matters; bare-name deps will hit PyPI in v0.2 once components publish; the file is v0.1.0-only); (e) reference to the README's `loam init` flow as the headline path. | File exists; markdown lints clean (rendered preview readable); content covers prereqs + shortcut + fallback + troubleshooting + headline-path reference. |
| **AC.FBE.4.8** (NEW) | The partition manifest at `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` admits both `install-from-source.txt` and `docs/install-from-source.md` to the `dev_and_public:` section so a stranger cloning the synth tree gets both files. Pre-existing `docs/**` admission may already cover the doc; verify at build time. | `grep -E 'install-from-source' framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` returns at least one explicit admission entry (top-level file requires explicit admission); doc may ride on existing `docs/**` glob. |
| **AC.FBE.4.S** (rewritten — fence-three-no-edit) | Sealed-component fence: `framework/workspace-bootstrap/` + `plugins/dev-sdlc/` + `framework/loam-init/`. All three sidecars bump (SEAL_COMMIT advances) but pyproject content stays byte-identical (per AC.FBE.4.{1,2}). Net source delta in fence-three: ZERO (bookkeeping-only). New files (`install-from-source.txt` at root, `docs/install-from-source.md` under docs/, partition-manifest admission edit) ride via `universal_paths.files` admission per the FBE.7 precedent (`CLAUDE.md`, `docs/odd-in-loam.md`, etc.). | `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under: (a) `framework/workspace-bootstrap/` (sidecar bump), (b) `plugins/dev-sdlc/` (sidecar bump), (c) `framework/loam-init/` (sidecar bump), (d) `docs/rebuild/plans/` (sub-plan + manifest + parent backfill via universal prefix), (e) the four explicitly-admitted top-level files (install-from-source.txt + docs/install-from-source.md + publish-mode-manifest.yaml). |

**ACs deliberately out of scope (NOT in FBE.4):**
- pyproject.toml edits to any of the three fenced components (Surface #2 + dispatcher ruling).
- v0.2 PyPI publish (Surface #3 — captured to FIDRAFT).
- Synth pipeline `framework/` prefix-strip fix (parent Decision D — FBE.2b).
- README.md or getting-started.md edits (FBE.5 description scrub + LOW-fix sweep).
- New deps added to any pyproject (no scope to add deps; fence is no-edit).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
The install-from-source.txt path is pip-native, not Claude-specific. But it composes with Claude Code's slash-command workflow indirectly: future `/loam:install` or `/loam:bootstrap` slash commands can invoke `pip install -r install-from-source.txt` as their first action. The shape doesn't preclude future Claude-leverage; it just doesn't add new leverage in FBE.4 itself.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. Removes the "fresh clone hits PyPI 404 and the persona never gets to greet the user" failure mode that the M11a-3 reviewer surfaced. The user's first install is now `pip install -r install-from-source.txt` (one command) followed by `loam init .` (per README). The persona greets immediately on the next `claude` invocation.
- **Harness test:** PASS. Adds a discoverable install-path artefact to the harness; the primary persona can describe the install path to a user via `loam --help`-derived output or by reading the doc.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which components appear in the install-from-source.txt, which doc sections cover prereqs vs troubleshooting) is the builder's call — but constrained tight enough that the smoke test (AC.FBE.4.4) admits exactly one shape (the topologically-ordered list that resolves clean on dry-run). No "options to rule on" framed in this plan-doc.

### Lens 4 — Prompt scope ↔ confidence
Very high confidence in outcome shape: dispatcher ruled Path B + fence-three-no-edit + the file paths + the smoke verification. Tight scope. Method is inferable from constraints (topological order of installs is forced by pip's resolver behaviour).

### Lens 5 — Swarming
FBE.4 is a leaf in the foldback ladder. ACs do not partition further: each binds to a single observable surface (file presence + content shape, smoke verification, fence diff). No sub-decomposition.

---

## 6. File-by-file map

### NEW files (admitted via `universal_paths.files`):

#### `install-from-source.txt` at canonical pos-v2 repo root

Content (full topological order):

```
# loam v0.1.0 — install-from-source path
#
# Stranger-clone install: a fresh venv + this requirements file.
# Each line is `-e ./<path>` so pip walks them in order; later
# components' bare-name inter-component deps hit the already-installed
# in-flight wheels (no PyPI roundtrip needed).
#
# Generated as part of FBE.4 (foldback amendment lane). When the
# loam component family publishes to PyPI at v0.2, this file becomes
# optional and the documented entry-point shifts to
# `pip install loam-cli loam-init loam-workspace-bootstrap loam-plugin-dev-sdlc`.
# See docs/install-from-source.md for the prose guide.

# Tier 1 — leaf components (no inter-component deps).
-e ./framework/scope-of-work
-e ./framework/objective-tracker
-e ./framework/observability-aggregator
-e ./framework/safety-layer
-e ./framework/reversibility-primitive
-e ./framework/cost-governance
-e ./framework/dormancy
-e ./framework/orchestrator
-e ./framework/self-correction
-e ./framework/self-upgrade
-e ./framework/telegram-interface
-e ./framework/primary-persona

# Tier 2 — composing the leaves.
-e ./framework/workspace-bootstrap

# Tier 3 — user-facing entry points (depend on Tier 2).
-e ./framework/tools/loam
-e ./framework/loam-init

# Tier 4 — plugin (depends on Tier 1 leaves + Tier 2).
-e ./plugins/dev-sdlc
```

**Build-time verification of the exact leaf set:** at build, `grep -l 'requires-python' framework/*/pyproject.toml` enumerates the leaf-shipping components; the topological order above is derived from the dependency graph in workspace-bootstrap's `dependencies = [...]` block. Some components may have inter-component deps among themselves (e.g. `primary-persona` depends on `loam-orchestrator`); these get sequenced before the dependent. Build-time will confirm and adjust if any tier mis-orders.

#### `docs/install-from-source.md`

Content sections (per AC.FBE.4.7):

1. Heading + one-line intent.
2. Prereqs — Python 3.13+, a fresh virtualenv (recommended), pip 23+ for editable-mode.
3. The one-command path — `pip install -r install-from-source.txt`.
4. Per-component fallback — same components in same order as discrete `pip install -e <path>` lines (in case a stranger wants to install a subset or troubleshoot a single component's failure).
5. Troubleshooting — pip resolver order matters; bare-name deps WILL hit PyPI lookup in v0.2 once components publish; this file is v0.1.0-only; common errors (missing build backend, Python version mismatch, venv not active).
6. Reference to README's `loam init` headline path — install-from-source is the precondition; `loam init .` is the next step.

### Sidecar bumps within sealed-component fence:

- `framework/workspace-bootstrap/tests/SEAL_COMMIT` — advances to FBE.4 seal SHA via `loam amend seal`.
- `framework/workspace-bootstrap/tests/SEAL_COMMIT.notes` — narrative file written by `loam amend seal` carrying the FBE.4 narrative (per manifest YAML §narrative.target + body).
- `plugins/dev-sdlc/tests/SEAL_COMMIT` — advances to FBE.4 seal SHA via `loam amend seal`.
- `plugins/dev-sdlc/tests/SEAL_COMMIT.notes` — narrative file written by `loam amend seal`.
- `framework/loam-init/tests/SEAL_COMMIT` — advances to FBE.4 seal SHA via `loam amend seal`.
- `framework/loam-init/tests/SEAL_COMMIT.notes` — narrative file written by `loam amend seal`.

### Partition-manifest edit (admitted via `universal_paths.files`):

- `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` — ADD two `path:` entries to `dev_and_public:` block:
  - `path: install-from-source.txt` (top-level file; not under any glob).
  - `path: docs/install-from-source.md` (verify at build time whether `docs/**` already covers; if so, this entry is omitted as redundant).

### Plan-doc + manifest (universal_paths.prefixes: `docs/rebuild/plans/`):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe4.md` (this file).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe4.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — §8 method-decision register: replace `### FBE.4` placeholder with apply commit SHA + seal commit SHA + verification summary.

**TOTAL fence diff:** zero source edits to the three named-fence components; six sidecar files (3 SEAL_COMMIT + 3 SEAL_COMMIT.notes) advance via `loam amend apply` + `loam amend seal`; two NEW files (install-from-source.txt + docs/install-from-source.md) at universal-admitted paths; one partition-manifest edit (universal-admitted path); plan-doc + manifest YAML + parent plan §8 backfill (universal prefix).

---

## 7. Smoke verification

**Pre-seal smoke (AC.FBE.4.4):**

```
python3.13 -m venv /tmp/fbe4-smoke-venv
/tmp/fbe4-smoke-venv/bin/pip install --upgrade pip
cd /Users/lukeivers/ivers-corp-pos-v2
/tmp/fbe4-smoke-venv/bin/pip install --dry-run -r install-from-source.txt
echo "Exit code: $?"
```

Expect exit 0 with "Would install ..." output naming all components in install order. If pip surfaces a 404 on a bare-name dep, this is a halt-and-surface — the install order is wrong or a component's pyproject declares an inter-component dep that isn't satisfied by an earlier `-e ./<comp>` line in the file. Halt + surface; fix is potentially out of FBE.4 scope.

**Note on dry-run vs real:** `pip install --dry-run` exercises the resolver but does NOT actually install. For an in-flight `-r requirements.txt` walk, pip's resolver tracks the set of in-progress installs in-memory; the `-e ./<path>` form is recognized as a local install whose `[project]` `name` value satisfies any later bare-name dep. This is the canonical pip behaviour exercised in Probe 7 of the prior status file.

---

## 8. Hard constraints

- Three sealed-component sidecars in fence: `framework/workspace-bootstrap/` + `plugins/dev-sdlc/` + `framework/loam-init/`. **Zero pyproject source edits in any of the three.**
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.4.*` (collision-safe; this sub-plan tightens the parent plan's existing AC.FBE.4.* per the empirical Surface #1 ruling).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`:
  - All three fence components' test suites must pass post-seal (no source edits → tests should be byte-identical PASS).
  - The smoke (AC.FBE.4.4) is exercised pre-seal manually; no in-tree pytest covers it directly (the smoke spans 16+ components and a fresh venv setup).

---

## 9. Out of scope (per ODD §2.5)

- pyproject.toml edits to workspace-bootstrap, dev-sdlc, loam-init (Surface #2 + dispatcher fence ruling).
- v0.2 PyPI publish (Surface #3; FIDRAFT).
- Synth pipeline path-rewrite (parent Decision D; FBE.2b).
- README.md / getting-started.md edits (FBE.5).
- Adding the four user-facing entry points (`loam-cli`, `loam-init`, `loam-workspace-bootstrap`, `loam-plugin-dev-sdlc`) to any other registry.
- pyproject `description`-field scrubs (FBE.5).

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not silently extend) on:

- **HT-1:** Smoke (AC.FBE.4.4) `pip install --dry-run -r install-from-source.txt` returns non-zero — halt; surface the actual error; do NOT iteratively shuffle the install order without analysis (the failure mode could be a real architectural issue like a circular dep).
- **HT-2:** A leaf component's pyproject declares an inter-component dep that isn't named in install-from-source.txt — halt; this surfaces a pyproject we missed in the topological enumeration.
- **HT-3:** `loam amend apply` rejects the manifest — halt; surface the error; the manifest's `universal_paths.files` admission shape may need adjustment.
- **HT-4:** `loam amend seal` rejects the seal — halt; surface; usually means a touched-file lives outside the fence + universal admissions.
- **HT-5:** A pyproject in any of the three fenced components has an unrelated edit detected post-seal (`git diff BASELINE..SEAL_COMMIT -- <pyproject>` is non-empty) — halt; AC.FBE.4.{1,2} violation; revert the unrelated change.
- **HT-6:** Surrounding-code ODD §2.5 violation discovered in any touched file — halt; surface; do NOT silently extend or fix in-band.
- **HT-7:** Wall-time exceeds 50 min (dispatch hard cap) — halt with partial findings.
- **HT-8:** WD drifts to pos3 — halt immediately.
- **HT-9:** Find a need to edit a pyproject "while I'm there" — halt + surface; scope creep.
- **HT-10:** The four user-facing entry-points' install order needs revision (e.g. `loam-init` must precede `loam-cli` for some reason) — halt; surface; the dispatch's named order (loam-cli first, then workspace-bootstrap, then loam-init, then dev-sdlc) is a hard constraint.

---

## 11. Risks

- **Risk: `pip install --dry-run -r install-from-source.txt` exercises resolver but not the in-memory in-flight install registration.** If pip's --dry-run mode skips the in-memory install set (and goes straight to PyPI for every bare-name dep), the smoke fails in a way that the real install would not. Mitigation: if dry-run fails, also try without `--dry-run` against a throwaway venv to confirm; document the behaviour in `docs/install-from-source.md` § Troubleshooting if real install works but dry-run doesn't.
- **Risk: synth pipeline strips `framework/` prefix (parent Decision D / FBE.2b).** If the synth strips `framework/`, the `-e ./framework/<comp>` lines in install-from-source.txt won't resolve in the synth tree. Mitigation: per dispatch — verify locally against canonical (which has `framework/`); FBE.6's smoke runs against the synth shape (which is FBE.2b's job to fix). FBE.4's smoke is canonical-only.
- **Risk: a component's pyproject declares a dep we missed in the topological enumeration.** Mitigation: AC.FBE.4.4 smoke catches this — pip surfaces a 404 on the missing dep. Halt-and-surface per HT-2.
- **Risk: partition-manifest admission of `install-from-source.txt` requires touching `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` which is owned by a component NOT in FBE.4's fence.** Mitigation: admit via `universal_paths.files` per Surface #5 builder's call; verify `loam amend apply` accepts the shape; if rejected (HT-3), expand fence to include `pos-publish-framework-only` (sidecar bump) and re-author the manifest (cost: one additional sidecar bump).
- **Risk: pip 26.0.1 specifically has different resolver behaviour vs pip 24.x or 25.x.** Mitigation: documented as v0.1.0 build-machine-only; v0.2 PyPI publish removes the requirements-file dependency. If a downstream stranger is on pip <26, the `pip install -r install-from-source.txt` form should still work (it's a stable pip behaviour predating 26.0).

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Source-side delta commit** — single commit covering: NEW `install-from-source.txt` at repo root, NEW `docs/install-from-source.md`, partition-manifest edit (one or two `path:` entries added to `dev_and_public:` block).
3. **Manifest commit** — author `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe4.manifest.yaml`.
4. **Smoke verification (no commit)** — run `pip install --dry-run -r install-from-source.txt` per §7 against a fresh venv. Verify exit 0. If non-zero → HT-1 halt.
5. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping commit (BASELINE bumps in three components' `test_no_sealed_amendments.py`; sidecar `SEAL_COMMIT` files advance).
6. **`loam amend seal`** — produces deterministic seal commit; sidecar `SEAL_COMMIT` files advance to seal SHA; narrative file written at each component's `tests/SEAL_COMMIT.notes`.
7. **Parent plan-doc backfill** — `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 backfill `### FBE.4` subsection with apply + seal SHAs (separate NEW commit; admitted via `docs/rebuild/plans/` universal prefix).
8. **Status file update** — overwrite `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe4-status-2026-05-03.md` with the seal report (keep historical empirical-probe section; replace halt-and-surface section with seal report).
9. **Pop the pre-build stash** — `git stash pop` to restore the dirty `docs/rebuild/FUTURE_IDEAS_DRAFT.md` per FBE.{2,3,7} pattern.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (§4 FBE.4 row tightened by this sub-plan).
- **Prior FBE.4 status (empirical anchor):** `<workspace>/.scratch/claude-output/fbe4-status-2026-05-03.md` (Probes 1–7 verified the C2 path-spec rejection; Probes 6 + 7 verified Paths A + B).
- **FBE.7 sub-plan / manifest YAML (shape precedent for fence-three sidecar-bump-only amendment style):** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.{md,manifest.yaml}` — though FBE.7 has source edits, its narrative-target convention + universal_paths.files admission shape is the model.
- **FBE.3 sub-plan / manifest YAML (shape precedent for partition-manifest edit):** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe3.{md,manifest.yaml}` — FBE.3 admits the partition-manifest edit via the partition component's sidecar.
- **Partition manifest:** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (parent plan's AC.FBE.4.* tightened/dropped/rewritten per Surface #1 empirical anchor).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-10).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to fence components only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1–6 explicit; Surface #5 surfaces the partition-admission shape for dispatcher review).
  - `feedback_principle_conflict_resolution_multi_signal` (Surface #5 names the conflict, signals, call, and surface step).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at planning" claim has a path/line/probe-number citation to the prior status file).
  - `feedback_critical_thinking_on_deviations` (Surface #5 enumerates fence-three vs fence-four alternatives weighed by outcome × cost × risk).
  - `feedback_swarming_recursive_decomposition` (Lens 5 — leaf in foldback ladder, no further decomposition).

---

## 14. AI-time band

- Predicted: **20–35 min, midpoint 27 min**; dispatch hard cap 50 min.
- Justification: zero source edits in fence-three; two NEW files at known paths; one partition-manifest 2-line edit; manifest-YAML authoring; smoke verification (one dry-run + 0–2 retries if needed); apply + seal + parent §8 backfill + status file update + stash pop. Per rubric: amendment-build (multi-component-aware single-fence triple) → 20–45 min midpoint 32; tighten to 20–35 because the in-fence component delta is null (sidecar-bump-only); the smoke verification is the longest single step.

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Source-side delta commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.4 sub-plan-doc. Ready to build.*
