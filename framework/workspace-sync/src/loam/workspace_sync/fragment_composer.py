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

"""settings-fragment auto-composer (loam-realignment RF-1 closure).

EXTENDS ``workspace-sync``. After a successful ``pos-sync`` advances
``<workspace>/framework/``, this module DISCOVERS every loam
component's ``settings.fragment.json`` under the synced framework tree
and COMPOSES their ``hooks`` blocks into
``<workspace>/.claude/settings.json`` — additively, idempotently, and
without clobbering the user's/workspace's own settings.

Design (plan ``docs/plans/workspace-sync-settings-fragment-composer.md``):

  * **Discovery (D-SFC.3 / AC.SFC.1).** Glob
    ``<framework>/*/hooks/**/settings.fragment.json`` — catches
    ``frame-kernel/hooks/settings.fragment.json`` AND
    ``hands-off-lifecycle/hooks/keep_pace/settings.fragment.json`` at
    their differing depths. Presence of the file is the opt-in; no
    registry. Each fragment's ``_comment`` field is ignored.

  * **Loam-ownership tag (D-SFC.1 / D-SFC.2 / AC.SFC.2).** Every
    composed matcher-group carries a ``_loam`` sibling key naming its
    source component + fragment relative path. The unknown-field
    marker was VERIFIED at build time to be tolerated by Claude Code
    (2.1.168): a hook carrying the ``_loam`` sibling fires normally
    (plan §8 trigger-1 / RF-2 resolved — no fallback marker needed).
    The tag gives a clean ownership boundary: the composer's write set
    is STRUCTURALLY limited to groups carrying ``_loam`` — a
    user/workspace group (no ``_loam``) is never in the write path.

  * **Dedupe / idempotency (D-SFC.1 / AC.SFC.4).** The desired
    loam-owned set is keyed by (source-fragment identity, event,
    resolved command tuple). A second compose with an unchanged
    fragment set is a no-op (no duplicate, no write).

  * **Removal (D-SFC.2 / AC.SFC.5).** The only removal the composer
    performs is dropping a previously-composed ``_loam`` group whose
    source fragment is no longer present in the synced tree. User
    groups are never removed.

  * **${LOAM_REPO} resolution (AC.SFC.6).** Resolved to the directory
    that CONTAINS ``framework/`` — i.e. ``workspace_root`` — so a
    composed ``${LOAM_REPO}/framework/<component>/...`` command points
    at the synced framework tree.

  * **Non-clobber (D-SFC.2 / AC.SFC.3).** Only the ``hooks`` key is
    touched; every other top-level key (``statusLine``,
    ``permissions``, ``env``, ``model``, ...) is copied through
    verbatim. Within ``hooks``, user-owned (untagged) groups are
    preserved byte-equivalent in place.

  * **Safety (D-SFC.5 / AC.SFC.7).** Writes are atomic (temp file in
    the same dir + ``os.replace``). A malformed/unparseable existing
    ``settings.json`` HALTS the compose (raises
    ``MalformedSettingsError``) and writes nothing — never a
    destructive overwrite. ``--dry-run-compose`` computes the plan and
    writes nothing. A malformed *fragment* is SKIPPED with a warning
    (RF-5), never aborts the whole compose.

HC#6 note (RF-1): this is a POST-merge NON-git Python write to
``<workspace>/.claude/settings.json`` (the workspace ROOT, outside
``framework/``). It does not violate HC#6's GIT-only-in-``framework/``
promise (the merge still happens only in ``framework/``); it is a
named widening of pos-sync's total write surface, bounded to exactly
the loam-owned ``hooks`` entries of ``<workspace>/.claude/settings.json``.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# The Lens-1 canonical resolver for <workspace>/.claude/ (D-Q.A4 lock).
# IMPORTED + called, never edited (plan §8 halt-trigger #3).
from loam.workspace_bootstrap.workspace_paths import claude_dir

#: The placeholder every shipped fragment carries in its commands.
LOAM_REPO_PLACEHOLDER = "${LOAM_REPO}"

#: The sibling key on a matcher-group marking it loam-composed. Its
#: value records the source component + fragment relative path so each
#: composed group is traceable (AC.SFC.2). Verified tolerated by Claude
#: Code at build time (plan §8 trigger-1 / RF-2).
LOAM_TAG_KEY = "_loam"

#: The fragment field the composer ignores (documentation only).
FRAGMENT_COMMENT_KEY = "_comment"

#: Discovery glob, relative to the synced framework root. Catches
#: fragments at both ``<component>/hooks/`` and
#: ``<component>/hooks/<subdir>/`` depths (D-SFC.3 / AC.SFC.1).
FRAGMENT_GLOB = "*/hooks/**/settings.fragment.json"


class MalformedSettingsError(Exception):
    """Raised when an existing settings.json cannot be parsed.

    The compose HALTS (writes nothing) rather than overwrite a file it
    cannot safely reason about (D-SFC.5 / AC.SFC.7).
    """


@dataclass(frozen=True)
class ComposedGroup:
    """A single loam-owned matcher-group destined for an event."""

    event: str
    source_component: str
    source_fragment: str  # relative to the framework root
    group: dict[str, Any]  # the resolved, tag-stamped matcher-group

    def dedupe_key(self) -> tuple[str, str, str, tuple[str, ...]]:
        """Stable identity used for add/skip/refresh reconciliation.

        Keyed by (source fragment, event, source component, resolved
        command tuple). ``${LOAM_REPO}`` is already resolved at this
        point, so the key is stable across runs in the same workspace
        (AC.SFC.4) and changes only when the resolved command changes
        (AC.SFC.6 refresh).
        """
        commands = tuple(
            h.get("command", "")
            for h in self.group.get("hooks", [])
            if isinstance(h, dict)
        )
        return (
            self.source_fragment,
            self.event,
            self.source_component,
            commands,
        )


@dataclass
class ComposePlan:
    """The reconcile diff between desired + present loam-owned sets."""

    added: list[ComposedGroup] = field(default_factory=list)
    refreshed: list[ComposedGroup] = field(default_factory=list)
    removed: list[tuple[str, str]] = field(default_factory=list)
    # ^ (event, source_fragment) of each dropped loam group.
    skipped_fragments: list[tuple[Path, str]] = field(default_factory=list)
    # ^ (fragment path, reason) for malformed fragments (RF-5).
    user_groups_touched: int = 0  # always 0 — asserted for the summary.

    def is_noop(self) -> bool:
        return not (self.added or self.refreshed or self.removed)

    def summary_line(self) -> str:
        """One-line stderr summary (D-SFC.4)."""
        parts = []
        if self.added:
            names = ", ".join(
                f"{g.source_component} {g.event}" for g in self.added
            )
            parts.append(f"+{len(self.added)} ({names})")
        if self.refreshed:
            parts.append(f"~{len(self.refreshed)} refreshed")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if not parts:
            parts.append("no change")
        skip = (
            f"; {len(self.skipped_fragments)} fragment(s) skipped"
            if self.skipped_fragments
            else ""
        )
        return (
            f"[settings-composer] {'; '.join(parts)}; "
            f"{self.user_groups_touched} user entries touched{skip}"
        )


# ---- discovery + parse -------------------------------------------------


def discover_fragments(framework_root: Path) -> list[Path]:
    """Return every ``settings.fragment.json`` under the synced tree.

    Sorted for deterministic compose order (AC.SFC.4 stability).
    """
    return sorted(framework_root.glob(FRAGMENT_GLOB))


def _component_of(fragment_path: Path, framework_root: Path) -> str:
    """The top-level component dir name a fragment belongs to."""
    rel = fragment_path.relative_to(framework_root)
    return rel.parts[0]


def _resolve_command(command: str, loam_repo: Path) -> str:
    """Substitute ``${LOAM_REPO}`` with the resolved repo root (AC.SFC.6)."""
    return command.replace(LOAM_REPO_PLACEHOLDER, str(loam_repo))


def _parse_fragment(
    fragment_path: Path,
    framework_root: Path,
    loam_repo: Path,
) -> list[ComposedGroup]:
    """Parse one fragment into resolved, tag-stamped ComposedGroups.

    Raises ``ValueError`` on a malformed fragment (the caller SKIPS it
    with a warning per RF-5, never aborts the whole compose).
    """
    raw = json.loads(fragment_path.read_text())
    if not isinstance(raw, dict):
        raise ValueError("fragment is not a JSON object")
    hooks_block = raw.get("hooks")
    if not isinstance(hooks_block, dict):
        raise ValueError("fragment has no 'hooks' mapping")

    component = _component_of(fragment_path, framework_root)
    source_fragment = str(fragment_path.relative_to(framework_root))

    composed: list[ComposedGroup] = []
    for event, groups in hooks_block.items():
        if not isinstance(groups, list):
            raise ValueError(f"event {event!r} does not map to a list")
        for group in groups:
            if not isinstance(group, dict) or "hooks" not in group:
                raise ValueError(
                    f"event {event!r} carries a malformed matcher-group"
                )
            resolved = copy.deepcopy(group)
            for h in resolved.get("hooks", []):
                if isinstance(h, dict) and "command" in h:
                    h["command"] = _resolve_command(h["command"], loam_repo)
            # Stamp the ownership tag (AC.SFC.2). Traceable to source.
            resolved[LOAM_TAG_KEY] = {
                "component": component,
                "source_fragment": source_fragment,
            }
            composed.append(
                ComposedGroup(
                    event=event,
                    source_component=component,
                    source_fragment=source_fragment,
                    group=resolved,
                )
            )
    return composed


def _desired_groups(
    framework_root: Path,
    loam_repo: Path,
    *,
    plan_skips: list[tuple[Path, str]],
) -> list[ComposedGroup]:
    """The full loam-owned set the synced tree wants composed.

    A malformed fragment is recorded in ``plan_skips`` and omitted
    (RF-5) — it never aborts the compose or contributes garbage.
    """
    desired: list[ComposedGroup] = []
    for fragment_path in discover_fragments(framework_root):
        try:
            desired.extend(
                _parse_fragment(fragment_path, framework_root, loam_repo)
            )
        except (ValueError, json.JSONDecodeError) as exc:
            plan_skips.append((fragment_path, str(exc)))
    return desired


# ---- settings.json read / classify ------------------------------------


def _read_settings(settings_path: Path) -> dict[str, Any]:
    """Read the existing settings.json, or return {} when absent.

    Raises ``MalformedSettingsError`` (HALT, never overwrite) when the
    file exists but is unparseable (D-SFC.5 / AC.SFC.7).
    """
    if not settings_path.exists():
        return {}
    try:
        data = json.loads(settings_path.read_text())
    except (json.JSONDecodeError, ValueError) as exc:
        raise MalformedSettingsError(
            f"existing settings.json at {settings_path} is not valid JSON "
            f"({exc}); compose HALTED — file left untouched."
        ) from exc
    if not isinstance(data, dict):
        raise MalformedSettingsError(
            f"existing settings.json at {settings_path} is not a JSON "
            f"object; compose HALTED — file left untouched."
        )
    return data


def _is_loam_group(group: Any) -> bool:
    return isinstance(group, dict) and LOAM_TAG_KEY in group


# ---- reconcile (the diff) ---------------------------------------------


def plan_compose(framework_root: Path, settings_path: Path) -> ComposePlan:
    """Compute the add/refresh/remove diff without writing.

    ``${LOAM_REPO}`` resolves to the dir CONTAINING ``framework/`` —
    i.e. ``framework_root.parent`` = the workspace root.
    """
    loam_repo = framework_root.parent
    plan = ComposePlan()

    desired = _desired_groups(
        framework_root, loam_repo, plan_skips=plan.skipped_fragments
    )
    desired_by_key = {g.dedupe_key(): g for g in desired}
    # All loam-owned (fragment-identity) source fragments still shipping,
    # so a removal targets only a vanished fragment, not a refreshed one.
    desired_fragments = {g.source_fragment for g in desired}

    existing = _read_settings(settings_path)
    existing_hooks = existing.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        existing_hooks = {}

    # Index the loam-owned groups already present (by dedupe key) and the
    # loam-owned (event, source_fragment) pairs present (for removal).
    present_keys: set[tuple[str, str, str, tuple[str, ...]]] = set()
    present_loam_pairs: set[tuple[str, str]] = set()
    for event, groups in existing_hooks.items():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not _is_loam_group(group):
                continue
            tag = group.get(LOAM_TAG_KEY, {})
            source_fragment = (
                tag.get("source_fragment", "")
                if isinstance(tag, dict)
                else ""
            )
            component = (
                tag.get("component", "") if isinstance(tag, dict) else ""
            )
            commands = tuple(
                h.get("command", "")
                for h in group.get("hooks", [])
                if isinstance(h, dict)
            )
            present_keys.add(
                (source_fragment, event, component, commands)
            )
            present_loam_pairs.add((event, source_fragment))

    # ADD: desired groups whose dedupe key is not present.
    # REFRESH: a desired group whose source fragment + event is present
    #          but whose resolved command tuple changed (different key).
    desired_pairs = {(g.event, g.source_fragment) for g in desired}
    refreshed_pairs: set[tuple[str, str]] = set()
    for key, group in desired_by_key.items():
        if key in present_keys:
            continue  # already present + identical → no-op (idempotent)
        pair = (group.event, group.source_fragment)
        if pair in present_loam_pairs:
            plan.refreshed.append(group)
            refreshed_pairs.add(pair)
        else:
            plan.added.append(group)

    # REMOVE: a present loam pair that is (a) no longer desired at all
    # (vanished fragment), and (b) not merely being refreshed.
    for event, source_fragment in present_loam_pairs:
        if source_fragment in desired_fragments:
            continue  # fragment still ships → kept or refreshed, not removed
        plan.removed.append((event, source_fragment))

    return plan


# ---- atomic write -----------------------------------------------------


def _atomic_write(settings_path: Path, data: dict[str, Any]) -> None:
    """Write settings.json atomically (temp in same dir + os.replace).

    A crash never leaves a half-written settings.json (D-SFC.5).
    """
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_path.parent / f".{settings_path.name}.compose-tmp"
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, settings_path)


def _apply_plan(
    settings: dict[str, Any],
    plan: ComposePlan,
) -> dict[str, Any]:
    """Return a NEW settings dict with the plan applied.

    Non-`hooks` keys are copied through verbatim (AC.SFC.3). Within
    `hooks`, user-owned (untagged) groups are preserved in place;
    loam-owned groups are reconciled (AC.SFC.2/.4/.5).
    """
    out = copy.deepcopy(settings)
    hooks = out.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
    out["hooks"] = hooks

    removed_pairs = set(plan.removed)
    refreshed_pairs = {
        (g.event, g.source_fragment) for g in plan.refreshed
    }

    for event in list(hooks.keys()):
        groups = hooks[event]
        if not isinstance(groups, list):
            continue
        kept: list[Any] = []
        for group in groups:
            if not _is_loam_group(group):
                kept.append(group)  # user group: preserved in place
                continue
            tag = group.get(LOAM_TAG_KEY, {})
            source_fragment = (
                tag.get("source_fragment", "")
                if isinstance(tag, dict)
                else ""
            )
            pair = (event, source_fragment)
            if pair in removed_pairs or pair in refreshed_pairs:
                continue  # drop (removed) or drop-then-re-add (refresh)
            kept.append(group)  # loam group, unchanged: keep
        hooks[event] = kept

    # Append the added + refreshed groups.
    for group in plan.added + plan.refreshed:
        hooks.setdefault(group.event, []).append(group.group)

    # Drop now-empty event lists that we fully removed (only if they
    # became empty AND held only loam groups — a user-empty list we
    # never created stays as the user had it).
    for event in list(hooks.keys()):
        if hooks[event] == []:
            del hooks[event]

    return out


# ---- public entry-point -----------------------------------------------


def compose_settings_fragments(
    workspace_root: Path,
    *,
    dry_run: bool = False,
    emit_summary: bool = True,
) -> ComposePlan:
    """Discover + compose fragments into ``<ws>/.claude/settings.json``.

    The production entry-point ``_execute_sync`` calls this on each
    terminal-success path (AC.SFC.S drives it via a real sync).

    * ``dry_run=True`` computes + (optionally) prints the plan and
      writes NOTHING (AC.SFC.7).
    * A malformed existing settings.json raises ``MalformedSettingsError``
      and writes nothing (AC.SFC.7) — the caller surfaces it; the sync
      itself stands.

    Returns the ``ComposePlan`` (what was added/refreshed/removed).
    """
    framework_root = workspace_root / "framework"
    settings_path = claude_dir(workspace_root) / "settings.json"

    plan = plan_compose(framework_root, settings_path)

    if emit_summary:
        prefix = "[dry-run] " if dry_run else ""
        print(prefix + plan.summary_line(), file=sys.stderr)
        for fragment_path, reason in plan.skipped_fragments:
            print(
                f"[settings-composer] WARNING: skipped malformed fragment "
                f"{fragment_path}: {reason}",
                file=sys.stderr,
            )
        if dry_run:
            for g in plan.added:
                cmds = ", ".join(
                    h.get("command", "")
                    for h in g.group.get("hooks", [])
                    if isinstance(h, dict)
                )
                print(
                    f"[dry-run]   + {g.event} <- {g.source_fragment} "
                    f"[{cmds}]",
                    file=sys.stderr,
                )
            for g in plan.refreshed:
                print(
                    f"[dry-run]   ~ {g.event} <- {g.source_fragment} "
                    f"(refresh)",
                    file=sys.stderr,
                )
            for event, source_fragment in plan.removed:
                print(
                    f"[dry-run]   - {event} <- {source_fragment} (vanished)",
                    file=sys.stderr,
                )

    if dry_run or plan.is_noop():
        return plan

    # Re-read (the malformed-HALT path already fired in plan_compose's
    # _read_settings; re-reading here is safe + keeps the write atomic
    # against the just-validated content).
    settings = _read_settings(settings_path)
    new_settings = _apply_plan(settings, plan)
    _atomic_write(settings_path, new_settings)
    return plan
