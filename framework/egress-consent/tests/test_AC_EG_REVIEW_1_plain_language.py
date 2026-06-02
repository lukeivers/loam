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

"""AC.EG-REVIEW.1 — plain-language review surface.

The default review view is plain-English (no JSON-reading required) and carries
ZERO internal vocabulary — verified by the SAME probe the recovery surface uses
(``find_internal_vocabulary``, Lens 1).
"""

from __future__ import annotations

import pytest

from loam.self_correction.recovery_surface import find_internal_vocabulary

from loam.egress_consent import (
    EgressBundle,
    EgressItem,
    ItemDecision,
    ItemKind,
)
from loam.egress_consent.review import ReviewSurfaceLeak, render_review


def _bundle(items):
    return EgressBundle.new(
        purpose="bug-report",
        destination_name="the loam team",
        destination_endpoint="loam-feedback-intake",
        items=items,
    )


def test_default_view_carries_zero_internal_vocabulary() -> None:
    b = _bundle(
        (
            EgressItem.new(
                kind=ItemKind.freeform_text,
                plain_summary="A note describing what went wrong",
                exact_bytes=b"it broke when I clicked save",
                decision=ItemDecision.approved,
            ),
            EgressItem.new(
                kind=ItemKind.system_fact,
                plain_summary="Which version of loam you are on",
                exact_bytes=b"1.0.1",
                decision=ItemDecision.approved,
            ),
            EgressItem.new(
                kind=ItemKind.file,
                plain_summary="The file you were working on",
                exact_bytes=b"data",
                decision=ItemDecision.declined,
            ),
        )
    )
    text = render_review(b)
    hits = find_internal_vocabulary(text)
    assert hits == (), f"review surface leaked internal vocabulary: {hits}"


def test_view_is_human_readable_not_json() -> None:
    b = _bundle(
        (
            EgressItem.new(
                kind=ItemKind.freeform_text,
                plain_summary="A note describing what went wrong",
                exact_bytes=b"x",
                decision=ItemDecision.approved,
            ),
        )
    )
    text = render_review(b)
    assert "loam would send" in text
    assert "Nothing is sent yet" in text
    assert "don't send anything" in text
    # No raw JSON structure leaks into the default view.
    assert "{" not in text and "}" not in text


def test_render_raises_on_an_internal_vocab_leak() -> None:
    """A careless caller passing an internal id as a summary is caught."""
    b = _bundle(
        (
            EgressItem.new(
                kind=ItemKind.file,
                # An AC-id shaped summary — the probe must catch it.
                plain_summary="see AC.EG-CORE.3 in src/loam/foo.py",
                exact_bytes=b"x",
                decision=ItemDecision.approved,
            ),
        )
    )
    with pytest.raises(ReviewSurfaceLeak):
        render_review(b)
