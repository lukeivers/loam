"""AC.FBMT1.S — outcome-altitude smoke for the four FBM T1 primitives.

Marked ``outcome-altitude: true``. Exercises:
  (a) Write a memory file via the worker — verify ``context:`` block
      present (T1.2).
  (b) Write a second memory file with ``superseded-by:`` pointing at
      the first — verify the retrieval ranker demotes the second
      (T1.1).
  (c) Seal a synthetic amendment in a tmpfs repo where the plan-doc
      slug overlaps a seeded FIDRAFT entry — verify the cleanup hook
      fires its surface (T1.3).
  (d) Verify the plan-doc moved from ``docs/plans/`` to
      ``docs/plans/sealed/`` in the seal commit (T1.4).

The test invokes the production memory-write worker, the production
retrieval contributor, the production ``loam amend seal`` CLI, and
the production FIDRAFT cleanup hook in sequence; no pre-arranged
state beyond the synthetic memory files and the synthetic plan-doc
+ manifest at test setup.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4 AC.FBMT1.S.
"""

from __future__ import annotations

import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pytest

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww
from loam.primary_persona.file_memory import (
    FileMemoryStore,
    _split_frontmatter,
    build_file_backed_memory_client,
    memory_dir_for_workspace,
)
from loam_amend.cli import main as cli_main

from test_seal import (
    _git,
    _make_amendment_commit,
    _write_manifest,
    sealed_repo,  # noqa: F401 — pytest fixture
)


def _write_plan_doc_with_section_14(plan_path: Path) -> None:
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        textwrap.dedent(
            """
            # Smoke fixture plan doc

            ## 1. Summary

            placeholder.

            ## 14. Method-decision record

            placeholder body.
            """
        ).lstrip(),
        encoding="utf-8",
    )


