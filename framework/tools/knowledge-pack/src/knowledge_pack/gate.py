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

"""Curation gate + publish-eligibility (AC.CLP-PUSH-RENDER.3, AC.CLP-PUSH.5).

RENDER.3 — the render emits a curation-gate record (a
``gate-record.json`` in the pack root) carrying the gate verdict
(pass/fail), the reviewer, the timestamp, and the content-hash the gate
ruled on. The pack is publish-eligible ONLY when a gate record exists,
its verdict is ``pass``, AND its ``content_hash`` matches the pack's
current content-hash (so a gate pass on one pack body cannot launder a
later, re-rendered body).

AC.CLP-PUSH.5 (adversarial leg, LOCAL) — :func:`assert_publish_eligible`
is the publish-path gate the S4c ⛔OWNER publish would consult. Here it is
built + tested LOCALLY: a publish attempt against a pack with no gate
record, a failed gate, or a content-hash mismatch is REFUSED
(:class:`UngatedPublishError`). Nothing leaves the machine without a
recorded gate pass — the egress-consent floor's local test surface.

The gate VERDICT itself is a recorded human/curator decision (the gate
is a record, not an auto-pass): the default rendered gate record is
``"pending"`` — neither pass nor fail — so a freshly-rendered pack is NOT
publish-eligible until a curator records a pass. Auto-passing the gate
would defeat its purpose (the "never ships" failure mode's inverse —
"ships unreviewed").
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

GATE_RECORD_NAME = "gate-record.json"
PACK_MANIFEST_NAME = "pack-manifest.json"

VERDICT_PASS = "pass"
VERDICT_FAIL = "fail"
VERDICT_PENDING = "pending"


class UngatedPublishError(Exception):
    """A publish was attempted against a pack that is not gate-passed
    (no record / pending / failed / content-hash mismatch). AC.CLP-PUSH.5."""


@dataclass
class GateRecord:
    verdict: str
    content_hash: str
    reviewer: Optional[str]
    ts: Optional[str]

    @property
    def is_pass(self) -> bool:
        return self.verdict == VERDICT_PASS


def emit_gate_record(
    pack_root: Path,
    content_hash: str,
    ts: str,
    verdict: str = VERDICT_PENDING,
    reviewer: Optional[str] = None,
) -> Path:
    """Emit the curation-gate record into the pack root (RENDER.3).

    A freshly-rendered pack gets a ``pending`` record by default — the
    curation decision is recorded by a human/curator who re-writes the
    record with ``pass`` + their identity (or by an explicit
    ``--gate-pass --reviewer NAME`` operator override at render time, for
    the rig). ``content_hash`` binds the verdict to the exact pack body.
    """
    if verdict not in (VERDICT_PASS, VERDICT_FAIL, VERDICT_PENDING):
        raise ValueError(f"invalid gate verdict: {verdict!r}")
    record = {
        "verdict": verdict,
        "content_hash": content_hash,
        "reviewer": reviewer,
        "ts": ts,
    }
    path = Path(pack_root) / GATE_RECORD_NAME
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def read_gate_record(pack_root: Path) -> Optional[GateRecord]:
    path = Path(pack_root) / GATE_RECORD_NAME
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return GateRecord(
        verdict=data.get("verdict", VERDICT_PENDING),
        content_hash=data.get("content_hash", ""),
        reviewer=data.get("reviewer"),
        ts=data.get("ts"),
    )


def _pack_content_hash(pack_root: Path) -> Optional[str]:
    mp = Path(pack_root) / PACK_MANIFEST_NAME
    if not mp.is_file():
        return None
    return json.loads(mp.read_text(encoding="utf-8")).get("content_hash")


def is_publish_eligible(pack_root: Path) -> bool:
    """True only when a gate record exists, verdict is ``pass``, and its
    content-hash matches the pack's current content-hash (RENDER.3)."""
    record = read_gate_record(pack_root)
    if record is None or not record.is_pass:
        return False
    current = _pack_content_hash(pack_root)
    return current is not None and current == record.content_hash


def assert_publish_eligible(pack_root: Path) -> None:
    """The publish-path gate (AC.CLP-PUSH.5). Raises
    :class:`UngatedPublishError` with a specific reason when the pack is
    not gate-passed. This is the LOCAL test surface for the ⛔OWNER
    publish refusal — nothing publishes without a recorded gate pass."""
    record = read_gate_record(Path(pack_root))
    if record is None:
        raise UngatedPublishError(
            "no curation-gate record present — pack is not publish-eligible "
            "(a recorded gate pass is required before any publish)"
        )
    if record.verdict == VERDICT_PENDING:
        raise UngatedPublishError(
            "curation-gate verdict is 'pending' — the curator has not "
            "recorded a pass; publish refused"
        )
    if record.verdict == VERDICT_FAIL:
        raise UngatedPublishError(
            "curation-gate verdict is 'fail' — publish refused"
        )
    current = _pack_content_hash(Path(pack_root))
    if current is None:
        raise UngatedPublishError(
            "pack manifest missing — cannot confirm the gated content-hash; "
            "publish refused"
        )
    if current != record.content_hash:
        raise UngatedPublishError(
            "gate record content-hash does not match the pack's current "
            "content-hash — the pack changed after the gate pass; publish "
            "refused (re-gate the new body)"
        )
