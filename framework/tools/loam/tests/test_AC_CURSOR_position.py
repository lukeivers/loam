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

"""AC.CURSOR.* — the persisted position cursor.

  - AC.CURSOR.1 — a cursor names {flow, step, branch_state, updated_at}
    and resolves to a step that EXISTS in the flow; a cursor pointing
    at a non-existent step resolves UNRESOLVED.
  - AC.CURSOR.2 — advancing updates the cursor; after an advance the
    cursor names the new step (not the prior) and updated_at advanced.
  - AC.CURSOR.3 — a STALE cursor (its step vanished from a mutated
    flow) resolves UNRESOLVED, never a false position.
  - AC.CURSOR.4 — the methodology-flow cursor path is tracked
    (committable); the user-state cursor path is under .loam/.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.flows.cursor import (
    Cursor,
    advance_cursor,
    methodology_cursor_path,
    read_cursor,
    resolve_cursor,
    user_state_cursor_path,
    write_cursor,
)
from loam_cli.flows.format import parse_flow_definition

REPO_ROOT = Path(__file__).resolve().parents[4]

_FLOW_TEXT = (
    "---\n"
    "flow: f\n"
    "entry: a\n"
    "steps:\n"
    "  - id: a\n    name: A\n    transitions: [b]\n"
    "  - id: b\n    name: B\n    transitions: [c]\n"
    "  - id: c\n    name: C\n    transitions: []\n"
    "---\n"
    "# f\nnarrative present, with a branch-free 3-step walk.\n"
)


@pytest.fixture
def flow():
    return parse_flow_definition(_FLOW_TEXT)


def test_AC_CURSOR_1_names_definite_position_and_resolves(
    tmp_path: Path, flow
) -> None:
    """AC.CURSOR.1 — a written cursor names a definite position and
    resolves to a step that exists in the flow."""
    path = tmp_path / "f.cursor.yaml"
    written = write_cursor(
        path, Cursor(flow="f", step="b", branch_state="mid")
    )
    # The on-disk record names all four fields.
    assert written.flow == "f"
    assert written.step == "b"
    assert written.branch_state == "mid"
    assert written.updated_at  # stamped.

    reread = read_cursor(path)
    assert reread is not None
    res = resolve_cursor(reread, flow)
    assert res.resolved
    assert res.step == "b"
    assert res.step_name == "B"


def test_AC_CURSOR_1_nonexistent_step_resolves_unresolved(flow) -> None:
    """AC.CURSOR.1 — a cursor pointing at a step not in the flow's node
    graph is treated as UNRESOLVED."""
    res = resolve_cursor(Cursor(flow="f", step="zzz"), flow)
    assert not res.resolved
    assert "zzz" in res.reason


def test_AC_CURSOR_2_advance_updates_step_and_timestamp(
    tmp_path: Path, flow
) -> None:
    """AC.CURSOR.2 — advancing moves the cursor to the transition
    target; the prior step is no longer current and updated_at advanced."""
    path = tmp_path / "f.cursor.yaml"
    first = write_cursor(
        path,
        Cursor(
            flow="f",
            step="a",
            branch_state="start",
            updated_at="2020-01-01T00:00:00Z",
        ),
    )
    advanced = advance_cursor(path, flow, "b")
    assert advanced.step == "b"  # new step.
    assert advanced.step != first.step  # prior step no longer current.
    # updated_at advanced past the seeded old timestamp.
    assert advanced.updated_at > first.updated_at
    # The on-disk record reflects the advance.
    assert read_cursor(path).step == "b"


def test_AC_CURSOR_2_advance_to_undeclared_transition_refused(
    tmp_path: Path, flow
) -> None:
    """AC.CURSOR.2 — an advance to a step that is not a declared
    transition of the current step is refused (no inferred jumps)."""
    path = tmp_path / "f.cursor.yaml"
    write_cursor(path, Cursor(flow="f", step="a"))
    with pytest.raises(ValueError):
        advance_cursor(path, flow, "c")  # a->c is not declared.


def test_AC_CURSOR_3_stale_cursor_resolves_unresolved_not_false(
    tmp_path: Path,
) -> None:
    """AC.CURSOR.3 — mutate the flow so the cursor's step vanishes; the
    cursor now resolves UNRESOLVED (triggers pause), NEVER a
    wrong-but-confident position."""
    path = tmp_path / "f.cursor.yaml"
    write_cursor(path, Cursor(flow="f", step="b", branch_state="mid"))

    # The flow changes out from under the cursor: step 'b' is removed
    # (the remaining flow is still a real multi-step flow — a >2-step
    # walk — so the staleness is the only difference, not a not-a-flow
    # rejection).
    mutated_text = (
        "---\n"
        "flow: f\n"
        "entry: a\n"
        "steps:\n"
        "  - id: a\n    name: A\n    transitions: [c]\n"
        "  - id: c\n    name: C\n    transitions: [d]\n"
        "  - id: d\n    name: D\n    transitions: []\n"
        "---\n"
        "# f\nthe flow was edited; step b no longer exists.\n"
    )
    mutated = parse_flow_definition(mutated_text)

    res = resolve_cursor(read_cursor(path), mutated)
    assert not res.resolved
    assert res.step == "b"  # it reports WHAT the cursor claimed,
    assert res.step_name == ""  # but does NOT resolve a false step name.
    assert "no longer exists" in res.reason or "stale" in res.reason


def test_AC_CURSOR_4_methodology_cursor_path_is_tracked(
    tmp_path: Path,
) -> None:
    """AC.CURSOR.4 — the methodology-flow cursor path is NOT gitignored;
    the user-state flow-instance cursor path IS. Checked against the
    REAL repo's .gitignore via git check-ignore (ground truth, not an
    assertion about an assumed rule)."""
    meth = methodology_cursor_path(REPO_ROOT, "loam-vnext-build")
    user = user_state_cursor_path(REPO_ROOT, "some-user-flow")

    # The methodology cursor lives under docs/flows/ (tracked).
    assert "docs/flows" in str(meth)
    # The user-state cursor lives under .loam/ (gitignored user-state).
    assert ".loam/flows" in str(user)

    def _ignored(p: Path) -> bool:
        # git check-ignore exits 0 when the path IS ignored, 1 when not.
        rc = subprocess.run(
            ["git", "check-ignore", "-q", str(p.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
        ).returncode
        return rc == 0

    assert not _ignored(meth), (
        "methodology-flow cursor MUST be committable (guards the "
        "build-cursor.md silent-drop near-miss)"
    )
    assert _ignored(user), (
        "user-state flow-instance cursor MUST be gitignored user-state"
    )