def test_AC_FBMT1_S_end_to_end_smoke(sealed_repo, capsys, tmp_path: Path):
    """Single end-to-end test exercising T1.1 + T1.2 + T1.3 + T1.4
    against production entry-points."""
    # ------------------------------------------------------------------
    # (a) T1.2 — memory write via worker produces a context: block.
    # ------------------------------------------------------------------
    # Use a SEPARATE tmpfs workspace for the memory portion (the
    # sealed_repo fixture is a git repo for the seal portion; memory
    # writes don't go there).
    ws_root = tmp_path / "smoke-workspace"
    (ws_root / "workspace" / ".pos").mkdir(parents=True)
    (ws_root / "workspace" / ".loam" / "memory").mkdir(parents=True)

    mwq.enqueue(
        workspace_root=ws_root,
        turn_id="smoke-1",
        session_id="smoke-sess",
        user_message="first memory",
        assistant_reply="first reply",
        triggering_msg_id="msg-smoke-1",
        active_task_id="task-smoke-1",
        cwd=str(ws_root),
        active_files=["a.py"],
    )
    counters = mww.drain_once(
        workspace_root=ws_root,
        client_factory=build_file_backed_memory_client,
        workspace_slug="smokegroup",
    )
    assert counters["ok"] == 1

    # Verify the on-disk file carries the context: block (T1.2).
    memory_dir = memory_dir_for_workspace(ws_root)
    memory_files = list((memory_dir / "episodes" / "smokegroup").rglob("*.md"))
    assert len(memory_files) == 1
    first_memory_path = memory_files[0]
    first_content = first_memory_path.read_text(encoding="utf-8")
    first_front, _ = _split_frontmatter(first_content)
    assert "context" in first_front
    ctx = first_front["context"]
    assert ctx["triggering_msg_id"] == "msg-smoke-1"
    assert ctx["active_files"] == ["a.py"]

    # ------------------------------------------------------------------
    # (b) T1.1 — second memory file with superseded-by ranks below
    # the first.
    # ------------------------------------------------------------------
    # Write a second memory file using the FileMemoryStore directly
    # (the worker uses turn-id as filename; this exposes the path
    # we need for the supersession marker).
    store = FileMemoryStore(memory_dir=memory_dir)
    ref_time = datetime(2026, 5, 21, 10, 0, 0, tzinfo=timezone.utc)
    store.write_episode(
        name="turn/second-rule",
        body="quokka platypus rare lexical match shared with first",
        source_description="smoke",
        reference_time=ref_time,
        source="message",
        group_id="smokegroup",
        context={
            "triggering_msg_id": "msg-smoke-2",
            "active_task_id": None,
            "cwd": str(ws_root),
            "active_files": [],
        },
    )
    second_files = list(
        (memory_dir / "episodes" / "smokegroup").rglob("second-rule.md")
    )
    assert second_files
    second_memory_path = second_files[0]

    # Also rewrite first memory's body to also include the rare
    # tokens, so both files match the query. Then annotate the
    # second as superseded-by the first.
    first_text = first_memory_path.read_text(encoding="utf-8")
    first_text_updated = first_text.replace(
        "[user]",
        "quokka platypus first rule wins\n[user]",
    )
    first_memory_path.write_text(first_text_updated, encoding="utf-8")
    second_text = second_memory_path.read_text(encoding="utf-8")
    relative_to_first = first_memory_path.relative_to(
        second_memory_path.parent
    )
    second_text_annotated = second_text.replace(
        "group_id: smokegroup\n",
        f"group_id: smokegroup\nsuperseded-by: {relative_to_first}\n",
    )
    second_memory_path.write_text(second_text_annotated, encoding="utf-8")

    # Re-index both files (the supersession marker is post-write).
    # Easiest: drop the index file and let the next search rebuild
    # from disk. The index lives at memory_dir / search-index.sqlite.
    idx = memory_dir / "search-index.sqlite"
    if idx.exists():
        idx.unlink()
    # Re-create the store to drop the cached connection.
    fresh_store = FileMemoryStore(memory_dir=memory_dir)
    # Re-index by reading each file and triggering _index_episode
    # via write_episode round-trip is too disruptive; the grep
    # fallback path handles supersession too, and it runs when the
    # FTS5 index has no hits. Drop the index → grep fires.
    result = fresh_store.search(
        query="quokka platypus",
        group_ids=["smokegroup"],
        num_results=5,
    )
    paths = [ep["path"] for ep in result["episodes"]]
    assert paths, "no episodes returned"
    idx_first = next(
        (i for i, p in enumerate(paths) if p.endswith(first_memory_path.name)),
        None,
    )
    idx_second = next(
        (i for i, p in enumerate(paths)
         if p.endswith(second_memory_path.name)),
        None,
    )
    assert idx_first is not None
    assert idx_second is not None
    assert idx_first < idx_second, (
        f"superseded (second) should rank below unsuperseded (first); "
        f"got positions first={idx_first}, second={idx_second}"
    )

    # ------------------------------------------------------------------
    # (c) + (d) — seal a synthetic amendment; verify T1.3 FIDRAFT
    # cleanup surface fires AND T1.4 plan-doc moved.
    # ------------------------------------------------------------------
    repo = sealed_repo
    # FIDRAFT entry that shares tokens with the plan-doc slug.
    fidraft = repo / "docs" / "FUTURE_IDEAS_DRAFT.md"
    fidraft.parent.mkdir(parents=True, exist_ok=True)
    fidraft.write_text(
        "- **Quokka platypus tier-1 smoke entry.** test of the "
        "FBM T1 smoke flow.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", "docs/FUTURE_IDEAS_DRAFT.md")
    _git(repo, "commit", "-q", "-m", "fixture: smoke FIDRAFT")

    plan_path = repo / "docs" / "plans" / "quokka-platypus-tier-1-smoke.md"
    _write_plan_doc_with_section_14(plan_path)
    _git(repo, "add", "--", "docs/plans/quokka-platypus-tier-1-smoke.md")
    _git(repo, "commit", "-q", "-m", "fixture: smoke plan-doc")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=1099,
        slug="quokka-platypus-tier-1-smoke",
        seal_description="smoke",
    )
    _make_amendment_commit(repo, "alpha", payload="smoke")

    capsys.readouterr()
    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0

    out = capsys.readouterr().out
    # (c) T1.3 — FIDRAFT cleanup surface fires + names matching entry.
    assert "FIDRAFT cleanup surface" in out
    assert "quokka-platypus" in out

    # (d) T1.4 — plan-doc + manifest moved to docs/plans/sealed/.
    assert not plan_path.exists()
    assert not manifest_path.exists()
    sealed_plan = (
        repo / "docs" / "plans" / "sealed" / plan_path.name
    )
    sealed_manifest = (
        repo / "docs" / "plans" / "sealed" / manifest_path.name
    )
    assert sealed_plan.exists()
    assert sealed_manifest.exists()
