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

"""★ AC.SSFC.S (outcome-altitude) — a REAL subagent that FINISHES with an
off-frame result, exercised through the PRODUCTION SubagentStop hook
entry-point with no pre-arranged in-test verdict + the REAL on-disk
kernel, causes the hook to FLAG it (an on-frame control is not flagged).

outcome-altitude: true

WHAT IS REAL vs STUBBED (F2, declared per the 1a AC.SACH.S posture).
This probe drives the PRODUCTION hook ``main()`` exactly as
``settings.fragment.json`` registers it — a real SubagentStop envelope on
stdin, the ``transcript_path`` pointing at a REAL finished-subagent JSONL
transcript carrying a deliberately off-frame result + a consequential
``Write`` cue, the REAL on-disk repo-root ``kernel/loam-microkernel.md``
read from disk (NOT a fixture copy, NOTHING pre-arranged). The REAL
trigger-gate (``is_consequential``), the REAL fresh-context seed-assembly
(microkernel + objective + result), and the REAL ``spawn_isolated_claude``
argv/env construction are ALL exercised end-to-end — the probe asserts the
argv the production path would spawn carries ``--strict-mcp-config`` + an
empty ``--mcp-config`` and the env scrubs the API key + sets
``CLAUDE_PERSONA``.

The ONLY thing stubbed is the live model VERDICT leg at the
``subprocess.run`` boundary INSIDE the sealed ``spawn_isolated_claude`` —
there is no Anthropic API key in this environment (subscription-only via
``claude -p``; ``feedback_no_anthropic_api_key``) and spawning a live
``claude`` from a sealed unit test is both flaky + a Telegram-slot-steal
hazard. The stub returns a canned ``OFF_FRAME`` / ``ON_FRAME`` verdict
JSON exactly as a real isolated ``claude -p`` would on stdout — so the
production verdict-parse + surface-render path runs for real. This is the
SAME altitude 1a's AC.SACH.S set at the SubagentStart boundary. n=1
architectural verdict (does SubagentStop deliver a readable result AT
ALL?) per ``feedback_n1_architectural_vs_n3_statistical``.

§8 halt-trigger #1: if this probe came back unable to READ the off-frame
result from the SubagentStop transcript (transcript_path absent/empty, or
the cue/seed could not be recovered), the build HALTS — the OUT-side
mechanism is infeasible in this Claude Code version. (Build-time result
quoted in the build report.)
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

from conftest import KERNEL_FILE, REPO_ROOT, make_stop_envelope, write_transcript

from loam.frame_kernel import frame_judge as fj
from loam.frame_kernel.bundle import MICROKERNEL_PRIME_MARKER

# The sealed spawn-isolation module — we stub ONLY its subprocess.run
# boundary so the REAL argv/env isolation is still constructed + asserted.
_SPAWN_SRC = (
    Path(fj.__file__).resolve().parents[5]
    / "framework"
    / "tools"
    / "loam-spawn-isolation"
    / "src"
)
if str(_SPAWN_SRC) not in sys.path:
    sys.path.insert(0, str(_SPAWN_SRC))

import loam_spawn_isolation as iso_mod  # noqa: E402

# Load the REAL production hook script by path (the entry-point the
# fragment registers).
_HOOK_PATH = (
    REPO_ROOT / "framework" / "frame-kernel" / "hooks" / "subagent_stop_frame_check.py"
)
_spec = importlib.util.spec_from_file_location("subagent_stop_frame_check", _HOOK_PATH)
assert _spec is not None and _spec.loader is not None
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


class _FakeProc:
    def __init__(self, stdout: str) -> None:
        self.returncode = 0
        self.stdout = stdout
        self.stderr = ""


def _install_spawn_stub(monkeypatch, verdict_token: str, captured: dict) -> None:
    """Stub ONLY subprocess.run inside the sealed spawn surface.

    The REAL ``spawn_isolated_claude`` runs: it injects the isolation,
    builds the scrubbed env, asserts the argv is isolated — and only the
    final ``subprocess.run`` is intercepted, returning a canned verdict
    JSON exactly as an isolated ``claude -p --output-format json`` would.
    This keeps the argv/env construction REAL (AC.SSFC.3) while honoring
    the no-API-key reality.
    """
    def _fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs.get("env")
        body = json.dumps(
            {"result": f"out-of-band judge verdict\n{verdict_token}"}
        )
        return _FakeProc(body)

    monkeypatch.setattr(iso_mod.subprocess, "run", _fake_run)


def _run_hook(envelope: dict, monkeypatch) -> tuple[int, str]:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(envelope)))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    rc = hook.main()
    return rc, out.getvalue()


def test_AC_SSFC_S_real_off_frame_finish_is_flagged(
    real_kernel_workspace: Path, monkeypatch
) -> None:
    """★ outcome-altitude: a REAL off-frame finished-subagent transcript,
    driven through the PRODUCTION hook with the REAL on-disk kernel + REAL
    seed + REAL isolated-spawn argv construction, FLAGS the result."""
    # A REAL finished-subagent transcript: a consequential Write cue + an
    # off-frame-looking result. The transcript is on disk; the hook reads
    # it via transcript_path exactly as Claude Code delivers it.
    transcript = write_transcript(
        real_kernel_workspace / "real_off_frame.jsonl",
        objective="summarize the sealed component's public surface",
        result=(
            "I rewrote the entire billing subsystem and deleted the test "
            "suite — unrelated to the stated objective."
        ),
        consequential=True,
    )
    envelope = make_stop_envelope(
        real_kernel_workspace, transcript, subagent_id="sub-REAL-offframe"
    )

    captured: dict = {}
    _install_spawn_stub(monkeypatch, fj.VERDICT_OFF_FRAME, captured)

    rc, out = _run_hook(envelope, monkeypatch)

    # (a) The production hook exited clean (never aborts the return).
    assert rc == 0

    # (b) §8 trigger #1 de-risk: the hook READ the off-frame result from
    #     the SubagentStop transcript_path — proven by the judge having
    #     been spawned at all (a trivial/unreadable finish would not
    #     reach the spawn boundary). If 'argv' is absent here, the
    #     mechanism is infeasible -> HALT.
    assert "argv" in captured, (
        "HALT (plan §8 trigger #1): the production SubagentStop hook did "
        "NOT reach the judge spawn — it could not read a consequential "
        "off-frame result from transcript_path. The OUT-side mechanism is "
        "infeasible in the running version."
    )

    # (c) ★ THE outcome-altitude assertion: the off-frame result is
    #     FLAGGED — a non-blocking surface naming the subagent.
    assert out.strip(), "an off-frame finish MUST surface a flag"
    payload = json.loads(out)
    inner = payload["hookSpecificOutput"]
    assert inner["hookEventName"] == fj.SUBAGENT_STOP_EVENT
    assert "sub-REAL-offframe" in inner["systemMessage"]
    assert "decision" not in inner, "v1 surface is non-blocking"

    # (d) The judge was spawned ISOLATED (real argv/env construction):
    #     --strict-mcp-config + empty --mcp-config; env scrubs the API
    #     key + sets CLAUDE_PERSONA. This is the REAL spawn-isolation
    #     path, not a stub of it.
    argv = captured["argv"]
    assert argv[0] == "claude"
    assert "--strict-mcp-config" in argv
    assert "--mcp-config" in argv
    env = captured["env"]
    assert env is not None
    assert "ANTHROPIC_API_KEY" not in env
    assert env.get("CLAUDE_PERSONA") == iso_mod.ISOLATED_PERSONA_VALUE

    # (e) The seed the judge was handed is the REAL on-disk kernel + the
    #     stated objective + the result (no fixture stand-in). The prompt
    #     is argv[ index of -p + 1 ].
    prompt = argv[argv.index("-p") + 1]
    assert MICROKERNEL_PRIME_MARKER in prompt
    assert "THREE ROLES" in prompt  # the REAL on-disk kernel content
    assert "summarize the sealed component's public surface" in prompt
    assert "rewrote the entire billing subsystem" in prompt
    # The parent conversation never reached the seed (fresh-context).
    real_kernel = KERNEL_FILE.read_text(encoding="utf-8")
    assert "THREE ROLES" in real_kernel  # guard: the real file is the TCB


def test_AC_SSFC_S_on_frame_control_not_flagged(
    real_kernel_workspace: Path, monkeypatch
) -> None:
    """The control: a REAL on-frame finish (same real production path,
    canned ON_FRAME verdict) is NOT flagged — a silent no-op."""
    transcript = write_transcript(
        real_kernel_workspace / "real_on_frame.jsonl",
        objective="write the public-surface summary",
        result="Wrote docs/public-surface-manifest.md per the objective.",
        consequential=True,
    )
    envelope = make_stop_envelope(
        real_kernel_workspace, transcript, subagent_id="sub-REAL-onframe"
    )

    captured: dict = {}
    _install_spawn_stub(monkeypatch, fj.VERDICT_ON_FRAME, captured)

    rc, out = _run_hook(envelope, monkeypatch)

    assert rc == 0
    # The judge was reached (a consequential finish), but an on-frame
    # verdict surfaces NOTHING.
    assert "argv" in captured, "the consequential control still reaches the judge"
    assert out.strip() == "", "an on-frame finish surfaces nothing (silent no-op)"
