"""Test helper — Stub PM matching the v0.1.7 PMRuntime structural surface.

Used by AC.COMPINT.{4,5,6,8,10,11} tests. Mirrors:

- ``enqueue_decision(text, *, provenance) -> int``
- ``surface_next_questions_batch(n=1) -> tuple[SurfacedQuestion, ...]``
- ``record_response(audit_path, response_text) -> RecordedResponse``

Per AC.COMPINT.4 — consumer is read-only on the PM. Tests don't need
the real PMRuntime; structural protocol matching is enough.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StubSurfacedQuestion:
    text: str
    provenance: str | None
    queue_position: int
    surfaced_at: str
    audit_path: Path


@dataclass
class StubRecordedResponse:
    response_text: str
    surfaced_audit_path: Path
    surfaced_question_text: str
    responded_at: str
    audit_path: Path


@dataclass
class StubPM:
    """In-memory PM that records every call.

    The audit-paths are synthetic Path strings rather than real
    filesystem entries — interview.py only round-trips them, never
    reads the targets back.
    """

    enqueued: list[tuple[str, str | None]] = field(default_factory=list)
    surfaced_calls: list[int] = field(default_factory=list)
    recorded: list[tuple[Path, str]] = field(default_factory=list)
    _queue: list[tuple[str, str | None]] = field(default_factory=list)
    _surface_count: int = 0
    _record_count: int = 0
    audit_root: Path | None = None

    def enqueue_decision(
        self,
        question_text: str,
        *,
        provenance: str | None = None,
    ) -> int:
        self.enqueued.append((question_text, provenance))
        self._queue.append((question_text, provenance))
        return len(self._queue)

    def surface_next_questions_batch(
        self, n: int | None = None
    ) -> tuple[StubSurfacedQuestion, ...]:
        # Strict n=1 enforcement — the consumer always passes 1.
        self.surfaced_calls.append(n if n is not None else -1)
        if not self._queue:
            return ()
        head_text, prov = self._queue.pop(0)
        self._surface_count += 1
        ap = (
            (self.audit_root or Path("/tmp/audit"))
            / f"surface-{self._surface_count:04d}.yaml"
        )
        sq = StubSurfacedQuestion(
            text=head_text,
            provenance=prov,
            queue_position=1,
            surfaced_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
            audit_path=ap,
        )
        return (sq,)

    def record_response(
        self,
        surfaced_audit_path: Any,
        response_text: str,
    ) -> StubRecordedResponse:
        self._record_count += 1
        ap = Path(surfaced_audit_path) if surfaced_audit_path else Path("/tmp/none.yaml")
        record_path = (
            (self.audit_root or Path("/tmp/audit"))
            / f"record-{self._record_count:04d}.yaml"
        )
        self.recorded.append((ap, response_text))
        return StubRecordedResponse(
            response_text=response_text,
            surfaced_audit_path=ap,
            surfaced_question_text="",
            responded_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
            audit_path=record_path,
        )
