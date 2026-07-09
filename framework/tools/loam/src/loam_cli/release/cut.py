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

"""Deterministic release-cut computation (AC.CUT.* + AC.PRE.2).

Recomputes the SemVer class + expected version number from repo state per
``docs/release-versioning-policy.md``. Shared by the deterministic-cut
gate (:func:`loam_cli.release.gates.check_deterministic_cut`) and the
``loam release preflight`` verb (:mod:`loam_cli.release.preflight`) — one
mechanism, two entry points (AC.PRE.2).

"Content class" is mechanized as a conventional-commit-prefix scan over
the unreleased commit range (D-CUT.CLASS): any ``feat`` subject => a
MINOR-class (new backwards-compatible capability); a breaking marker
(``!`` after the type, or ``BREAKING CHANGE`` in a commit body) => a
surfaced breaking note; else PATCH. This operationalizes the policy's
semantic "class from content"; it diverges from perfect semantic
classification in edge cases (an internal-only ``feat`` => a false MINOR;
a capability landing under ``fix``/``chore`` => a missed under-cut). The
gate is a tripwire whose corrective hint is human-reconcilable, not an
authority — the divergence is named + accepted in the plan-doc §6
(D-CUT.CLASS) as an F2 surface.

MAJOR stays owner-gated (D-CUT.MAJOR): this module never returns MAJOR as
the computed class — MAJOR is a quality-bar owner event per the policy
(breaking changes ride minors with deprecation cycles). The gate handles
a MAJOR *target* as an allowed owner escalation.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


# --------------------------------------------------------------------
# Version parsing + bump arithmetic
# --------------------------------------------------------------------


def parse_version(version: str) -> tuple[int, ...] | None:
    """``v1.11.0`` -> ``(1, 11, 0)``; ``v0.2.5.1`` -> ``(0, 2, 5, 1)``.

    Strips a leading ``v`` and any pre-release suffix (``-rc.1``). Returns
    ``None`` when the core is not 3 or 4 dot-separated integers (the gate
    then treats the target as not-a-clean-bump rather than crashing).
    """
    core = version.lstrip("vV").split("-", 1)[0].split("+", 1)[0]
    parts = core.split(".")
    if len(parts) not in (3, 4):
        return None
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def _sort_key(version: str) -> tuple[int, ...]:
    """Semver sort key; unparseable tags sort to the bottom."""
    t = parse_version(version)
    if t is None:
        return (-1,)
    # Pad to 4 so 3-digit and 4-digit compare consistently.
    return t + (0,) * (4 - len(t))


def bump_patch(t: tuple[int, ...]) -> tuple[int, int, int]:
    return (t[0], t[1], t[2] + 1)


def bump_minor(t: tuple[int, ...]) -> tuple[int, int, int]:
    return (t[0], t[1] + 1, 0)


def bump_major(t: tuple[int, ...]) -> tuple[int, int, int]:
    return (t[0] + 1, 0, 0)


def bump_hotfix(t: tuple[int, ...]) -> tuple[int, int, int, int]:
    """Four-digit hot-patch: ``v0.2.5`` -> ``v0.2.5.1``; a further hot
    patch on a four-digit base increments the fourth part."""
    if len(t) == 4:
        return (t[0], t[1], t[2], t[3] + 1)
    return (t[0], t[1], t[2], 1)


def format_version(t: tuple[int, ...]) -> str:
    return "v" + ".".join(str(p) for p in t)


def bump_class_between(
    published: str, target: str
) -> str | None:
    """Return the bump class *target* represents relative to *published*.

    One of ``MAJOR`` / ``MINOR`` / ``PATCH`` / ``HOTFIX``; ``None`` when
    *target* is not a clean single bump of *published* (a misnumber — e.g.
    skipping a minor, or bumping two parts at once).
    """
    p = parse_version(published)
    q = parse_version(target)
    if p is None or q is None:
        return None
    p3 = p[:3]
    if tuple(q) == bump_major(p3):
        return "MAJOR"
    if tuple(q) == bump_minor(p3):
        return "MINOR"
    if tuple(q) == bump_patch(p3):
        return "PATCH"
    if tuple(q) == bump_hotfix(p):
        return "HOTFIX"
    return None


# --------------------------------------------------------------------
# Conventional-commit class scan (D-CUT.CLASS)
# --------------------------------------------------------------------


# A conventional-commit subject: ``<type>(<scope>)?(!)?: <desc>``.
_SUBJECT_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\([^)]*\))?(?P<bang>!)?:", re.IGNORECASE
)


def _split_commits(log_text: str) -> list[str]:
    """Split a ``git log`` dump into per-commit bodies on the NUL
    record separator (``--format=...%x00``)."""
    return [c for c in log_text.split("\x00") if c.strip()]


def _is_feat(message: str) -> bool:
    subject = message.strip().splitlines()[0] if message.strip() else ""
    m = _SUBJECT_RE.match(subject)
    return bool(m and m.group("type").lower() == "feat")


def _is_breaking(message: str) -> bool:
    lines = message.strip().splitlines()
    subject = lines[0] if lines else ""
    m = _SUBJECT_RE.match(subject)
    if m and m.group("bang"):
        return True
    return "BREAKING CHANGE" in message


def classify_commits(messages: list[str]) -> tuple[str, bool]:
    """Return ``(class, has_breaking)``.

    ``class`` is ``MINOR`` when any commit is a ``feat``; else ``PATCH``.
    MAJOR is never returned (D-CUT.MAJOR — owner-gated). ``has_breaking``
    flags any breaking marker for the gate to surface as a note.
    """
    has_breaking = any(_is_breaking(m) for m in messages)
    has_feat = any(_is_feat(m) for m in messages)
    klass = "MINOR" if has_feat else "PATCH"
    return klass, has_breaking


# --------------------------------------------------------------------
# Published-tag reads
# --------------------------------------------------------------------


def _git(
    *args: str, repo_root: Path
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )


def highest_local_tag(repo_root: Path) -> str | None:
    """Highest ``vX.Y.Z`` tag in the LOCAL tag set (excludes pre-releases)."""
    proc = _git("tag", "--list", "v*", repo_root=repo_root)
    tags = [
        t
        for t in proc.stdout.split()
        if parse_version(t) is not None and "-" not in t
    ]
    return max(tags, key=_sort_key) if tags else None


def highest_origin_tag(repo_root: Path, remote: str = "origin") -> str | None:
    """Highest ``vX.Y.Z`` tag on the ORIGIN remote (excludes pre-releases
    + the ``^{}`` peeled-tag lines). Returns ``None`` when the remote is
    unreachable or has no version tags (the gate degrades fail-safe)."""
    proc = _git("ls-remote", "--tags", remote, repo_root=repo_root)
    if proc.returncode != 0:
        return None
    tags: list[str] = []
    for line in proc.stdout.splitlines():
        m = re.search(r"refs/tags/(v[0-9][^\s^]*)$", line.strip())
        if m and parse_version(m.group(1)) is not None and "-" not in m.group(1):
            tags.append(m.group(1))
    return max(tags, key=_sort_key) if tags else None


def _commit_messages(
    repo_root: Path, published: str, extra_refs: tuple[str, ...]
) -> list[str]:
    """``git log --format=%B%x00 <published>..HEAD`` (+ extra refs) bodies.

    *extra_refs* widen the range to also include commits reachable from
    named merging branches but not from *published* — the preflight verb
    passes candidate branches so the computed cut reflects what WOULD be
    cut once they merge (audit Class A "unreleased seals on main + merging
    branches").
    """
    range_specs = [f"{published}..HEAD", *[f"{published}..{r}" for r in extra_refs]]
    proc = _git(
        "log", "--format=%B%x00", "--no-merges", *range_specs, repo_root=repo_root
    )
    if proc.returncode != 0:
        return []
    return _split_commits(proc.stdout)


# --------------------------------------------------------------------
# The cut
# --------------------------------------------------------------------


@dataclass(frozen=True)
class CutResult:
    """Computed release cut for the current repo state."""

    published: str | None
    klass: str  # MINOR | PATCH (MAJOR is owner-gated, never computed here)
    has_breaking: bool
    expected_version: str | None
    commit_count: int
    determinate: bool
    detail: str


def compute_cut(
    repo_root: Path,
    *,
    extra_refs: tuple[str, ...] = (),
    published_override: str | None = None,
    commit_messages_override: list[str] | None = None,
) -> CutResult:
    """Recompute the release cut (class + expected number) from repo state.

    *published_override* / *commit_messages_override* let the gate + tests
    drive the computation without hitting git (mirrors the injection hooks
    on gates 8/9). In production both are ``None`` and the function reads
    the origin tag + the ``<published>..HEAD`` commit range.
    """
    published = published_override or highest_origin_tag(repo_root)
    if published is None:
        return CutResult(
            published=None,
            klass="PATCH",
            has_breaking=False,
            expected_version=None,
            commit_count=0,
            determinate=False,
            detail=(
                "could not determine the current published version (no "
                "origin version tag reachable); cut is indeterminate"
            ),
        )
    if commit_messages_override is not None:
        messages = commit_messages_override
    else:
        messages = _commit_messages(repo_root, published, extra_refs)
    klass, has_breaking = classify_commits(messages)
    p = parse_version(published)
    if p is None:
        return CutResult(
            published=published,
            klass=klass,
            has_breaking=has_breaking,
            expected_version=None,
            commit_count=len(messages),
            determinate=False,
            detail=f"published tag {published!r} is not parseable as SemVer",
        )
    expected = bump_minor(p[:3]) if klass == "MINOR" else bump_patch(p[:3])
    return CutResult(
        published=published,
        klass=klass,
        has_breaking=has_breaking,
        expected_version=format_version(expected),
        commit_count=len(messages),
        determinate=True,
        detail=(
            f"published={published}, {len(messages)} unreleased commit(s), "
            f"class={klass}"
            + (", breaking-markers present" if has_breaking else "")
        ),
    )
