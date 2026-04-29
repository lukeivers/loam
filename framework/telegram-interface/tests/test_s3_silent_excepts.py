"""Amendment #21 — S3 silent-except bundle — telegram-interface surface.

Covers Site 3:
  * ``src/allowlist.py::AccessFile.identities()`` — a malformed
    ``pos_identities`` record was previously skipped silently; the fix
    emits ``loam.telegram.allowlist_record_malformed`` while preserving
    the ``continue`` so the returned dict still contains only the
    well-formed records.

Fixture strategy mirrors the other observability-assertion tests in
this suite — install a ``TracerProvider`` + ``InMemorySpanExporter``
at module scope and check the exporter after each call.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from loam.telegram_interface.allowlist import AccessFile, AuthorityClass


@pytest.fixture(scope="module")
def otel_exporter():
    exporter = InMemorySpanExporter()
    current = trace.get_tracer_provider()
    if hasattr(current, "add_span_processor"):
        # Another test already installed a TracerProvider at module
        # scope — OTel rejects re-registration, so attach an
        # additional SimpleSpanProcessor to the existing provider.
        current.add_span_processor(SimpleSpanProcessor(exporter))
    else:
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    return exporter


def _spans_named(exporter, name):
    return [s for s in exporter.get_finished_spans() if s.name == name]


def test_identities_surfaces_malformed_record(
    tmp_path: Path, otel_exporter
) -> None:
    otel_exporter.clear()
    # One well-formed owner record + one record missing
    # ``authority_class`` + one non-mapping record.
    path = tmp_path / "access.json"
    access = AccessFile(
        path=path,
        data={
            "dmPolicy": "allowlist",
            "allowFrom": ["111111", "222222", "333333"],
            "groups": {},
            "pending": {},
            "pos_identities": {
                "111111": {
                    "user_id": "111111",
                    "display_name": "Luke",
                    "relationship": "owner",
                    "authority_class": AuthorityClass.OWNER,
                    "added_at": "2026-04-22T00:00:00+00:00",
                },
                "222222": {
                    # missing authority_class
                    "user_id": "222222",
                    "display_name": "Spouse",
                    "relationship": "spouse",
                    "added_at": "2026-04-22T01:00:00+00:00",
                },
                "333333": "not-a-mapping",
            },
        },
    )

    identities = access.identities()

    # Existing-behaviour preservation: only the valid record survives.
    assert "111111" in identities
    assert "222222" not in identities
    assert "333333" not in identities

    # Observable surface: one span per malformed record (2 expected).
    spans = _spans_named(otel_exporter, "loam.telegram.allowlist_record_malformed")
    by_uid = {dict(s.attributes).get("telegram.user_id"): s for s in spans}
    assert "222222" in by_uid, (
        f"expected span for 222222; saw uids {list(by_uid)}"
    )
    assert "333333" in by_uid, (
        f"expected span for 333333; saw uids {list(by_uid)}"
    )

    attrs_222 = dict(by_uid["222222"].attributes)
    assert attrs_222["exception.class"] == "KeyError"
    assert attrs_222["telegram.allowlist.malformed_key"] == "authority_class"

    attrs_333 = dict(by_uid["333333"].attributes)
    assert attrs_333["exception.class"] == "TypeError"
