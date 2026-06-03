"""The per-project STATE probe spec for the LitRPG production workspace
(Slice C registry extension — work-streams Increment 1, AC.WS.LIVE.1).

LitRPG ("Patch Notes for Reality") is NOT a code project: it is a
content-production pipeline. Its ground-truth "build state" is
PRODUCTION PROGRESS — which pipeline LAYERS have been produced and how
far the chapter draft has advanced — derived from the litrpg-writer
workspace on disk + the git ref graph, never from a prose status line.

This is the DIRECT ANALOGUE of :mod:`loam_cli.audit.cairn_state`,
re-keyed to LitRPG's REAL markers (production-pipeline layer
directories + their introducing commit's ancestry), proving the STATE
engine generalizes to a CONTENT project, not merely a second
code-shaped hardcode. It REUSES the repo-agnostic engine wholesale: the
:class:`Liveness` classes, the :class:`ComponentState` row shape, the
:class:`StateOfLoam` record, and the ``merge-base --is-ancestor`` git
probe. The ONLY new logic is the layer-presence + introducing-commit
production classifier.

The LitRPG production pipeline (the multiverse-qa layer stack) is the
ground-truth surface:

  * ``multiverse-qa/layer-N/`` — a produced pipeline layer is a layer
    directory carrying at least one content ``.md`` file (a layer dir
    that is absent or empty is an UNBUILT production stage).
  * the git commit that FIRST added that layer directory is an ancestor
    of HEAD → the layer is MERGED (produced + on the mainline). Present
    but not yet on the mainline → SEALED. Present but git cannot resolve
    the introducing commit → UNKNOWN (fail-safe — never a false green).

LitRPG lives in the pos3 workspace tree (a git repo), so the same
ancestry verdict cairn uses applies. The classifier is keyed to
LitRPG's layer markers; everything else is the shared engine.

This is what lets the persona derive LitRPG's REAL production state
(e.g. "layer-4 drafting in motion, layers 6/7 not yet produced")
instead of describing it from stale prose — the same accuracy anchor
Slice C built for loam + cairn, now extended to the LitRPG stream.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from loam_cli.audit.probe import Liveness, _git_is_ancestor
from loam_cli.audit.record import ComponentState, StateOfLoam, _head_sha

#: The live LitRPG production workspace root (the litrpg-writer
#: multiverse-qa pipeline). Tests override this with a fixture repo;
#: production reads the live workspace.
DEFAULT_LITRPG_REPO_ROOT = Path(
    "/Users/lukeivers/pos3/workspace/products/litrpg-writer/workspace/multiverse-qa"
)


@dataclass(frozen=True)
class LayerProbeSpec:
    """A LitRPG production-layer probe spec: a name + the layer directory
    (relative to the workspace root) whose presence + introducing-commit
    ancestry is the ground-truth production marker.
    """

    name: str
    layer_relpath: str


def _layer_content_files(layer_dir: Path) -> list[Path]:
    """Content ``.md`` files anywhere under a production-layer dir.

    A layer is "produced" when it carries at least one content markdown
    file (the layer's output). An absent dir, or a dir with no ``.md``
    content (only scaffolding), is an UNBUILT production stage. Searches
    recursively because a layer's output may be nested (e.g.
    ``layer-4/book-1/chapter-02.md``).
    """
    if not layer_dir.is_dir():
        return []
    return [p for p in layer_dir.rglob("*.md") if p.is_file()]


def _first_add_commit(repo_root: Path, layer_relpath: str) -> str | None:
    """The git SHA that FIRST added the layer directory (the commit that
    introduced that production stage), or ``None`` when git cannot
    resolve one.

    Uses ``git log --reverse --diff-filter=A`` over the layer path and
    takes the earliest add — the introduction point. This is LitRPG's
    equivalent of cairn's introducing-commit marker, derived from the
    ref graph.
    """
    proc = subprocess.run(
        [
            "git",
            "log",
            "--reverse",
            "--diff-filter=A",
            "--format=%H",
            "--",
            layer_relpath,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    return lines[0] if lines else None


def classify_layer_production_status(
    repo_root: Path,
    layer_relpath: str,
) -> tuple[Liveness, str]:
    """Classify a LitRPG production layer's state from LitRPG's REAL
    markers (layer-dir presence + introducing-commit ancestry).

    Resolution (ground-truth only — no prose):

      * layer dir ABSENT or carries no content ``.md`` →
        :attr:`Liveness.UNBUILT` (production stage not yet produced).
      * layer PRESENT (>=1 content file) AND its introducing commit is
        an ancestor of HEAD → :attr:`Liveness.MERGED` (produced + on the
        mainline — the fully-landed production state).
      * layer PRESENT but its introducing commit is a real commit NOT
        reachable from HEAD → :attr:`Liveness.SEALED` (produced on a side
        branch, not on the current line).
      * layer PRESENT but git cannot resolve / verify the introducing
        commit → :attr:`Liveness.UNKNOWN` (fail-safe: never a false
        green).

    Returns (liveness, evidence) — evidence is the human-readable trail
    that produced the class, matching the engine's evidence convention.
    """
    layer_dir = repo_root / layer_relpath
    content = _layer_content_files(layer_dir)
    if not content:
        return (
            Liveness.UNBUILT,
            f"no production output at {layer_relpath} (layer absent or empty)",
        )

    intro = _first_add_commit(repo_root, layer_relpath)
    n = len(content)
    if intro is None:
        return (
            Liveness.UNKNOWN,
            f"{layer_relpath} present ({n} content files) but git could not "
            f"resolve its introducing commit (indeterminate — fail-safe)",
        )

    ancestry = _git_is_ancestor(repo_root, intro)
    if ancestry is True:
        return (
            Liveness.MERGED,
            f"{layer_relpath} present ({n} content files); introducing "
            f"commit {intro[:9]} is an ancestor of HEAD (produced on mainline)",
        )
    if ancestry is False:
        return (
            Liveness.SEALED,
            f"{layer_relpath} present ({n} content files); introducing "
            f"commit {intro[:9]} not reachable from HEAD (side branch)",
        )
    return (
        Liveness.UNKNOWN,
        f"{layer_relpath} present ({n} content files); introducing "
        f"commit {intro[:9]} not a known git object (indeterminate — fail-safe)",
    )


def default_litrpg_layer_specs() -> tuple[LayerProbeSpec, ...]:
    """LitRPG's production-pipeline layers — the markers whose presence
    derives the real production progress (which pipeline stages have
    output) the persona surfaces for the LitRPG stream.

    The layer stack is the multiverse-qa production pipeline: premise /
    protagonist / world-systems / antagonist / narrative-arc /
    line-edit / final, plus the chapter draft surface. Names are
    plain-language production-stage labels (no internal IDs leak to the
    surface — the work_visibility vocab invariant).
    """
    return (
        LayerProbeSpec(name="premise-world", layer_relpath="layer-1"),
        LayerProbeSpec(name="protagonist", layer_relpath="layer-2"),
        LayerProbeSpec(name="world-systems", layer_relpath="layer-3"),
        LayerProbeSpec(name="narrative-arc", layer_relpath="layer-5"),
        LayerProbeSpec(name="chapter-drafts", layer_relpath="layer-4"),
        LayerProbeSpec(name="line-edit", layer_relpath="layer-6"),
        LayerProbeSpec(name="final-pass", layer_relpath="layer-7"),
    )


def litrpg_state_record(
    repo_root: Path | None = None,
    *,
    layer_specs: tuple[LayerProbeSpec, ...] | None = None,
) -> StateOfLoam:
    """Generate LitRPG's per-project production-STATE record FRESH from
    ground truth.

    Reuses the engine's :class:`StateOfLoam` / :class:`ComponentState`
    record types; the only LitRPG-specific logic is the layer
    production classifier. Nothing is persisted — the record regenerates
    from disk + the git ref graph on every call, so it cannot have
    drifted (the same generate-fresh invariant as cairn's
    ``cairn_state_record``).

    *repo_root* defaults to the live LitRPG workspace
    (:data:`DEFAULT_LITRPG_REPO_ROOT`); tests pass a fixture repo.
    """
    root = (repo_root or DEFAULT_LITRPG_REPO_ROOT).resolve()
    specs = layer_specs if layer_specs is not None else default_litrpg_layer_specs()

    rows: list[ComponentState] = []
    for spec in specs:
        liveness, evidence = classify_layer_production_status(
            root, spec.layer_relpath
        )
        rows.append(
            ComponentState(
                name=spec.name,
                liveness=liveness,
                kind="component",
                evidence=evidence,
            )
        )

    return StateOfLoam(head_sha=_head_sha(root), components=tuple(rows))
