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

"""AC46.1 — SessionStart CLI emits structured additionalContext.

Outcome (per umbrella plan §4a + builder plan §2): in a fully-scaffolded
workspace, ``emit_session_start_context(workspace_root)`` (or the
equivalent CLI subcommand path) returns a non-empty additionalContext
string whose serialised form contains:

  - the corpus_paths list with present indicators
  - amendments_in_flight list
  - service_state fields (memory + orchestrator)
  - cost_headroom
  - corpus_gate_state sentinel
  - first-run-completion timestamp + generation marker
  - tracker-context contributor's output (when in-flight objectives
    exist; this test exercises the empty-tracker path which is also
    AC-shape-correct — empty contribution is permitted per AC40.5)
  - starter-pending block when ``contract.is_starter=True``

Total payload fits within the composer's 10,000-char structural cap.

Builder plan §3.1 D-build.4 — production-side memory-client factory
returns None pre-#47; the memory-retrieval contributor is not
registered. The session-level payload is independently AC-correct.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from loam.primary_persona.context_composer import ADDITIONAL_CONTEXT_CAP
from loam.primary_persona.session_start_emitter import (
    cli_session_start,
    emit_session_start_context,
)


def _seed_workspace(root: Path, *, with_starter_persona: bool = True) -> None:
    """Write a fully-scaffolded baseline workspace."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(
        "# test workspace\n\n"
        "## Session-start discipline\n\n"
        "Before acting, read:\n\n"
        "- `docs/odd-methodology.md`\n"
        "- `docs/odd-in-loam.md`\n"
        "- `docs/rebuild/VALUE_PROPOSITION.md`\n"
        "- `docs/rebuild/STATE.md`\n"
        "- `docs/rebuild/FUTURE_IDEAS.md`\n"
        "\n---\n\n"
    )
    (root / "docs").mkdir()
    (root / "docs" / "odd-methodology.md").write_text("odd")
    (root / "docs" / "odd-in-loam.md").write_text("in-pos")
    (root / "docs" / "rebuild").mkdir()
    (root / "docs" / "rebuild" / "VALUE_PROPOSITION.md").write_text("vp")
    (root / "docs" / "rebuild" / "STATE.md").write_text("state")
    (root / "docs" / "rebuild" / "FUTURE_IDEAS.md").write_text("ideas")
    (root / "docs" / "rebuild" / "plans").mkdir()
    (root / "docs" / "rebuild" / "plans" / "amendment-x.md").write_text("#x")
    # D-migration D.2 (amendment #63): workspace-state under
    # <ws>/workspace/.pos/ post-D.2.
    pos = root / "workspace" / ".pos"
    pos.mkdir(parents=True)
    (pos / "first-run.state").write_text(
        json.dumps({"completed_at": "2026-04-25T00:00:00Z"})
    )
    (pos / "cost-headroom.json").write_text(
        json.dumps({"mtd_spend_usd": "12.34", "ceiling_usd": "500.00"})
    )
    if with_starter_persona:
        personas = root / "workspace" / "personas"
        personas.mkdir()
        starter = personas / "primary"
        starter.mkdir()
        (starter / "contract.yaml").write_text(
            "handle: primary\n"
            "given_name: Iris\n"
            "contract_version: 1.0.0\n"
            "responsibilities:\n"
            "  single_point_of_contact: Coordinator.\n"
            "  context_holder: Holds context.\n"
            "  escalation_judge: Decides surfacing.\n"
            "authority_boundary:\n"
            "  tier_a: defer\n"
            "  tier_b: defer\n"
            "  tier_c: execute\n"
            "  tier_d: execute\n"
            "escalation_taxonomy:\n"
            "  categories: [x]\n"
            "severity_vocabulary:\n"
            "  labels: [a, b]\n"
            "is_primary: true\n"
            "is_starter: true\n"
        )
        (starter / "prompt.md").write_text("# persona prompt\n")


def test_AC46_1_emit_returns_non_empty_string(tmp_path: Path) -> None:
    """Baseline-correct workspace produces a non-empty payload."""
    _seed_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert text, "emit returned empty string on a well-scaffolded workspace"


def test_AC46_1_payload_carries_corpus_paths(tmp_path: Path) -> None:
    """Payload's serialised form names baseline corpus paths."""
    _seed_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert "CLAUDE.md" in text
    assert "docs/odd-methodology.md" in text
    assert "docs/odd-in-loam.md" in text
    assert "corpus_gate_state" in text


def test_AC46_1_payload_carries_amendments_in_flight(tmp_path: Path) -> None:
    """Payload names amendment-*.md in-flight planning files."""
    _seed_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert "amendments_in_flight" in text
    assert "amendment-x.md" in text


def test_AC46_1_payload_carries_service_state(tmp_path: Path) -> None:
    """Payload names memory + orchestrator service state."""
    _seed_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert "service_state" in text
    assert "memory" in text
    assert "orchestrator" in text


def test_AC46_1_payload_carries_cost_headroom(tmp_path: Path) -> None:
    """Payload names cost_headroom MTD spend + ceiling."""
    _seed_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert "cost_headroom" in text
    assert "12.34" in text
    assert "500.00" in text


def test_AC46_1_payload_carries_first_run_completion(tmp_path: Path) -> None:
    """Payload names the first-run completion timestamp + generation
    marker."""
    _seed_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert "first_run_completion" in text
    assert "2026-04-25" in text
    # Generation marker comes from compose_session_fields' default.
    assert "session-start" in text


def test_AC46_1_payload_carries_starter_pending_when_starter(tmp_path: Path) -> None:
    """Workspace with a starter-flagged contract carries the starter-
    pending contributor output in the SessionStart payload."""
    _seed_workspace(tmp_path, with_starter_persona=True)
    text = emit_session_start_context(tmp_path)
    assert "starter-pending" in text or "[primary-persona/onboarding" in text


def test_AC46_1_payload_within_10k_cap(tmp_path: Path) -> None:
    """Total payload fits within the composer's 10,000-char cap."""
    _seed_workspace(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert len(text) <= ADDITIONAL_CONTEXT_CAP


def test_AC46_1_cli_session_start_writes_payload_to_stdout(
    tmp_path: Path, capsys
) -> None:
    """The CLI helper writes the rendered payload to stdout and exits 0."""
    _seed_workspace(tmp_path)
    rc = cli_session_start(workspace_root=tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    assert out, "cli_session_start produced no stdout"
    assert "CLAUDE.md" in out
