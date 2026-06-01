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

"""AC.SR-RESET.1 + AC.SR-RESET.2 — the FBM hard-reset is backup-first and
fail-closed, and after a reset the prior store is restorable byte-for-byte.

AC.SR-RESET.1 — a hard-reset takes a recoverable snapshot BEFORE any
destructive step, and a reset attempt with no recoverable snapshot path is
REFUSED (fail-closed — ProtectionFloorRefusal).

AC.SR-RESET.2 — after a hard-reset the pre-reset .loam/ store is restorable
from the snapshot byte-for-byte (the irreplaceable store is never lost).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.reversibility_primitive import ReversibilityStore
from loam.self_correction import (
    ResetNotConfirmed,
    SafeFbmReset,
    is_reset_confirmed,
    reset_would_fail_closed,
)


def _seed_loam(workspace: Path) -> dict[str, bytes]:
    """Create a realistic .loam/ store and return its byte contents for a
    byte-for-byte comparison later."""
    loam = workspace / ".loam"
    (loam / "memory").mkdir(parents=True)
    files = {
        ".loam/objectives.yaml": b"goal: write the novel\n",
        ".loam/memory/notes.md": b"# irreplaceable notes\nchapter 1 idea\n",
        ".loam/state.json": b'{"cursor": 42}',
    }
    for rel, content in files.items():
        (workspace / rel).write_bytes(content)
    return files


def _reset_store(workspace: Path) -> ReversibilityStore:
    # The reversibility store + snapshots live OUTSIDE .loam/ so they survive
    # the reset.
    return ReversibilityStore(workspace / ".loam-recovery" / "rev.sqlite")


# ---- AC.SR-RESET.1 — backup-first ------------------------------------


def test_AC_SR_RESET_1_snapshot_taken_before_destructive_step(
    tmp_path: Path,
) -> None:
    """The snapshot exists (backup-first) and the destructive step ran —
    proving the snapshot preceded the removal."""
    ws = tmp_path / "ws"
    ws.mkdir()
    _seed_loam(ws)

    store = _reset_store(ws)
    try:
        resetter = SafeFbmReset(
            store=store, snapshot_root=ws / ".loam-recovery" / "snap"
        )
        result = resetter.reset(ws, confirmed="yes, start fresh")
    finally:
        store.close()

    # Backup exists.
    assert result.snapshot_path.exists()
    assert (result.snapshot_path / "objectives.yaml").exists()
    # Destructive step ran (live store gone).
    assert not (ws / ".loam").exists()


# ---- AC.SR-RESET.1 — fail-closed -------------------------------------


def test_AC_SR_RESET_1_no_snapshot_is_refused(tmp_path: Path) -> None:
    """With no recoverable snapshot (no compensation binding), the gate
    REFUSES — the fail-closed posture, asserted WITHOUT a destructive step."""
    ws = tmp_path / "ws"
    ws.mkdir()
    _seed_loam(ws)
    store = _reset_store(ws)
    try:
        # No binding registered → guard would refuse.
        assert reset_would_fail_closed(store, ws / ".loam-recovery" / "snap") is True
    finally:
        store.close()
    # And the store is untouched (no destructive step happened).
    assert (ws / ".loam").exists()


def test_AC_SR_RESET_1_unconfirmed_reset_refused_before_destruction(
    tmp_path: Path,
) -> None:
    """FORK F-3 ruling: a reset without the explicit plain-English confirm is
    refused BEFORE any destructive step — the store survives intact."""
    ws = tmp_path / "ws"
    ws.mkdir()
    seeded = _seed_loam(ws)
    store = _reset_store(ws)
    try:
        resetter = SafeFbmReset(
            store=store, snapshot_root=ws / ".loam-recovery" / "snap"
        )
        with pytest.raises(ResetNotConfirmed):
            resetter.reset(ws, confirmed=None)
        with pytest.raises(ResetNotConfirmed):
            resetter.reset(ws, confirmed="maybe")
    finally:
        store.close()
    # Store untouched — nothing destroyed without the confirm.
    assert (ws / ".loam").exists()
    for rel, content in seeded.items():
        assert (ws / rel).read_bytes() == content


def test_AC_SR_RESET_1_confirm_phrase_recognition() -> None:
    assert is_reset_confirmed("yes, start fresh") is True
    assert is_reset_confirmed("YES, START FRESH") is True
    assert is_reset_confirmed("  yes start fresh  ") is True
    assert is_reset_confirmed("no") is False
    assert is_reset_confirmed("") is False
    assert is_reset_confirmed(None) is False


# ---- AC.SR-RESET.2 — restorable byte-for-byte -------------------------


def test_AC_SR_RESET_2_prior_store_restorable_byte_for_byte(
    tmp_path: Path,
) -> None:
    """After a reset, the pre-reset .loam/ is restorable from the snapshot
    byte-for-byte — the irreplaceable store is never lost."""
    ws = tmp_path / "ws"
    ws.mkdir()
    seeded = _seed_loam(ws)

    store = _reset_store(ws)
    try:
        resetter = SafeFbmReset(
            store=store, snapshot_root=ws / ".loam-recovery" / "snap"
        )
        result = resetter.reset(ws, confirmed="yes, start fresh")
        assert not (ws / ".loam").exists()  # reset happened

        # Restore from the snapshot.
        resetter.restore(result.snapshot_path, ws)
    finally:
        store.close()

    # Byte-for-byte: every original file is back with identical bytes.
    assert (ws / ".loam").exists()
    for rel, content in seeded.items():
        restored = ws / rel
        assert restored.exists(), f"{rel} not restored"
        assert restored.read_bytes() == content, f"{rel} bytes differ after restore"
