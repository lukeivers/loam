# AC.FRMSG — first-run fresh-start message accuracy.
#
# The fresh-start first-run message once told a fresh user the install
# "pulls graphiti-core, neo4j, and kuzu." That dependency set RETIRED at
# v0.1.0 (AC.MFBM.7 — file-based memory is the default substrate). The
# message lied about what installs. This test pins the corrected reality.
#
# AC.FRMSG.1 — no graphiti/neo4j/kuzu reference in the fresh-start message.
# AC.FRMSG.2 — the message states current file-based-memory install reality.
# AC.FRMSG.S — outcome-altitude: the production message-builder
#              _msg_fresh_start(log, helper_version), called with no
#              pre-arranged state, returns accurate text.
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import first_run_dispatch  # noqa: E402


RETIRED_DEP_NAMES = ("graphiti", "neo4j", "kuzu")


def _fresh_message() -> str:
    """Call the production message-builder with no pre-arranged state.

    Outcome-altitude: no fixture-seeded string; the real production
    function a fresh user's first run invokes is called directly.
    """
    return first_run_dispatch._msg_fresh_start(
        Path("/tmp/first-run.log"), helper_version="1"
    )


@pytest.mark.parametrize("retired", RETIRED_DEP_NAMES)
def test_AC_FRMSG_1_no_retired_dep_reference(retired: str) -> None:
    """AC.FRMSG.1 — the retired-dependency claim is gone."""
    msg = _fresh_message().lower()
    assert retired not in msg, (
        f"fresh-start first-run message still references retired "
        f"dependency {retired!r}; it retired at v0.1.0 (AC.MFBM.7)"
    )


def test_AC_FRMSG_2_states_file_based_memory_reality() -> None:
    """AC.FRMSG.2 — the message states current install reality."""
    msg = _fresh_message().lower()
    assert "file-based" in msg, (
        "fresh-start message must name that memory is file-based "
        "(the v0.1.0 default substrate)"
    )


def test_AC_FRMSG_S_production_call_is_accurate() -> None:
    """AC.FRMSG.S (outcome-altitude) — the real string a fresh user sees
    is accurate: no retired-dep name AND names file-based memory."""
    msg = _fresh_message()
    lowered = msg.lower()
    for retired in RETIRED_DEP_NAMES:
        assert retired not in lowered, (
            f"production _msg_fresh_start still emits retired dep {retired!r}"
        )
    assert "file-based" in lowered, (
        "production _msg_fresh_start must name file-based memory"
    )
