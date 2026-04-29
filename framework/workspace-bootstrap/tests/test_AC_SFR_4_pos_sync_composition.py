"""AC.SFR.4 — `pos-sync` composition with the synthetic branch is
unchanged from D.3's invariant.

Single-framework restructure (amendment #67). After the restructure:

1. `pos-new-workspace` clones canonical's `framework-only` branch.
2. Canonical advances `pos-v2`; the synthesis (manual or pre-push hook
   driven) advances `framework-only` to a new commit whose parent is
   the prior `framework-only` tip (lockstep ff-graph).
3. From the workspace, `pos-sync` runs `git fetch + git merge --ff-only`
   against `framework-only`'s HEAD; the workspace's `framework/`
   fast-forwards.
4. After `pos-sync`, every file under `<workspace>/framework/<rel>` is
   byte-identical to `framework-only` HEAD's `<rel>`.
5. Files under `<workspace>/workspace/` are byte-identical pre/post
   sync (D.3's HC#6 structural promise carried forward).

The test composes:

- `pos-publish-framework-only.synthesise_framework_only` — to
  initialise the canonical's `framework-only` ref + advance it after a
  follow-on `pos-v2` commit.
- `workspace_bootstrap.new_workspace.bootstrap_new_workspace` — to
  produce the workspace.
- `workspace_sync.cli.main` — to run `pos-sync` against the workspace.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters import tracker_seed
from loam.workspace_bootstrap.new_workspace import bootstrap_new_workspace


def _stub_tracker_seed_runner(**_kwargs):
    return tracker_seed.TrackerSeedResult(
        seeded=False,
        reason="skipped_test_stub",
        classification="user",
        root_id=None,
        descendants_seeded=(),
        value_prop_source=None,
    )


def _git(args: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.rstrip("\n")


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _snapshot_tree_sha(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root))] = _sha256(p)
    return out


def test_AC_SFR_4_pos_sync_fast_forwards_framework_only(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """The full bootstrap-then-sync flow over framework-only.

    Steps:
      1. Construct fixture canonical with pos-v2 + initial
         framework-only synthesis.
      2. `pos-new-workspace` produces a workspace tracking
         framework-only.
      3. Capture `<workspace>/workspace/` tree snapshot pre-sync.
      4. Advance canonical's pos-v2 with a follow-on commit.
      5. Re-synthesise framework-only (lockstep advance).
      6. From the workspace, `pos-sync` runs.
      7. Assert: workspace's framework/ HEAD equals framework-only's
         new HEAD (`git fetch + git merge --ff-only` succeeded).
      8. Assert: workspace files byte-equal post-sync to framework-only
         HEAD's tree (HC#4 carry-forward).
      9. Assert: `<workspace>/workspace/` files byte-identical
         pre/post sync (HC#6 carry-forward).
    """
    pytest.importorskip("workspace_sync.cli")
    from pos_publish_framework_only.synth import (  # noqa: PLC0415
        synthesise_framework_only,
    )
    from loam.workspace_sync.cli import main as sync_cli_main  # noqa: PLC0415

    canonical = make_fixture_canonical(tmp_path / "canonical")
    new_ws = tmp_path / "new-ws"
    agents = tmp_path / "LaunchAgents"

    # Step 2: bootstrap workspace.
    bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        service_manager_dir_override=agents,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )
    framework = new_ws / "framework"
    workspace_state_dir = new_ws / "workspace"

    # Sanity: workspace-side initial HEAD matches canonical's
    # framework-only initial HEAD.
    initial_fo_sha = _git(
        ["rev-parse", "refs/heads/framework-only"], cwd=canonical
    )
    initial_ws_sha = _git(["rev-parse", "HEAD"], cwd=framework)
    assert initial_ws_sha == initial_fo_sha

    # Step 3: snapshot workspace-state.
    pre_workspace_state = _snapshot_tree_sha(workspace_state_dir)
    assert pre_workspace_state, (
        "<workspace>/workspace/ must contain scaffolded state pre-sync"
    )

    # Step 4: advance canonical's pos-v2.
    new_file = canonical / "framework" / "workspace-bootstrap" / "added.py"
    new_file.write_text("# new content for AC.SFR.4 sync\n")
    _git(["add", "-A"], cwd=canonical)
    _git(["commit", "-m", "advance pos-v2 for AC.SFR.4"], cwd=canonical)

    # Step 5: re-synthesise framework-only.
    synth = synthesise_framework_only(canonical)
    assert not synth.no_op
    advanced_fo_sha = synth.framework_only_sha
    assert advanced_fo_sha != initial_fo_sha

    # Step 6: pos-sync from the workspace.
    rc = sync_cli_main(["--workspace", str(new_ws)])
    assert rc == 0, f"pos-sync exited non-zero: {rc}"

    # Step 7: workspace's framework/ now at framework-only HEAD.
    post_ws_sha = _git(["rev-parse", "HEAD"], cwd=framework)
    assert post_ws_sha == advanced_fo_sha, (
        f"AC.SFR.4: workspace HEAD post-sync should equal advanced "
        f"framework-only ({advanced_fo_sha!r}); got {post_ws_sha!r}"
    )

    # Step 8: workspace's framework/<rel> byte-equals framework-only
    # HEAD's <rel>. The advance landed `framework/workspace-bootstrap/
    # added.py` on canonical's pos-v2 → framework-only carries it as
    # `workspace-bootstrap/added.py` at root → workspace lands it at
    # `<workspace>/framework/workspace-bootstrap/added.py`.
    advanced_file = framework / "workspace-bootstrap" / "added.py"
    assert advanced_file.exists()
    assert advanced_file.read_text() == "# new content for AC.SFR.4 sync\n"

    # Step 9: workspace-state byte-identical pre/post sync (HC#6) for
    # files OTHER than pos-sync's own state-record at
    # `<workspace>/workspace/.pos/sync/state.yaml` — D.3 records its
    # own audit trail there. The structural promise is that pos-sync
    # does not mutate workspace files outside its declared state-record
    # surface.
    post_workspace_state = _snapshot_tree_sha(workspace_state_dir)

    def _strip_sync_state(d: dict[str, str]) -> dict[str, str]:
        return {k: v for k, v in d.items() if not k.startswith(".pos/sync/")}

    pre_minus_sync = _strip_sync_state(pre_workspace_state)
    post_minus_sync = _strip_sync_state(post_workspace_state)
    assert pre_minus_sync == post_minus_sync, (
        "AC.SFR.4 / HC#6: <workspace>/workspace/ files mutated by "
        "pos-sync outside its own state-record surface; D.3's "
        "structural-promise broken. "
        f"removed={set(pre_minus_sync) - set(post_minus_sync)!r} "
        f"added={set(post_minus_sync) - set(pre_minus_sync)!r}"
    )
