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
    from loam.self_correction import observability as obs

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
        / "loam"
        / "self_correction"
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
