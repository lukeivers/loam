"""AC3 — apply mode boots out and renames aside.

For each detected orphan: ``launchctl bootout`` is invoked for the
orphan's label; the file is renamed to ``*.orphan-disabled.bak``;
the action is reported on stdout. Plists are NEVER deleted. A
non-recoverable bootout failure leaves the file in place and exits
non-zero.

The launchctl boundary is mocked — no real launchctl invocation in
the suite.
"""

from __future__ import annotations

import io
from pathlib import Path

from loam.orphan_plist_cleanup.cli import main
from loam.orphan_plist_cleanup.launchctl import BootoutResult


class _BootoutRecorder:
    """Test double for the launchctl bootout call."""

    def __init__(
        self,
        *,
        always_ok: bool = True,
        fail_for: set[str] | None = None,
    ) -> None:
        self.always_ok = always_ok
        self.fail_for = fail_for or set()
        self.called_with: list[str] = []

    def __call__(self, label: str) -> BootoutResult:
        self.called_with.append(label)
        if label in self.fail_for:
            return BootoutResult(
                ok=False, returncode=1, stderr="Permission denied"
            )
        return BootoutResult(ok=True, returncode=0, stderr="")


class TestApply:
    def test_apply_invokes_bootout_for_each_orphan_label(
        self, launch_agents_dir: Path
    ) -> None:
        # AC3 step 1: bootout invoked for every orphan label, none
        # for namespaced or unrelated plists.
        recorder = _BootoutRecorder()
        rc = main(
            ["--apply", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=io.StringIO(),
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=recorder,
        )
        assert rc == 0
        assert set(recorder.called_with) == {
            "com.pos-v2.memory-graphiti",
            "com.pos-v2.orchestrator",
            "com.pos.orchestrator",
        }

    def test_apply_renames_orphan_to_bak(
        self, launch_agents_dir: Path
    ) -> None:
        # AC3 step 2: each orphan plist is renamed to
        # ``*.orphan-disabled.bak`` (extension replaced wholesale).
        recorder = _BootoutRecorder()
        rc = main(
            ["--apply", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=io.StringIO(),
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=recorder,
        )
        assert rc == 0

        # Originals gone, .bak twins present.
        assert not (
            launch_agents_dir / "com.pos-v2.memory-graphiti.plist"
        ).exists()
        assert (
            launch_agents_dir
            / "com.pos-v2.memory-graphiti.orphan-disabled.bak"
        ).exists()
        assert not (launch_agents_dir / "com.pos.orchestrator.plist").exists()
        assert (
            launch_agents_dir / "com.pos.orchestrator.orphan-disabled.bak"
        ).exists()

    def test_apply_never_deletes_plist_content(
        self, launch_agents_dir: Path
    ) -> None:
        # AC3 + reversibility constraint: rename, don't delete. The
        # renamed file's content matches the original byte-for-byte.
        original_body = (
            launch_agents_dir / "com.pos-v2.memory-graphiti.plist"
        ).read_text()
        recorder = _BootoutRecorder()
        main(
            ["--apply", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=io.StringIO(),
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=recorder,
        )
        renamed_body = (
            launch_agents_dir
            / "com.pos-v2.memory-graphiti.orphan-disabled.bak"
        ).read_text()
        assert renamed_body == original_body

    def test_apply_does_not_touch_namespaced_plists(
        self, launch_agents_dir: Path
    ) -> None:
        # AC5 still holds in apply mode: namespaced + unrelated
        # plists are untouched.
        recorder = _BootoutRecorder()
        main(
            ["--apply", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=io.StringIO(),
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=recorder,
        )
        # Namespaced plists still in place, untouched.
        assert (
            launch_agents_dir / "com.loam.alpha.memory-graphiti.plist"
        ).exists()
        assert (
            launch_agents_dir / "com.loam.alpha.orchestrator.plist"
        ).exists()
        # Unrelated plists still in place.
        assert (launch_agents_dir / "com.apple.something.plist").exists()
        # No bootout was called for any namespaced label.
        assert all(
            "alpha" not in label for label in recorder.called_with
        )

    def test_apply_reports_each_action_on_stdout(
        self, launch_agents_dir: Path
    ) -> None:
        # AC3 step 3: each successful remediation is reported on stdout.
        recorder = _BootoutRecorder()
        stdout = io.StringIO()
        main(
            ["--apply", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=stdout,
            stderr=io.StringIO(),
            platform="darwin",
            bootout_fn=recorder,
        )
        out = stdout.getvalue()
        assert "com.pos-v2.memory-graphiti.plist" in out
        assert "com.pos-v2.memory-graphiti.orphan-disabled.bak" in out
        assert "com.pos.orchestrator.plist" in out

    def test_apply_bootout_failure_leaves_file_in_place(
        self, launch_agents_dir: Path
    ) -> None:
        # AC3 + fail-closed constraint: when bootout fails (non-
        # recoverable, not the "service not loaded" variant), the
        # file is left in place and the tool exits non-zero. Other
        # orphans on the same run are still remediated.
        recorder = _BootoutRecorder(
            fail_for={"com.pos-v2.memory-graphiti"}
        )
        stderr = io.StringIO()
        rc = main(
            ["--apply", "--launch-agents-dir", str(launch_agents_dir)],
            stdout=io.StringIO(),
            stderr=stderr,
            platform="darwin",
            bootout_fn=recorder,
        )
        assert rc == 1
        # Failed orphan: original still on disk, no .bak twin.
        assert (
            launch_agents_dir / "com.pos-v2.memory-graphiti.plist"
        ).exists()
        assert not (
            launch_agents_dir
            / "com.pos-v2.memory-graphiti.orphan-disabled.bak"
        ).exists()
        # Other orphans still remediated.
        assert not (
            launch_agents_dir / "com.pos-v2.orchestrator.plist"
        ).exists()
        assert (
            launch_agents_dir / "com.pos-v2.orchestrator.orphan-disabled.bak"
        ).exists()
        # Failure surfaced on stderr.
        assert "bootout failed" in stderr.getvalue()
        assert "com.pos-v2.memory-graphiti" in stderr.getvalue()
