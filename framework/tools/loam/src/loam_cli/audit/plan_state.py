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

"""Plan-state derivation — what plans exist + how built they REALLY are
(FBM correctness cycle, Slice 1 / AC.PSI.1).

The Slice-C STATE engine (:mod:`loam_cli.audit.registry`) derives a
project's per-COMPONENT status fresh from ground truth. This module is
the same shape one level up: per registered project, the set of
PLAN-DOCS (``docs/plans/*.md`` + the sealed archive
``docs/plans/sealed/*.md``) and each plan's REAL build-state, derived
FRESH from disk + the git ref graph — NEVER from a plan's own prose
status line (the exact drift surface that produced the 2026-06-09
"wasn't planned" failure).

Build-state classes (AC.PSI.1):

  * ``sealed`` — the plan's seal narrative landed in the sealed
    archive (``docs/plans/sealed/<slug>.md``), OR the plan's NEWEST
    slug-named evidence commit in the HEAD-reachable subject history
    is a completed seal (``chore(seals): <slug> …``) — the
    latest-evidence-seal-reachability predicate (AC.PSTATE.1 /
    D-PSTATE.1, plan-state-false-partial-fix). Archive presence is a
    doc convention, not the build fact; keying ``sealed`` on archive
    presence alone reported 18 fully-sealed legacy-narrative plans as
    "partially built" (the 2026-06-11 false-dispatch-premise defect).
  * ``partially-sealed`` — build evidence exists but the newest
    slug-named evidence commit is NOT a completed seal (an apply
    landed; its seal has not) — a genuinely mid-cycle plan
    (AC.PSTATE.2). A NEW apply after a prior seal (next cycle
    mid-flight) re-enters this state. Sealing a slice in the real
    repo flips a plan through these states on the next derivation
    with NO doc edit — the derived-not-stored contract.
  * ``no-build-evidence`` — a plan-doc exists but the ref graph
    carries no apply/seal commit naming its slug.

ADDITIVE-ONLY (plan §5 fence #1): this module is a NEW sibling of
``registry.py``; it consumes ``PROJECT_REGISTRY`` / ``resolve_project``
read-only and changes no existing Slice-C contract. Read-only git/disk
probes only.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from loam_cli.audit.registry import (
    PROJECT_REGISTRY,
    ProjectStateSpec,
    resolve_project,
)

#: Build-state tokens (AC.PSI.1). String constants so persona-side
#: consumers can compare without importing an enum across the lazy
#: fail-soft boundary.
BUILD_STATE_SEALED = "sealed"
BUILD_STATE_PARTIAL = "partially-sealed"
BUILD_STATE_PENDING = "no-build-evidence"

#: The governed plan roots, relative to a project's repo root. A
#: project with no plans dir degrades to an empty derivation (D6
#: fail-soft) — never an error.
PLANS_SUBDIR = Path("docs/plans")
SEALED_SUBDIR = Path("docs/plans/sealed")

#: Commit-subject prefixes that constitute build evidence for a slug
#: (AC.PSI.1 — seal evidence from the ref graph, not prose). These are
#: the deterministic shapes ``loam amend apply`` / ``loam amend seal``
#: author.
_EVIDENCE_SUBJECT_PREFIXES = ("chore(amend): ", "chore(seals): ")

#: A completed-seal subject (the second evidence shape). When the
#: NEWEST evidence line for a slug carries this prefix, the plan's
#: latest build cycle completed — the sealed verdict's git-fact arm
#: (AC.PSTATE.1 / D-PSTATE.1).
_SEAL_SUBJECT_PREFIX = "chore(seals): "

#: Builder-companion plan docs (``<slug>.builder-plan.md``) are
#: auxiliary artefacts of the SAME plan identity, not independent
#: plans; enumerating them as separate slugs would double-count.
_BUILDER_PLAN_SUFFIX = ".builder-plan"

#: Bounded read when extracting a plan's title (the first ``# ``
#:  heading) — identity only, never the prose status line.
_TITLE_READ_CAP = 4096
_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

#: Git subject probe timeout. A hung git never wedges a derivation
#: (the Slice-C/D fail-soft discipline AC.PSI.2 inherits).
_GIT_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class PlanBuildState:
    """One plan-doc's identity + REAL build-state (AC.PSI.1).

    ``seal_evidence`` carries the matching apply/seal commit lines
    (``<short-sha> <subject>``) so a consumer (the AC.CLG.1 claim
    guard's steer; the AC.PSI.OA test's independent verification) can
    cite the ground truth rather than re-deriving it.
    """

    project: str
    slug: str
    title: str
    doc_path: str
    build_state: str
    seal_evidence: tuple[str, ...]
    in_sealed_archive: bool


def _git_subject_lines(repo_root: Path) -> list[tuple[str, str]]:
    """Every commit as ``(short_sha, subject)``, newest first.

    One subprocess call per derivation (AC.PSI.1 — evidence from the
    ref graph). Fail-soft: any git error / timeout yields ``[]`` so a
    non-repo plans dir degrades to no evidence rather than a crash.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "log", "--format=%h\t%s"],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    out: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        sha, _, subject = line.partition("\t")
        if sha and subject:
            out.append((sha, subject))
    return out


