"""Clause-(h) workspace-data envelope.

Three-class workspace-protection envelope used by clause-(h) to decide
how a conflicting workspace path is resolved against canonical:

- **Class A** — workspace state. NEVER overwritten by an upgrade.
  Examples: ``personas/<handle>/contract.yaml``,
  ``.pos/objective_tracker.sqlite``, ``.pos/**``, ``.scratch/**``,
  ``.mcp.json``. Class-A paths are workspace-supplied artefacts the
  framework must not touch.

- **Class B** — operator preferences. Overridden when the workspace
  modified them (workspace wins); accepted from canonical otherwise.
  Examples: ``memory.yaml``.

- **Class C** — framework code. When both sides changed, the
  clause-(h) LLM-mediated resolver decides. Default class for any
  path that doesn't match a Class-A or Class-B rule.

The envelope is loaded from ``<workspace>/.pos/sync-protected.yaml``.
The Pydantic schema enforces a **framework floor** — a set of patterns
that MUST be present in the workspace's envelope; removing any of them
fails validation at load time. The floor mirrors safety-layer's
``always_ask.yaml`` pattern: framework-supplied invariants the
workspace cannot opt out of.

A fresh-clone workspace (no ``sync-protected.yaml`` present) receives
a default envelope written from
``self-upgrade/templates/sync-protected.default.yaml`` on the first
clause-(h) upgrade invocation.
"""

from __future__ import annotations

import fnmatch
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FileClass(str, Enum):
    """Three-class workspace-data envelope."""

    A = "A"  # workspace state — never overwritten
    B = "B"  # operator preference — override-resolved
    C = "C"  # framework code — LLM-resolved on conflict


class SyncProtectedRule(BaseModel):
    """One classification rule: glob pattern → class."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pattern: str
    klass: FileClass


# Framework floor — patterns the workspace's sync-protected.yaml
# MUST carry. Removing any of these fails Pydantic validation.
# Class-A paths cover workspace state the framework never touches.
# memory.yaml is Class B because canonical may legitimately update
# defaults but workspace-side edits should win.
#
# D-migration D.2 (amendment #63): post-D.2 workspace state lives
# under ``workspace/`` so the patterns prefix every workspace-state
# match accordingly. ``memory.yaml`` remains workspace-root-relative
# per its operator-preference shape (lives under ``workspace/.pos/``
# in the new layout but the synced ref pattern keeps the bare name
# for backwards-compat with prior envelopes).
FRAMEWORK_FLOOR: tuple[tuple[str, FileClass], ...] = (
    ("workspace/personas/**/contract.yaml", FileClass.A),
    ("workspace/.pos/objective_tracker.sqlite", FileClass.A),
    ("workspace/.pos/**", FileClass.A),
    ("workspace/.scratch/**", FileClass.A),
    ("workspace/.mcp.json", FileClass.A),
    ("workspace/memory.yaml", FileClass.B),
)


class SyncProtected(BaseModel):
    """Workspace's sync-protected envelope.

    ``framework_floor`` is the set of rules the framework requires;
    validation refuses any envelope missing a floor entry.
    ``workspace_rules`` is operator-tunable; first-match wins, with
    ``workspace_rules`` matched before ``framework_floor`` so an
    operator can tighten Class-A coverage but cannot remove it.
    """

    model_config = ConfigDict(extra="forbid")

    framework_floor: list[SyncProtectedRule] = Field(default_factory=list)
    workspace_rules: list[SyncProtectedRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def _floor_intact(self) -> "SyncProtected":
        floor_patterns = {(r.pattern, r.klass) for r in self.framework_floor}
        missing: list[str] = []
        for pattern, klass in FRAMEWORK_FLOOR:
            if (pattern, klass) not in floor_patterns:
                missing.append(f"{pattern} ({klass.value})")
        if missing:
            raise ValueError(
                "sync-protected.yaml is missing framework-floor rules: "
                f"{missing}. The framework floor is non-negotiable; "
                "restore the missing rules to the framework_floor list."
            )
        return self

    def classify(self, path: str) -> FileClass:
        """Classify ``path`` against workspace rules then framework floor.

        First-match wins. ``workspace_rules`` are checked first so an
        operator can tighten Class-A coverage of additional paths;
        ``framework_floor`` is the fallback. Anything that matches no
        rule is Class C (framework-code default → resolver-handled).
        """
        for rule in self.workspace_rules:
            if fnmatch.fnmatchcase(path, rule.pattern):
                return rule.klass
        for rule in self.framework_floor:
            if fnmatch.fnmatchcase(path, rule.pattern):
                return rule.klass
        return FileClass.C


def default_sync_protected() -> SyncProtected:
    """Build the framework-default envelope (used to seed first-run)."""
    return SyncProtected(
        framework_floor=[
            SyncProtectedRule(pattern=p, klass=k)
            for p, k in FRAMEWORK_FLOOR
        ],
        workspace_rules=[],
    )


def load_sync_protected(path: str | Path) -> SyncProtected:
    """Load + validate a workspace's sync-protected.yaml."""
    p = Path(path)
    raw = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{p}: top-level must be a mapping")
    return SyncProtected.model_validate(raw)


def save_sync_protected(sp: SyncProtected, path: str | Path) -> None:
    """Write the envelope to disk."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        yaml.safe_dump(
            sp.model_dump(mode="json"),
            default_flow_style=False,
            sort_keys=False,
        )
    )


def write_default_if_absent(workspace_root: Path) -> Path:
    """Write the default envelope to
    ``<workspace>/workspace/.pos/sync-protected.yaml`` if absent.
    Returns the path either way. Idempotent: existing files are not
    overwritten.

    D-migration D.2 (amendment #63): workspace-state under
    ``<workspace>/workspace/.pos/``.
    """
    from workspace_bootstrap.workspace_paths import pos_subdir

    target = pos_subdir(workspace_root) / "sync-protected.yaml"
    if target.exists():
        return target
    save_sync_protected(default_sync_protected(), target)
    return target


def classify(path: str, sp: SyncProtected) -> FileClass:
    """Module-level convenience wrapper around ``SyncProtected.classify``."""
    return sp.classify(path)
