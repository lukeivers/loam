"""AC.SE.1 — workspace-mode bit is queryable.

Per the locked plan-doc
``docs/rebuild/plans/structural-enforcement-a1-substrate.md`` §4
AC.SE.1: a pure-Python helper returns ``"dev-mode" | "normal-use"``
deterministically given the workspace's primary-persona contract
``dev_intent`` field. Sub-100ms p95, callable from inside a Claude
Code hook process (no async runtime, no Claude SDK dependency).
When ``dev_intent`` is unset / unreadable / corrupt, the helper
returns ``"normal-use"`` (fail-closed-to-permissive — DEV-MODE
machinery is opt-in).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from corpus_load_sentinel import workspace_mode  # noqa: E402


def _write_persona_contract(
    workspace_root: Path, *, dev_intent: str
) -> Path:
    """Write a minimal persona contract carrying the dev_intent value."""
    persona_dir = workspace_root / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    contract = persona_dir / "contract.yaml"
    contract.write_text(
        "handle: primary\n"
        f"dev_intent: {dev_intent}\n"
        "is_primary: true\n",
        encoding="utf-8",
    )
    return contract


def test_AC_SE_1_returns_dev_mode_when_dev_intent_yes(
    tmp_path: Path,
) -> None:
    _write_persona_contract(tmp_path, dev_intent="yes")
    assert workspace_mode(tmp_path) == "dev-mode"


def test_AC_SE_1_returns_normal_use_when_dev_intent_no(
    tmp_path: Path,
) -> None:
    _write_persona_contract(tmp_path, dev_intent="no")
    assert workspace_mode(tmp_path) == "normal-use"


def test_AC_SE_1_returns_normal_use_when_dev_intent_absent(
    tmp_path: Path,
) -> None:
    """No persona contract on disk → ``normal-use`` (fail-closed-to-
    permissive)."""
    assert workspace_mode(tmp_path) == "normal-use"


def test_AC_SE_1_returns_normal_use_when_contract_unreadable(
    tmp_path: Path,
) -> None:
    """A contract file with malformed YAML returns ``normal-use``
    rather than raising."""
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        "this is: not\n  valid yaml: [unclosed\n",
        encoding="utf-8",
    )
    assert workspace_mode(tmp_path) == "normal-use"


def test_AC_SE_1_helper_completes_under_100ms_p95(
    tmp_path: Path,
) -> None:
    """Sub-100ms p95 budget per AC.SE.1.

    Run the helper 50 times against a real on-disk contract and
    assert the 95th-percentile wall-clock is under 100ms. The helper
    is pure synchronous YAML parsing over a ~50-byte file; budget
    is generous.
    """
    _write_persona_contract(tmp_path, dev_intent="yes")
    timings = []
    for _ in range(50):
        start = time.perf_counter()
        workspace_mode(tmp_path)
        timings.append(time.perf_counter() - start)
    timings.sort()
    p95 = timings[int(0.95 * len(timings))]
    assert p95 < 0.1, f"AC.SE.1 p95 budget exceeded: {p95 * 1000:.1f}ms"


def test_AC_SE_1_helper_returns_one_of_two_strings_only(
    tmp_path: Path,
) -> None:
    """Mode bit is structurally a two-value enum on the wire — never
    leaks loam-mode's internal ``dev``/``user`` terminology."""
    _write_persona_contract(tmp_path, dev_intent="yes")
    result = workspace_mode(tmp_path)
    assert result in ("dev-mode", "normal-use")
    _write_persona_contract(tmp_path, dev_intent="no")
    result = workspace_mode(tmp_path)
    assert result in ("dev-mode", "normal-use")
