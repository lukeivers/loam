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

"""Workspace + user sync-config schema and loader (β.1).

Pydantic schema for ``<workspace>/.pos/sync-config.yaml`` and
``~/.loam/sync-config.yaml``. Both files share one schema; the
loader walks a precedence chain (workspace-local > ~/-rooted >
defaults) and returns a single merged ``SyncConfig`` instance.

Field ``canonical_source`` (NEW for amendment #58 / β.1) carries
the URL or absolute local path the operator wants ``pos-sync``
to pull canonical from when no ``--canonical`` flag is passed.
URL form clones to ``~/.loam/canonical-cache/<repo-id>/`` per
``canonical_cache.py``; absolute-path form is used directly.

Fields ``cumulative_token_budget`` and ``per_conflict_token_budget``
honour the docstring promise in ``_resolver_client.py:292`` (HALT-
FOUND #2 in plan §13). β.1 wires the precedence chain so file-set
budgets are consumed by ``cli.py``'s resolver-budget construction.

Per amendment #56 + plan-doc Hard Constraint #8: this file is a
*config layer, not a state layer*. Operator preferences live here;
state (audit log, state.yaml, sync-protected.yaml envelope,
ancestor-cache.yaml) lives elsewhere. The schema's ``extra="forbid"``
guarantees state-shaped fields cannot accidentally land here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


CanonicalSourceKind = Literal["url", "local"]


class SyncConfig(BaseModel):
    """Operator-tunable sync-config schema (β.1).

    Both ``<workspace>/.pos/sync-config.yaml`` and
    ``~/.loam/sync-config.yaml`` validate against this model.
    Unknown fields raise (``extra="forbid"`` mirrors #56's
    ``sync_protected.py`` pattern).

    All fields are optional with ``None`` defaults so partial
    files are legal. The loader (``load_sync_config``) merges
    workspace-local over user-rooted over defaults.
    """

    model_config = ConfigDict(extra="forbid")

    canonical_source: str | None = Field(
        default=None,
        description=(
            "URL (http(s)://, git@) or absolute POSIX path to the "
            "canonical loam working tree. When absent, "
            "pos-sync requires --canonical on the CLI."
        ),
    )
    cumulative_token_budget: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Cumulative resolver token budget override (default "
            "100_000 from ResolverBudget when None)."
        ),
    )
    per_conflict_token_budget: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Per-conflict resolver token budget override (default "
            "5_000 from ResolverBudget when None)."
        ),
    )


def workspace_sync_config_path(workspace_root: Path) -> Path:
    """Return ``<workspace_root>/workspace/.pos/sync-config.yaml``.

    D-migration D.2 (amendment #63): workspace-state under
    ``<workspace>/workspace/.pos/``.
    """
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "sync-config.yaml"


def user_sync_config_path() -> Path:
    """Return ``~/.loam/sync-config.yaml`` (user-rooted)."""
    return Path.home() / ".loam" / "sync-config.yaml"


def _load_one(path: Path) -> SyncConfig | None:
    """Load + validate a single sync-config.yaml file.

    Returns ``None`` when the file is absent. Raises on YAML parse
    error or Pydantic validation error so the operator gets explicit
    feedback at load time (fail-closed).
    """
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    raw: Any = yaml.safe_load(text) or {}
    if not isinstance(raw, dict):
        raise ValueError(
            f"{path}: top-level YAML must be a mapping (got "
            f"{type(raw).__name__})"
        )
    return SyncConfig.model_validate(raw)


def _merge(higher: SyncConfig | None, lower: SyncConfig | None) -> SyncConfig:
    """Field-by-field merge: ``higher`` wins where set, else ``lower``.

    ``higher`` and ``lower`` are SyncConfig instances or None;
    when both are None the result is the default (all fields None).
    A field is "set" when it is not ``None``.
    """
    if higher is None and lower is None:
        return SyncConfig()
    if higher is None:
        return lower if lower is not None else SyncConfig()
    if lower is None:
        return higher
    # Both non-None: pick higher's value when set, else lower's.
    fields: dict[str, Any] = {}
    for name in SyncConfig.model_fields:
        h_val = getattr(higher, name)
        l_val = getattr(lower, name)
        fields[name] = h_val if h_val is not None else l_val
    return SyncConfig(**fields)


def load_sync_config(workspace_root: Path) -> SyncConfig:
    """Load sync-config with the precedence chain.

    Precedence (highest → lowest):

    1. ``<workspace_root>/.pos/sync-config.yaml`` (workspace-local).
    2. ``~/.loam/sync-config.yaml`` (user-rooted).
    3. Schema defaults (all fields None).

    Field-by-field merge: a field set in the workspace-local file
    wins over the user-rooted file's value for that field.

    The CLI flag (``--canonical``, ``--budget-tokens``) overrides
    the merged file values; that override happens in ``cli.py``,
    NOT here. This loader is precedence layers 1 + 2 + 3 only.
    """
    ws = _load_one(workspace_sync_config_path(workspace_root))
    user = _load_one(user_sync_config_path())
    return _merge(ws, user)


def canonical_source_kind(source: str) -> CanonicalSourceKind:
    """Discriminate URL vs absolute-local-path forms (D-β.1 LOCKED).

    Locked accepted shapes:

    - Starts with ``http://`` or ``https://`` → ``"url"``
    - Starts with ``git@`` → ``"url"`` (SSH form)
    - Starts with ``/`` (absolute POSIX path) → ``"local"``

    Anything else (relative paths, ``file://``, ``ssh://``,
    Windows-style paths, etc.) raises ``ValueError`` with a message
    naming the three accepted shapes. β.1 trusts the operator's
    canonical_source as set; future amendments can widen the
    accepted-shape set.
    """
    if source.startswith(("http://", "https://", "git@")):
        return "url"
    if source.startswith("/"):
        return "local"
    raise ValueError(
        f"canonical_source {source!r} must be one of: "
        "an http(s) URL (e.g. 'https://github.com/owner/repo'), "
        "a git@-style SSH spec (e.g. 'git@github.com:owner/repo.git'), "
        "or an absolute POSIX path (e.g. '/Users/.../loam'). "
        "Relative paths, file:// URLs, and ssh:// URLs are not accepted."
    )
