"""CR22 — OTel spans routed via trace.get_tracer only, no TracerProvider."""

from __future__ import annotations

from pathlib import Path


def test_CR22_no_tracer_provider_construction() -> None:
    src_root = Path(__file__).resolve().parent.parent / "src"
    for py in src_root.rglob("*.py"):
        text = py.read_text()
        # No TracerProvider construction anywhere in this component.
        assert "TracerProvider(" not in text, (
            f"{py} constructs a TracerProvider — A1 correction "
            "forbids this. Use trace.get_tracer(...) only."
        )
        assert "set_tracer_provider" not in text, (
            f"{py} calls set_tracer_provider — forbidden."
        )


def test_CR22_tracer_name_is_pos_self_correction() -> None:
    from self_correction import observability as obs

    # The module-level tracer name must be "loam.self_correction" —
    # parallel to "loam.cost_governance" on cost-governance.
    # We assert by reading the source; tracer objects do not expose
    # their name publicly.
    src = (
        Path(obs.__file__).read_text()
    )
    assert 'trace.get_tracer("loam.self_correction"' in src


def test_CR22_span_names_use_pos_correction_prefix() -> None:
    src = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "observability.py"
    ).read_text()
    # Every `start_as_current_span` call names a span with the
    # `loam.correction.` prefix — consistent with `loam.cost.` spans
    # emitted by cost-governance (even though its tracer is
    # `loam.cost_governance`).
    import re
    names = re.findall(r'start_as_current_span\("([^"]+)"\)', src)
    assert names, "expected at least one span emission"
    for n in names:
        assert n.startswith("loam.correction."), (
            f"span {n!r} does not use the loam.correction.* namespace"
        )
