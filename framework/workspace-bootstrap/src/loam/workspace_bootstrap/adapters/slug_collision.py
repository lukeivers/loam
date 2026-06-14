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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Workspace-slug collision detection + disambiguation
(principle-foundation-structural-enforcement, AC.PFSE.6).

THE PROBLEM. A workspace slug is derived from the directory basename
(``workspace_slug``); it becomes the launchd label ``com.loam.<slug>.
<kind>`` and the plist filename in ``~/Library/LaunchAgents/``. Two
workspaces on one host whose basenames sluggify to the SAME slug (e.g.
``pos-v2`` and ``pos.v2`` both → ``pos-v2``, or two clones both named
``loam``) collide: the second bootstrap's plists CLOBBER the first
workspace's services. The collision is silent today — the structural
fix (feedback_structural_enforcement_on_recurrence) is a deterministic
collision check at install + bootstrap time, with a disambiguation
knob.

THE DETECTION. A slug is "taken by another workspace" iff a
``com.loam.<slug>.*.plist`` already exists in the LaunchAgents dir AND
its embedded ``WorkingDirectory`` resolves to a DIFFERENT workspace
root than the one being bootstrapped. (A plist whose WorkingDirectory
is the SAME workspace is a re-bootstrap, not a collision.)

THE KNOB. ``disambiguate_slug`` appends a numeric suffix
(``<slug>-2``, ``<slug>-3``, ...) until the slug is free of the taken
set — the deterministic disambiguation the caller applies when a
collision is detected and the user opts to disambiguate rather than
abort.

Deterministic; NO network/LLM. Reads plist files (a bounded glob over
one directory). Fail-soft: an unreadable plist is treated as
non-colliding (the check must never crash the bootstrap).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .first_run_scaffold import workspace_slug


# The plist <WorkingDirectory> value embeds ``{workspace}/...`` — we
# extract the workspace prefix to compare against the bootstrapping
# workspace root. The templates write
# ``<string>{workspace}/framework/memory-system</string>`` etc., so the
# captured path is the workspace root plus a known suffix.
_WORKING_DIR_RE = re.compile(
    r"<key>WorkingDirectory</key>\s*<string>([^<]+)</string>"
)

# Known trailing suffixes the launchd templates append to {workspace}.
# Stripping one of these recovers the workspace root.
_WORKDIR_SUFFIXES: tuple[str, ...] = (
    "/framework/memory-system",
    "/workspace",
)

_LAUNCH_AGENTS_DEFAULT = Path.home() / "Library" / "LaunchAgents"


@dataclass(frozen=True)
class SlugCollision:
    """A detected slug collision.

    ``slug`` is the colliding slug. ``this_workspace`` is the workspace
    being bootstrapped. ``other_workspace`` is the EXISTING workspace
    already claiming the slug (resolved from a plist's WorkingDirectory),
    or None when the other workspace could not be resolved but a
    same-slug plist nonetheless exists. ``plist_paths`` are the colliding
    plist files.
    """

    slug: str
    this_workspace: Path
    other_workspace: Path | None
    plist_paths: tuple[Path, ...]


def _workspace_root_from_plist(plist_text: str) -> Path | None:
    """Recover the workspace root from a plist's WorkingDirectory, or
    None when it cannot be parsed."""
    m = _WORKING_DIR_RE.search(plist_text)
    if m is None:
        return None
    workdir = m.group(1).strip()
    for suffix in _WORKDIR_SUFFIXES:
        if workdir.endswith(suffix):
            return Path(workdir[: -len(suffix)])
    # Unknown suffix — return the dir itself (conservative: a different
    # path still signals a collision).
    return Path(workdir)


def _same_path(a: Path, b: Path) -> bool:
    """True iff two paths resolve to the same location (best-effort)."""
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return str(a) == str(b)


def detect_slug_collision(
    workspace_root: Path | str,
    *,
    launch_agents_dir: Path | None = None,
) -> SlugCollision | None:
    """Return a ``SlugCollision`` iff the workspace's derived slug is
    already claimed by a DIFFERENT workspace's launchd plists, else None.

    Method: derive the slug; glob ``com.loam.<slug>.*.plist`` in the
    LaunchAgents dir; for each, recover the embedded workspace root. A
    plist whose workspace root differs from ``workspace_root`` is a
    collision. A plist for the SAME workspace (re-bootstrap) is NOT a
    collision. Fail-soft: an unreadable plist is skipped.
    """
    ws = Path(workspace_root)
    try:
        slug = workspace_slug(ws)
    except Exception:  # noqa: BLE001 — unrepresentable slug is not a collision
        return None

    agents_dir = launch_agents_dir or _LAUNCH_AGENTS_DEFAULT
    if not agents_dir.is_dir():
        return None

    colliding: list[Path] = []
    other: Path | None = None
    for plist in sorted(agents_dir.glob(f"com.loam.{slug}.*.plist")):
        try:
            text = plist.read_text(encoding="utf-8")
        except OSError:
            continue
        other_ws = _workspace_root_from_plist(text)
        if other_ws is not None and _same_path(other_ws, ws):
            # Same workspace — re-bootstrap, not a collision.
            continue
        colliding.append(plist)
        if other is None and other_ws is not None:
            other = other_ws

    if not colliding:
        return None
    return SlugCollision(
        slug=slug,
        this_workspace=ws,
        other_workspace=other,
        plist_paths=tuple(colliding),
    )


def disambiguate_slug(
    slug: str,
    *,
    taken_slugs: set[str] | frozenset[str],
) -> str:
    """Return the first ``<slug>-N`` (N from 2) not in ``taken_slugs``.

    The deterministic disambiguation knob: when a collision is detected
    and the user opts to disambiguate, this yields a stable free slug.
    If ``slug`` itself is not taken, it is returned unchanged.
    """
    if slug not in taken_slugs:
        return slug
    n = 2
    while f"{slug}-{n}" in taken_slugs:
        n += 1
    return f"{slug}-{n}"


def taken_slugs_in(
    launch_agents_dir: Path | None = None,
) -> set[str]:
    """Return the set of slugs currently claimed by ``com.loam.<slug>.
    <kind>.plist`` files in the LaunchAgents dir.

    Used by ``disambiguate_slug`` callers to compute the taken set from
    the live host state. Fail-soft: a missing dir yields the empty set.
    """
    agents_dir = launch_agents_dir or _LAUNCH_AGENTS_DEFAULT
    if not agents_dir.is_dir():
        return set()
    out: set[str] = set()
    pat = re.compile(r"^com\.loam\.([a-z0-9-]+)\.[a-z0-9-]+\.plist$")
    for plist in agents_dir.glob("com.loam.*.plist"):
        m = pat.match(plist.name)
        if m:
            out.add(m.group(1))
    return out
