# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Establish the per-workspace ``.loam/`` user-state layout (slice P1.2).

This is FRAMEWORK code whose *output* is USER-STATE — the same shape as
``new_workspace.py`` (framework machinery that writes the user's tree). It
creates the declared ``.loam/`` layout that holds the workspace's
meaningful state behind the framework ↔ user-state boundary (master plan
§2 / §3 decision #1: ``~/.claude/`` = global user-state;
``<workspace>/.loam/`` = workspace-scoped user-state).

Contract (the declared layout):

    <workspace>/.loam/
      README.md            self-describing contract + boundary rule
      memory/              FBM episode store (EXISTS — never disturbed here)
      migrations/          applied-migration CURSOR home (.cursor; engine = P1.3)
      user-model/          home for the per-user model + config (P1.5 fills it)
      session-model/       home for the session-model (later slice fills it)
      environment-model/   home for the per-user environment/perception model

Design invariants (the slice's acceptance, AC-LOAM-LAYOUT-1..4):

- **Idempotent / fail-safe.** Running twice is a no-op on the second run;
  an existing ``memory/``, ``README.md``, or ``.cursor`` is detected and
  left intact. NEVER overwrites live user-state.
- **Additive.** It only ever creates absent paths. It removes nothing.
- **Boundary-respecting.** It writes only under ``<workspace>/.loam/`` —
  nothing under ``framework/``.
- **Self-describing.** It always ensures a ``README.md`` documenting every
  declared dir + the boundary rule exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# The directories the layout declares as homes for present + future
# user-state. ``memory/`` is intentionally NOT in this auto-create list:
# it is the live FBM store and is only ever touched when already absent
# (a brand-new workspace), via ESTABLISH_IF_ABSENT below — never recreated
# or cleared.
DECLARED_DIRS: tuple[str, ...] = (
    "migrations",
    "user-model",
    "session-model",
    "environment-model",
)

# Dirs that hold live state and must only be created when wholly absent.
ESTABLISH_IF_ABSENT: tuple[str, ...] = ("memory",)

README_NAME = "README.md"

README_CONTENT = """\
# `.loam/` — per-workspace user-state

This directory holds **this workspace's meaningful state**, behind the
loam framework ↔ user-state boundary. It is the workspace-scoped half of
user-state; global user-state lives at `~/.claude/` (CLAUDE.md,
OBJECTIVES.md, the feedback corpus).

**Boundary rule:** USER-STATE ONLY. No framework code lives here. The
framework machinery that *writes* these dirs lives under `framework/`;
its *output* (everything below) is user-state — unique per user, carried
forward across loam upgrades, migrated never overwritten.

This whole tree is gitignored on the user side (it is the user's state,
not loam source). The framework-side *contract* that declares what a
release changes in user-state lives in the tracked loam repo under
`docs/state-migrations/`.

## Declared layout

| Path | What it holds |
|---|---|
| `memory/` | The FBM episode store + search index + access log. The live cross-session memory (slice P1.1). **Never recreated or cleared by the layout establish step** — only created when wholly absent on a brand-new workspace. |
| `migrations/` | The applied-migration **cursor** (`.cursor`): which declared state-migrations *this* workspace has applied. The migration *engine* that reads/writes it is slice P1.3. |
| `user-model/` | Home for the per-user model + config (slice P1.5 fills it). |
| `session-model/` | Home for the session-model (later slice fills it). |
| `environment-model/` | Home for the per-user environment / perception model (later slice fills it). |
| `claude_p_policy.toml` | (if present) Workspace-scoped `claude -p` isolation policy — left in place. |

## Sibling user-state left in place

A sibling `.pos/` directory may hold legacy workspace user-state
(memory-write-queue, sync config, trait-reflection, …). It is **not**
absorbed into `.loam/` — relocating it would be a destructive move
(protection-floor / G★). It is left where it is.
"""


@dataclass
class LayoutResult:
    """Outcome of an establish run — what was created vs already present.

    ``created`` and ``existing`` together name every declared path, so a
    test can assert idempotency (a second run has empty ``created``) and
    completeness (every declared path is present after the run).
    """

    loam_dir: Path
    created: list[str] = field(default_factory=list)
    existing: list[str] = field(default_factory=list)
    memory_preexisting: bool = False

    @property
    def changed(self) -> bool:
        return bool(self.created)


def establish_loam_layout(workspace_root: Path | str) -> LayoutResult:
    """Idempotently establish the ``.loam/`` layout under ``workspace_root``.

    Creates every declared path that is absent and writes a self-describing
    ``README.md`` if one is missing. Touches nothing that already exists —
    in particular an existing ``memory/`` tree is detected and left
    byte-for-byte intact (fail-safe over live state).

    Returns a :class:`LayoutResult` recording created vs pre-existing paths.
    """
    root = Path(workspace_root)
    loam = root / ".loam"
    result = LayoutResult(loam_dir=loam)

    # The .loam/ root itself.
    if loam.exists():
        result.existing.append(".")
    else:
        loam.mkdir(parents=True)
        result.created.append(".")

    # Live-state dirs: create ONLY if wholly absent; never recreate/clear.
    for name in ESTABLISH_IF_ABSENT:
        path = loam / name
        if path.exists():
            result.existing.append(name)
            if name == "memory":
                result.memory_preexisting = True
        else:
            path.mkdir(parents=True)
            result.created.append(name)

    # Declared home dirs: additive, idempotent. A .gitkeep marks each empty
    # home so its declared existence survives in any tooling that prunes
    # empty dirs (and documents intent for a human browsing the tree).
    for name in DECLARED_DIRS:
        path = loam / name
        if path.exists():
            result.existing.append(name)
        else:
            path.mkdir(parents=True)
            (path / ".gitkeep").write_text("", encoding="utf-8")
            result.created.append(name)

    # Self-describing README — write only if absent (never overwrite a
    # README a user may have annotated).
    readme = loam / README_NAME
    if readme.exists():
        result.existing.append(README_NAME)
    else:
        readme.write_text(README_CONTENT, encoding="utf-8")
        result.created.append(README_NAME)

    return result
