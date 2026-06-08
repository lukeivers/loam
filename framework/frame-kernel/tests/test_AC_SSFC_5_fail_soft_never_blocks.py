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

"""AC.SSFC.5 — the hook NEVER aborts or blocks a subagent's return. Any
internal error (missing kernel, unreadable transcript, judge spawn
failure/timeout, malformed verdict) still lets the subagent finish
cleanly, AND the off-frame surface is non-blocking (a flag, not a hard
block) for v1.

Each degenerate path is fed to the production hook entry-point
(``main()``) and to ``evaluate``; the assertions are (a) clean exit 0,
(b) no raise, (c) no hard-block decision. Mirrors 1a's AC.SACH.4 exit-0
contract.
"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

from conftest import REPO_ROOT, make_stop_envelope, write_transcript

from loam.frame_kernel import frame_judge as fj

# Load the hook script module by path (it lives under hooks/, not the
# package) so we exercise the REAL production entry-point.
_HOOK_PATH = (
    REPO_ROOT / "framework" / "frame-kernel" / "hooks" / "subagent_stop_frame_check.py"
)
_spec = importlib.util.spec_from_file_location("subagent_stop_frame_check", _HOOK_PATH)
assert _spec is not None and _spec.loader is not None
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


def _run_hook(stdin_text: str, monkeypatch) -> tuple[int, str]:
    """Drive the hook's main() with *stdin_text*; return (rc, stdout)."""
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    rc = hook.main()
    return rc, out.getvalue()


def test_empty_stdin_exits_clean_no_output(monkeypatch) -> None:
    """No envelope -> exit 0, no surface, never blocks."""
    rc, out = _run_hook("", monkeypatch)
    assert rc == 0
    assert out == ""


def test_malformed_json_exits_clean(monkeypatch) -> None:
    """Garbage stdin -> exit 0, no raise."""
    rc, out = _run_hook("}{not json", monkeypatch)
    assert rc == 0
    assert out == ""


def test_absent_transcript_does_not_block(real_kernel_workspace: Path) -> None:
    """A transcript_path that does not exist -> no cue read, no spawn,
    evaluate returns None (no block)."""
    envelope = make_stop_envelope(
        real_kernel_workspace, real_kernel_workspace / "nonexistent.jsonl"
    )
    assert fj.evaluate(envelope) is None


def test_unreadable_transcript_does_not_raise(
    real_kernel_workspace: Path,
) -> None:
    """A transcript path that is a DIRECTORY (read raises) -> fail-soft
    None, no raise."""
    bad = real_kernel_workspace / "as_dir.jsonl"
    bad.mkdir()
    envelope = make_stop_envelope(real_kernel_workspace, bad)
    assert fj.evaluate(envelope) is None


def test_judge_spawn_failure_does_not_block(
    real_kernel_workspace: Path,
) -> None:
    """The judge spawn raising -> fail-soft None (the subagent return is
    never blocked)."""
    transcript = write_transcript(
        real_kernel_workspace / "t.jsonl",
        objective="o",
        result="r",
        consequential=True,
    )
    envelope = make_stop_envelope(real_kernel_workspace, transcript)

    def _boom(prompt: str, **_kw):
        raise RuntimeError("spawn failed")

    assert fj.evaluate(envelope, _run_judge=_boom) is None


def test_judge_returns_none_treated_as_not_off_frame(
    real_kernel_workspace: Path,
) -> None:
    """A None judge result (spawn failure / timeout sentinel) ->
    NOT-off-frame (no false surface)."""
    transcript = write_transcript(
        real_kernel_workspace / "t.jsonl",
        objective="o",
        result="r",
        consequential=True,
    )
    envelope = make_stop_envelope(real_kernel_workspace, transcript)
    assert fj.evaluate(envelope, _run_judge=lambda *_a, **_k: None) is None


def test_malformed_verdict_fails_soft_not_off_frame() -> None:
    """An unparseable verdict -> parsed=False, off_frame=False (a judge
    malfunction never manufactures a false off-frame block)."""
    v = fj.parse_verdict("garbage with no verdict token at all")
    assert v.parsed is False
    assert v.off_frame is False
    v_none = fj.parse_verdict(None)
    assert v_none.parsed is False and v_none.off_frame is False


def test_missing_kernel_does_not_abort_seed(tmp_path: Path) -> None:
    """A workspace with no kernel file -> the seed degrades to the
    missing-marker; assemble_seed never raises."""
    transcript = write_transcript(
        tmp_path / "t.jsonl",
        objective="o",
        result="r",
        consequential=True,
    )
    ctx = fj.parse_stop_envelope(make_stop_envelope(tmp_path, transcript))
    seed = fj.assemble_seed(fj.read_subagent_result(ctx))
    from loam.frame_kernel.bundle import MISSING_KERNEL_MARKER

    assert MISSING_KERNEL_MARKER in seed


def test_full_hook_off_frame_emits_nonblocking_surface(
    real_kernel_workspace: Path, monkeypatch
) -> None:
    """End-to-end through main(): an off-frame finish emits a
    systemMessage envelope (non-blocking), exit 0, no decision:block."""
    transcript = write_transcript(
        real_kernel_workspace / "t.jsonl",
        objective="o",
        result="r",
        consequential=True,
    )
    envelope = make_stop_envelope(
        real_kernel_workspace, transcript, subagent_id="sub-FS"
    )

    # Stub the judge at the module boundary so main() exercises the real
    # gate + seed + emit path with a deterministic off-frame verdict.
    monkeypatch.setattr(
        fj, "run_judge", lambda *_a, **_k: "reason\n" + fj.VERDICT_OFF_FRAME
    )

    rc, out = _run_hook(json.dumps(envelope), monkeypatch)
    assert rc == 0
    payload = json.loads(out)
    inner = payload["hookSpecificOutput"]
    assert inner["hookEventName"] == fj.SUBAGENT_STOP_EVENT
    assert "systemMessage" in inner
    assert "decision" not in inner, "v1 surface is non-blocking, not a block"