def _evidence_for_slug(
    slug: str, subjects: list[tuple[str, str]]
) -> tuple[str, ...]:
    """The apply/seal commit lines naming ``slug`` (AC.PSI.1).

    A subject matches when it is ``chore(amend): <slug>`` /
    ``chore(seals): <slug>`` followed by a non-slug character (space /
    end) — so ``…-check-1`` never claims ``…-check-1b``'s evidence.
    """
    hits: list[str] = []
    for sha, subject in subjects:
        for prefix in _EVIDENCE_SUBJECT_PREFIXES:
            candidate = prefix + slug
            if subject == candidate or subject.startswith(candidate + " "):
                hits.append(f"{sha} {subject}")
                break
    return tuple(hits)


def _latest_evidence_is_seal(evidence: tuple[str, ...]) -> bool:
    """True when the NEWEST evidence line is a completed seal commit
    (AC.PSTATE.1 — evidence lines are ``<short-sha> <subject>``,
    newest-first by ``git log`` order; HEAD-reachability is by
    construction of the subject probe)."""
    if not evidence:
        return False
    _sha, _, subject = evidence[0].partition(" ")
    return subject.startswith(_SEAL_SUBJECT_PREFIX)


def _plan_title(doc: Path, slug: str) -> str:
    """The plan's first ``# `` heading (identity), else the prettified
    slug. Bounded read; fail-soft — title is identity, never state."""
    try:
        head = doc.read_text(encoding="utf-8", errors="replace")[
            :_TITLE_READ_CAP
        ]
    except OSError:
        return slug.replace("-", " ")
    m = _TITLE_RE.search(head)
    if m:
        return m.group(1).strip()
    return slug.replace("-", " ")


def _enumerate_plan_docs(plans_dir: Path) -> dict[str, Path]:
    """Slug → doc path for the governed plan-docs in one dir.

    ``*.md`` only (manifests are ``.yaml``); builder-companion docs
    are folded out (same plan identity). ``Path.glob`` skips
    dotfiles, so scope-extension dotfiles never enumerate.
    """
    out: dict[str, Path] = {}
    try:
        candidates = sorted(plans_dir.glob("*.md"))
    except OSError:
        return out
    for doc in candidates:
        if not doc.is_file():
            continue
        slug = doc.stem
        if slug.endswith(_BUILDER_PLAN_SUFFIX):
            continue
        out[slug] = doc
    return out


def derive_plan_states(
    name: str,
    *,
    repo_root: Path | None = None,
    registry: dict[str, ProjectStateSpec] | None = None,
) -> tuple[PlanBuildState, ...] | None:
    """Derive one registered project's plan-docs + REAL build-state,
    FRESH from disk + the git ref graph (AC.PSI.1 — the production
    derivation entry point).

    Returns ``None`` when *name* is not registered (mirrors
    ``derive_project_state``'s clean-None contract); an empty tuple
    when the project has no plans dir (D6 fail-soft — a project
    without governed plans degrades to no entries, never an error).

    The state is derived per call from the plan files present on disk
    and the commit subjects in the ref graph — never persisted, never
    read from a plan's own prose status line — so sealing a slice in
    the real repo changes the reported state on the next call with NO
    doc edit (AC.PSI.1's derived-not-stored outcome).
    """
    spec = resolve_project(name, registry=registry)
    if spec is None:
        return None
    root = repo_root if repo_root is not None else spec.repo_root
    plans_dir = root / PLANS_SUBDIR
    if not plans_dir.is_dir():
        return ()

    active = _enumerate_plan_docs(plans_dir)
    sealed_dir = root / SEALED_SUBDIR
    sealed = _enumerate_plan_docs(sealed_dir) if sealed_dir.is_dir() else {}

    subjects = _git_subject_lines(root)
    states: list[PlanBuildState] = []
    for slug in sorted(set(active) | set(sealed)):
        in_archive = slug in sealed
        doc = active.get(slug, sealed.get(slug))
        evidence = _evidence_for_slug(slug, subjects)
        if in_archive or _latest_evidence_is_seal(evidence):
            # Sealed: archive narrative present (doc convention) OR the
            # newest HEAD-reachable evidence is a completed seal commit
            # (the git build-fact — AC.PSTATE.1 / D-PSTATE.1).
            build_state = BUILD_STATE_SEALED
        elif evidence:
            # Mid-cycle: an apply landed; its seal has not (AC.PSTATE.2).
            build_state = BUILD_STATE_PARTIAL
        else:
            build_state = BUILD_STATE_PENDING
        states.append(
            PlanBuildState(
                project=spec.name,
                slug=slug,
                title=_plan_title(doc, slug),
                doc_path=str(doc),
                build_state=build_state,
                seal_evidence=evidence,
                in_sealed_archive=in_archive,
            )
        )
    return tuple(states)


def derive_all_plan_states(
    *,
    registry: dict[str, ProjectStateSpec] | None = None,
) -> dict[str, tuple[PlanBuildState, ...]]:
    """Derive plan-states for EVERY registered project (D6 — the index
    inherits ``PROJECT_REGISTRY``; hardcoding loam would re-create the
    blind spot one repo over).

    Fail-soft per project: a project whose derivation errors is
    OMITTED (the Slice-D omit-never-wrong discipline); a project with
    no plans dir contributes an empty tuple.
    """
    reg = registry if registry is not None else PROJECT_REGISTRY
    out: dict[str, tuple[PlanBuildState, ...]] = {}
    for name in sorted(reg.keys()):
        try:
            derived = derive_plan_states(name, registry=reg)
        except Exception:  # noqa: BLE001 — fail-soft; omit the project
            continue
        if derived is None:
            continue
        out[name] = derived
    return out
