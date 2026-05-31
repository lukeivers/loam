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

"""AC.SOL-RECORD.* — the record is derived from ground truth, never prose.

  * AC.SOL-RECORD.1 — derived-not-authored: editing a rendered record by
    hand has no effect on the next generation (it regenerates from ground
    truth). Drift is impossible by construction.
  * AC.SOL-RECORD.2 — reflects a real change: when ground truth changes (a
    seal merges, a hook is added to settings.json), the regenerated record
    reflects the new state with no manual edit.
  * AC.SOL-RECORD.3 — terse + always-loadable: the rendered record is a
    bounded summary, not an unwieldy dump.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam_cli.audit.probe import Liveness
from loam_cli.audit.record import (
    ComponentProbeSpec,
    HookProbeSpec,
    generate_record,
    render_record,
)


def _settings(*markers: str) -> dict:
    return {
        "hooks": {
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {"type": "command", "command": m} for m in markers
                    ]
                }
            ]
        }
    }


def _commit(repo: Path, msg: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=repo, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_AC_SOL_RECORD_1_editing_rendered_record_has_no_effect(
    scratch_repo: Path, tmp_path: Path
) -> None:
    """The record GENERATES from ground truth on every read. There is no
    persisted prose source it is copied from — so hand-editing a rendered
    copy cannot drift the next generation (it regenerates identically from
    the same ground truth)."""
    repo = scratch_repo
    sidecar = repo / "tests" / "SEAL_COMMIT"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    (repo / "seed.txt").write_text("x\n", encoding="utf-8")
    sha = _commit(repo, "seed")
    sidecar.write_text(sha + "\n", encoding="utf-8")
    _commit(repo, "pin sidecar")

    specs = (
        ComponentProbeSpec(
            name="widget", seal_sidecar_relpath="tests/SEAL_COMMIT"
        ),
    )
    first = generate_record(repo, component_specs=specs)

    # "Hand-edit" a rendered copy to claim the OPPOSITE (a lie on disk).
    lied = tmp_path / "state-of-loam.md"
    lied.write_text(
        render_record(first).replace("merged", "dark"), encoding="utf-8"
    )
    assert "dark" in lied.read_text(encoding="utf-8")

    # Regenerate: the hand-edit on the rendered copy has NO effect — the
    # next generation derives from ground truth, unchanged.
    second = generate_record(repo, component_specs=specs)
    assert second.by_name("widget").liveness is Liveness.MERGED
    assert second.by_name("widget").liveness == first.by_name("widget").liveness


def test_AC_SOL_RECORD_2_reflects_a_real_ground_truth_change(
    scratch_repo: Path,
) -> None:
    """When ground truth changes (a hook added to settings.json), the
    regenerated record reflects the new state with no manual edit."""
    repo = scratch_repo
    hook_specs = (HookProbeSpec(name="kp-hook", marker="kp_marker"),)

    # Before: no hook wired → DARK.
    from loam_cli.audit.record import generate_record as gen

    before = gen(repo, hook_specs=hook_specs)
    assert before.by_name("kp-hook").liveness is Liveness.DARK

    # Ground truth changes: the hook is now wired in live config.
    settings_path = repo / "settings.json"
    import json

    settings_path.write_text(
        json.dumps(_settings("/v/python -m kp_marker run")), encoding="utf-8"
    )

    after = gen(repo, hook_specs=hook_specs, settings_path=settings_path)
    assert after.by_name("kp-hook").liveness is Liveness.WIRED


def test_AC_SOL_RECORD_3_render_is_terse_and_bounded(
    scratch_repo: Path,
) -> None:
    """The rendered record is a bounded, always-loadable summary — one
    line per component, grouped by kind, with a HEAD anchor header."""
    repo = scratch_repo
    hook_specs = (HookProbeSpec(name="kp-hook", marker="kp_marker"),)
    rendered = render_record(generate_record(repo, hook_specs=hook_specs))
    # Bounded: a single-hook record renders in a handful of lines.
    assert rendered.count("\n") < 12
    assert "STATE-OF-LOAM" in rendered
    # One line per component (the hook row is present).
    assert "kp-hook" in rendered
