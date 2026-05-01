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

"""Single-source-of-truth workspace-state path helpers.

D-migration D.2 (amendment #63). Establishes the workspace-state
directory at ``<workspace>/workspace/`` and centralises every framework
reader's path computation onto a single helper module.

## Why this module exists

Pre-D.2, every framework reader of workspace-state computed its own
path: ``workspace_root / ".pos"``, ``workspace_root / "personas"``,
``host.workspace_root / "data" / ...``, ``workspace_root /
"objective_tracker.sqlite"``. The path-string was replicated across
~10 reader files (per the D.2 halt-and-surface report). A future move
of the layout root would have to touch every replicated site.

Post-D.2, every reader imports from this module:

    from loam.workspace_bootstrap.workspace_paths import (
        pos_subdir,
        personas_dir,
        data_subdir,
        mcp_json_path,
        tracker_db_path,
        scratch_dir,
        orchestrator_log_paths,
        memory_worker_log_paths,
        claude_dir,
    )

The helpers return ``Path`` objects under ``<workspace>/workspace/``
for workspace-state surfaces. ``claude_dir`` is the lone exception
(per D-Q.A4 lock — Claude Code expects ``.claude/`` at workspace
root). Future moves of the workspace-state subdirectory change one
file (``WORKSPACE_STATE_SUBDIR``) — every reader inherits the move.

## HC#6 structural guard (AC.D.2.4)

The ``WorkspaceLayout`` Pydantic model carries a model-level
validator that refuses construction when the supplied
``workspace_root`` has basename ``framework`` — defence against the
specific mis-construction the plan named: a workspace_root literally
named ``framework`` would route workspace-state writes into the
canonical-repo's framework subtree. Production workspace roots have
names like ``pos3``, ``ivers-corp-pos-v2`` — never ``framework``.

The validator runs once at construction; subsequent path reads are
cheap attribute access. The structural promise: workspace-state
``<workspace_root>/workspace/<...>`` never lands under
``<canonical>/framework/<component>/`` because the workspace_root
basename ``framework`` is refused.

The validator deliberately does NOT refuse ``framework`` as a
non-root segment of the absolute workspace_root path: legitimate
paths like a self-upgrade release-archive simulation
(``pos-base/framework/releases/<tag>/``) use ``framework`` as an
intermediate segment, and refusing those would over-fire on
benign test fixtures. Pre-D.2 this was a convention (every reader
chose its own path). Post-D.2 it is a Pydantic-enforced invariant
on the structural mis-construction the plan named.

## Hands-off-lifecycle hooks duplicate constants per D.2-build.B

The hook scripts under ``framework/hands-off-lifecycle/hooks/`` run
under launchd / from-bash subprocesses with a stdlib-only import
contract (per amendment #4's first-run-helper architecture — the
hook boots before the workspace's ``.venv`` is built). They cannot
import this module. Hooks duplicate the relevant constants
(``WORKSPACE_STATE_SUBDIR = "workspace"``, ``POS_SUBDIR = ".pos"``,
etc.) with a comment pointing at this module as the canonical source.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator


# ---- canonical constants ----------------------------------------------


# Workspace-state subdirectory name. Every workspace-state file lives
# under ``<workspace>/<WORKSPACE_STATE_SUBDIR>/<...>``. ``.claude/`` is
# the lone exception per D-Q.A4 lock.
WORKSPACE_STATE_SUBDIR = "workspace"

# Workspace-state file/dir names, inside ``WORKSPACE_STATE_SUBDIR``.
POS_SUBDIR = ".pos"
PERSONAS_SUBDIR = "personas"
DATA_SUBDIR = "data"
SCRATCH_SUBDIR = ".scratch"
MCP_JSON_FILENAME = ".mcp.json"
TRACKER_DB_FILENAME = "objective_tracker.sqlite"
ORCHESTRATOR_OUT_LOG = "orchestrator.out.log"
ORCHESTRATOR_ERR_LOG = "orchestrator.err.log"
MEMORY_WORKER_OUT_LOG = "memory-write-worker.out.log"
MEMORY_WORKER_ERR_LOG = "memory-write-worker.err.log"

# ``.claude/`` lives at workspace root per D-Q.A4 lock.
CLAUDE_SUBDIR = ".claude"


# ---- WorkspaceLayout schema (HC#6 structural guard) -------------------


class WorkspaceLayout(BaseModel):
    """Validated workspace-state layout for a given ``workspace_root``.

    HC#6 (AC.D.2.4): the model-level validator refuses construction
    when ``workspace_root`` contains a path segment named
    ``framework`` — defence against accidental framework-rooted
    workspace-state writes. The check is structural; bypass requires
    editing this validator.

    Subclassing / mutation is forbidden (``model_config = frozen``).
    """

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    workspace_root: Path

    @model_validator(mode="after")
    def _refuse_framework_rooted(self) -> "WorkspaceLayout":
        # HC#6 (AC.D.2.4): refuse a workspace_root whose basename is
        # ``framework`` — the canonical pos-v2 layout puts the
        # framework's own component code under ``framework/<component>``
        # at the canonical-repo root, so a workspace_root literally
        # named ``framework`` is a misuse: it would route workspace-
        # state writes into the canonical-repo's framework subtree.
        # Production workspace roots have names like ``pos3``,
        # ``ivers-corp-pos-v2`` — never ``framework``.
        #
        # Why basename, not "any segment": legitimate paths under a
        # release-archive simulation (e.g. self-upgrade's release
        # directory ``pos-base/framework/releases/<tag>/``) use
        # ``framework`` as a non-root segment. Refusing on any segment
        # over-fires; refusing on basename catches the actual
        # mis-construction the plan named.
        try:
            resolved = self.workspace_root.expanduser().resolve()
        except OSError:
            resolved = self.workspace_root
        if resolved.name == "framework":
            raise ValueError(
                "WorkspaceLayout refuses a workspace_root whose basename "
                "is 'framework'. Workspace-state must not be rooted "
                "under a framework/ component (HC#6, AC.D.2.4). "
                f"Got: {resolved}"
            )
        return self

    # ---- derived paths (no I/O) -------------------------------------

    @property
    def workspace_state_dir(self) -> Path:
        """``<workspace>/workspace/`` — the workspace-state root."""
        return self.workspace_root / WORKSPACE_STATE_SUBDIR

    @property
    def pos_dir(self) -> Path:
        """``<workspace>/workspace/.pos/`` — sentinel + state files."""
        return self.workspace_state_dir / POS_SUBDIR

    @property
    def personas_dir(self) -> Path:
        """``<workspace>/workspace/personas/``."""
        return self.workspace_state_dir / PERSONAS_SUBDIR

    @property
    def data_dir(self) -> Path:
        """``<workspace>/workspace/data/`` — adapter SQLite stores."""
        return self.workspace_state_dir / DATA_SUBDIR

    @property
    def scratch_dir(self) -> Path:
        """``<workspace>/workspace/.scratch/`` — ephemeral artefacts."""
        return self.workspace_state_dir / SCRATCH_SUBDIR

    @property
    def mcp_json_path(self) -> Path:
        """``<workspace>/workspace/.mcp.json`` — Claude Code MCP reg."""
        return self.workspace_state_dir / MCP_JSON_FILENAME

    @property
    def tracker_db_path(self) -> Path:
        """``<workspace>/workspace/objective_tracker.sqlite``."""
        return self.workspace_state_dir / TRACKER_DB_FILENAME

    @property
    def orchestrator_out_log(self) -> Path:
        return self.workspace_state_dir / ORCHESTRATOR_OUT_LOG

    @property
    def orchestrator_err_log(self) -> Path:
        return self.workspace_state_dir / ORCHESTRATOR_ERR_LOG

    @property
    def memory_worker_out_log(self) -> Path:
        return self.workspace_state_dir / MEMORY_WORKER_OUT_LOG

    @property
    def memory_worker_err_log(self) -> Path:
        return self.workspace_state_dir / MEMORY_WORKER_ERR_LOG

    @property
    def claude_dir(self) -> Path:
        """``<workspace>/.claude/`` — D-Q.A4 lock; NOT under
        workspace-state subdir. Claude Code expects ``.claude/`` at
        workspace root.
        """
        return self.workspace_root / CLAUDE_SUBDIR


# ---- ergonomic top-level helpers --------------------------------------
#
# Thin wrappers over ``WorkspaceLayout`` for callers that prefer a
# function-call shape over a model construction. Each helper builds a
# fresh ``WorkspaceLayout`` (the validator runs every time), so a bad
# workspace_root surfaces at call site rather than later.


def _layout(workspace_root: Path | str) -> WorkspaceLayout:
    return WorkspaceLayout(workspace_root=Path(workspace_root))


def workspace_state_dir(workspace_root: Path | str) -> Path:
    """``<workspace>/workspace/``."""
    return _layout(workspace_root).workspace_state_dir


def pos_subdir(workspace_root: Path | str) -> Path:
    """``<workspace>/workspace/.pos/``."""
    return _layout(workspace_root).pos_dir


def personas_dir(workspace_root: Path | str) -> Path:
    """``<workspace>/workspace/personas/``."""
    return _layout(workspace_root).personas_dir


def data_subdir(workspace_root: Path | str) -> Path:
    """``<workspace>/workspace/data/``."""
    return _layout(workspace_root).data_dir


def scratch_dir(workspace_root: Path | str) -> Path:
    """``<workspace>/workspace/.scratch/``."""
    return _layout(workspace_root).scratch_dir


def mcp_json_path(workspace_root: Path | str) -> Path:
    """``<workspace>/workspace/.mcp.json``."""
    return _layout(workspace_root).mcp_json_path


def tracker_db_path(workspace_root: Path | str) -> Path:
    """``<workspace>/workspace/objective_tracker.sqlite``."""
    return _layout(workspace_root).tracker_db_path


def orchestrator_log_paths(workspace_root: Path | str) -> tuple[Path, Path]:
    """``(stdout, stderr)`` log paths for the orchestrator plist."""
    layout = _layout(workspace_root)
    return (layout.orchestrator_out_log, layout.orchestrator_err_log)


def memory_worker_log_paths(workspace_root: Path | str) -> tuple[Path, Path]:
    """``(stdout, stderr)`` log paths for the memory-write-worker
    plist.
    """
    layout = _layout(workspace_root)
    return (layout.memory_worker_out_log, layout.memory_worker_err_log)


def claude_dir(workspace_root: Path | str) -> Path:
    """``<workspace>/.claude/`` — D-Q.A4 lock; at workspace root."""
    return _layout(workspace_root).claude_dir
