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

"""AC.SOL-PROBE.* — the liveness probe classifies state from ground truth.

  * AC.SOL-PROBE.1 — built/sealed/merged from the git ref graph, NOT from
    any artefact's prose status line.
  * AC.SOL-PROBE.2 — wired vs dark from live config (hook) AND from a cheap
    REAL probe for backend-class components (the load-bearing F2: a "config
    says wired but it does not actually run" component is DARK, not live).
  * AC.SOL-PROBE.3 — run against the current repo, the probe reports FBM as
    live (the verdict that today required a hand-reconciliation).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam_cli.audit.probe import (
    Liveness,
    classify_backend_liveness,
    classify_build_status,
    classify_hook_wired,
)


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


def test_AC_SOL_PROBE_1_built_sealed_merged_from_refs(scratch_repo: Path) -> None:
    """Build/seal/merge status derives from `merge-base --is-ancestor`,
    NOT from a prose status line. An ancestor SHA → MERGED; a real
    side-branch SHA → SEALED; no sidecar → UNBUILT; a bogus SHA →
    UNKNOWN (fail-safe)."""
    repo = scratch_repo
    # A merged seal: a commit on HEAD's history.
    (repo / "f.txt").write_text("a\n", encoding="utf-8")
    merged_sha = _commit(repo, "merged work")
    assert (
        classify_build_status(repo, seal_sha=merged_sha) is Liveness.MERGED
    )

    # A sealed-not-merged commit: branch off, commit, return to main.
    subprocess.run(
        ["git", "checkout", "-q", "-b", "side"], cwd=repo, check=True
    )
    (repo / "g.txt").write_text("b\n", encoding="utf-8")
    side_sha = _commit(repo, "side work")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    assert classify_build_status(repo, seal_sha=side_sha) is Liveness.SEALED

    # No anchor at all → UNBUILT.
    assert (
        classify_build_status(repo, seal_sidecar=repo / "nope" / "SEAL_COMMIT")
        is Liveness.UNBUILT
    )

    # A bogus (unknown) SHA → UNKNOWN (fail-safe, never a false green).
    assert (
        classify_build_status(repo, seal_sha="deadbeef" * 5)
        is Liveness.UNKNOWN
    )


def test_AC_SOL_PROBE_1_reads_sidecar_sha(scratch_repo: Path) -> None:
    """The probe reads the pinned SHA from a SEAL_COMMIT sidecar; a
    `HEAD`/empty placeholder means not-yet-sealed → UNBUILT."""
    repo = scratch_repo
    (repo / "h.txt").write_text("c\n", encoding="utf-8")
    sha = _commit(repo, "work")
    sidecar = repo / "tests" / "SEAL_COMMIT"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(sha + "\n", encoding="utf-8")
    assert (
        classify_build_status(repo, seal_sidecar=sidecar) is Liveness.MERGED
    )

    sidecar.write_text("HEAD\n", encoding="utf-8")
    assert (
        classify_build_status(repo, seal_sidecar=sidecar) is Liveness.UNBUILT
    )


def test_AC_SOL_PROBE_2_hook_wired_vs_dark_from_live_config() -> None:
    """A hook is WIRED iff live settings.json carries a command matching
    the marker; DARK when settings is empty (the IP-7 class — "hooks
    already wired" assumed true while settings.json was empty)."""
    wired_settings = {
        "hooks": {
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": "/v/python -m loam.primary_persona.cli user-prompt-submit",
                        }
                    ]
                }
            ]
        }
    }
    assert (
        classify_hook_wired(
            wired_settings, marker="primary_persona.cli user-prompt-submit"
        )
        is Liveness.WIRED
    )
    # Empty config → DARK (the IP-7 class).
    assert classify_hook_wired({}, marker="anything") is Liveness.DARK
    # Marker absent → DARK.
    assert (
        classify_hook_wired(wired_settings, marker="some_other_hook")
        is Liveness.DARK
    )


def test_AC_SOL_PROBE_2_hook_wired_in_config_but_script_missing_is_dark() -> None:
    """A hook wired in config but pointing at a missing script degrades
    to DARK (wired in name only)."""
    settings = {
        "hooks": {
            "Stop": [
                {"hooks": [{"type": "command", "command": "/v/python missing_hook.py"}]}
            ]
        }
    }
    assert (
        classify_hook_wired(
            settings, marker="missing_hook.py", script_exists=lambda _c: False
        )
        is Liveness.DARK
    )
    assert (
        classify_hook_wired(
            settings, marker="missing_hook.py", script_exists=lambda _c: True
        )
        is Liveness.WIRED
    )


def test_AC_SOL_PROBE_2_backend_config_wired_but_real_probe_fails_is_dark() -> None:
    """★ The load-bearing F2 (plan §10 item 1): a backend whose CONFIG
    says wired but whose REAL probe FAILS is classified DARK — the
    graphiti case (MCP-wired + async queue present, but the consumer was
    a shim that never ran). Static config alone would mis-classify it
    LIVE; the real probe catches what config cannot."""
    # config says wired, but the real probe (an import/call) FAILS.
    assert (
        classify_backend_liveness(
            config_says_wired=True, real_probe=lambda: False
        )
        is Liveness.DARK
    )
    # config says wired AND the real probe SUCCEEDS → genuinely live.
    assert (
        classify_backend_liveness(
            config_says_wired=True, real_probe=lambda: True
        )
        is Liveness.WIRED
    )
    # an EXCEPTION from the probe (ImportError, connection refused) is a
    # failed probe → DARK, never an indeterminate pass.
    def _boom() -> bool:
        raise ImportError("graphiti_core not importable")

    assert (
        classify_backend_liveness(config_says_wired=True, real_probe=_boom)
        is Liveness.DARK
    )
    # config does not even declare it → DARK.
    assert (
        classify_backend_liveness(
            config_says_wired=False, real_probe=lambda: True
        )
        is Liveness.DARK
    )


def test_AC_SOL_PROBE_3_live_component_reads_live_on_current_repo() -> None:
    """Run against the CURRENT canonical repo, the default probe reports
    FBM as live (the keep-pace hook wired, the seals merged) — the
    roadmap §6 R-1 finding the persona had to derive by hand."""
    from loam_cli.audit.loam_state import default_state_record

    repo_root = Path(__file__).resolve().parents[4]
    record = default_state_record(repo_root)
    fbm_component = record.by_name("fbm-episode-store")
    assert fbm_component is not None
    # The FBM seals are merged into HEAD's history (7dcb95b ancestor).
    assert fbm_component.liveness is Liveness.MERGED
    # The backend real-probe (loam_cli import) classifies the runtime live.
    runtime = record.by_name("loam-cli-runtime")
    assert runtime is not None
    assert runtime.liveness is Liveness.WIRED
