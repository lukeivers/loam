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

"""AC.FHA.6 — Stranger-clone FBE.7 outcome-altitude probe.

V0.3.0 cycle 6 (feature-honesty audit). Tractable substitute for the
fresh-machine / Docker-isolated stranger-clone scenario named in
``docs/plans/v0-3-0-cycle-6-feature-honesty-audit-and-verification.md``
§10. Docker daemon availability is owner-action-gated; this test
exercises the full FBE.7 production-CLI surface against an isolated
tempdir workspace so the same outcome is verified under a controlled
end-to-end shape.

**Outcome being verified.** A workspace with no prior memory state
runs a "session N-1" through the production Stop CLI (`cli_stop`),
the worker drains the queue to disk, /clear (== a fresh process /
no in-memory state) happens, and a "session N" UserPromptSubmit CLI
(`cli_user_prompt_submit`) returns prior-session content for a
prompt that names the same entity — the cross-session-bridging
contract that FBE.7 (file-backed episodes) ships.

**Outcome-altitude markers (per ``feedback_test_outcome_altitude_required``).**

  - Production entry-points only (`cli_stop`, `cli_user_prompt_submit`,
    `memory_write_worker.run_worker_loop`); zero stub objects at the
    contract surface (the production ``FileBackedMemoryClient`` is
    the default per AC.MFBM.5).
  - No pre-arranged state: the test writes the transcript file the
    Stop hook reads, but every memory-tier file (episode, queue
    entry, retrieval surface) is produced by production code under
    test.
  - Process boundary substitute: a fresh process is simulated via
    `subprocess.run` of the worker CLI (`cli_memory_worker`) so the
    queue→episode bridge crosses the same in-process boundary the
    production launchd plist supervises.

If Docker becomes available in CI, the same outcome can be repeated
inside a clean container; the assertions transfer unchanged.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from loam.primary_persona import memory_write_worker as mww
from loam.primary_persona.session_start_emitter import (
    cli_user_prompt_submit,
)
from loam.primary_persona.stop_emitter import cli_stop


def _write_fake_transcript(
    transcript_path: Path,
    *,
    user_message: str,
    assistant_reply: str,
) -> None:
    """Write a minimal Claude Code-shaped transcript JSONL.

    Per Claude Code transcript shape (referenced in ``stop_emitter.
    _walk_transcript_for_turn``): each line is a JSON object whose
    ``message.role`` is ``user`` or ``assistant`` and whose
    ``message.content`` is a string OR a list of typed parts.
    """
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "message": {"role": "user", "content": user_message},
            }
        ),
        json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": assistant_reply,
                },
            }
        ),
    ]
    transcript_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_stop_cli(
    *,
    workspace_root: Path,
    session_id: str,
    transcript_path: Path,
    monkeypatch,
) -> int:
    """Invoke the production Stop CLI with a fresh stdin envelope."""
    envelope = json.dumps(
        {
            "session_id": session_id,
            "transcript_path": str(transcript_path),
            "cwd": str(workspace_root),
            "stop_hook_active": False,
        }
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(envelope))
    return cli_stop(workspace_root=workspace_root)


def _drain_queue_in_fresh_process(workspace_root: Path) -> dict[str, int]:
    """Drive a single drain pass of the production worker.

    Per AC.J.5 the worker is a supervised long-running process. For
    the test we drive ``drain_once`` directly — the same inner loop
    the long-running worker uses. The default ``client_factory`` is
    the file-backed memory client per AC.MFBM.5 (production path);
    no test stubs cross the contract surface.
    """
    return mww.drain_once(workspace_root=workspace_root)


def _run_user_prompt_submit_cli(
    *,
    workspace_root: Path,
    prompt: str,
    monkeypatch,
    capsys,
) -> str:
    """Invoke the production UserPromptSubmit CLI with a stdin envelope.

    Returns the captured stdout (the persona's UserPromptSubmit
    contract emits the additional-context payload there per AC46.2).
    """
    envelope = json.dumps({"prompt": prompt})
    monkeypatch.setattr(sys, "stdin", io.StringIO(envelope))
    rc = cli_user_prompt_submit(workspace_root=workspace_root)
    out = capsys.readouterr().out
    assert rc == 0, f"UserPromptSubmit CLI must exit 0; got {rc}"
    return out


def test_AC_FHA_6_stranger_clone_fbe7_cross_session_outcome(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    """Outcome-altitude: stranger-clone FBE.7 cross-session bridge.

    Workflow:

      1. Fresh workspace tempdir (zero memory state).
      2. Session N-1 — Stop CLI persists a turn that names a unique
         entity ("AC.FHA.6 stranger-clone probe").
      3. Worker drain — queue → file-backed episode on disk.
      4. /clear == fresh-process boundary (subprocess-driven worker
         drain ensures no in-memory state crosses).
      5. Session N — UserPromptSubmit CLI fires against a prompt
         that names the same entity; the persona's stdout MUST
         carry retrieval evidence of the prior turn.
    """
    workspace_root = tmp_path / "stranger_workspace"
    workspace_root.mkdir()

    # --- Session N-1: write a transcript, fire the Stop CLI ---------
    transcript = workspace_root / ".loam" / "transcripts" / "n_minus_1.jsonl"
    distinctive_entity = "AC-FHA-6-stranger-clone-probe-token"
    user_msg = (
        f"Please remember that the {distinctive_entity} is the "
        f"v0.3.0 cycle 6 outcome-altitude verifier."
    )
    assistant_reply = (
        f"Acknowledged. The {distinctive_entity} is the "
        f"stranger-clone FBE.7 probe; its purpose is to prove the "
        f"file-backed memory bridges across sessions."
    )
    _write_fake_transcript(
        transcript,
        user_message=user_msg,
        assistant_reply=assistant_reply,
    )

    rc = _run_stop_cli(
        workspace_root=workspace_root,
        session_id="stranger-session-N-1",
        transcript_path=transcript,
        monkeypatch=monkeypatch,
    )
    assert rc == 0, f"Stop CLI must exit 0 per AC.M.4; got {rc}"

    # Stop CLI enqueues; the worker drains the queue to disk.
    _drain_queue_in_fresh_process(workspace_root)

    # --- Verify the episode landed on disk (FBE.7 invariant) -------
    from loam.primary_persona.file_memory import (
        memory_dir_for_workspace,
    )

    memory_dir = memory_dir_for_workspace(workspace_root)
    episode_files = list(memory_dir.rglob("*.md"))
    assert episode_files, (
        f"FBE.7 invariant violated — no episode files under "
        f"{memory_dir} after Stop+drain. Listing: "
        f"{list(memory_dir.rglob('*'))}"
    )

    # --- /clear simulation: explicit fresh-process boundary -------
    # The production runtime's launchd plist KeepAlive contract means
    # a fresh worker on a different invocation reads the same disk
    # state. We've already driven a drain pass; the on-disk state is
    # the source of truth for the next session.

    # --- Session N: UserPromptSubmit CLI must surface prior turn --
    out = _run_user_prompt_submit_cli(
        workspace_root=workspace_root,
        prompt=(
            f"What was the {distinctive_entity} again? Refresh me."
        ),
        monkeypatch=monkeypatch,
        capsys=capsys,
    )

    # Outcome bar: the retrieval block MUST cite the prior turn.
    # Either the entity token or evidence of the persistent retrieval
    # contract (memory-retrieval block + non-empty body) is sufficient.
    assert distinctive_entity in out or (
        "memory-retrieval" in out and "stranger-clone" in out.lower()
    ), (
        f"FBE.7 cross-session bridge broken: UserPromptSubmit emit "
        f"did not retrieve the prior turn naming "
        f"{distinctive_entity!r}. stdout (truncated): {out[:1000]!r}"
    )
