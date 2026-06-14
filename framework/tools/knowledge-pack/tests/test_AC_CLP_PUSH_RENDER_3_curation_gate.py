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

"""AC.CLP-PUSH-RENDER.3 + AC.CLP-PUSH.5 — curation gate + ungated-publish
refusal rig (LOCAL).

RENDER.3 — the render emits a curation-gate record; the pack is
publish-eligible ONLY on a recorded gate PASS bound to the pack's
content-hash.

AC.CLP-PUSH.5 (adversarial, LOCAL) — a publish attempt against a pack
with no gate record / a pending verdict / a failed verdict / a
content-hash mismatch is REFUSED. Nothing leaves the machine without a
recorded gate pass.
"""

from __future__ import annotations

import pytest

from knowledge_pack.render import render_pack
from knowledge_pack.gate import (
    emit_gate_record,
    read_gate_record,
    is_publish_eligible,
    assert_publish_eligible,
    UngatedPublishError,
    VERDICT_PASS,
    VERDICT_FAIL,
    VERDICT_PENDING,
)


def _render(fixture_corpus, name="pack"):
    corpus = fixture_corpus["corpus_root"]
    pack = fixture_corpus["repo_root"] / name
    result = render_pack(corpus, pack, "2026-06-14T12:00:00Z")
    return pack, result


def test_AC_CLP_PUSH_RENDER_3_default_pending_not_eligible(fixture_corpus):
    """A freshly rendered pack with a default PENDING gate record is NOT
    publish-eligible."""
    pack, result = _render(fixture_corpus)
    emit_gate_record(pack, result.content_hash, "2026-06-14T12:00:00Z")
    rec = read_gate_record(pack)
    assert rec is not None and rec.verdict == VERDICT_PENDING
    assert not is_publish_eligible(pack)


def test_AC_CLP_PUSH_RENDER_3_pass_makes_eligible(fixture_corpus):
    """A recorded PASS bound to the current content-hash makes the pack
    publish-eligible."""
    pack, result = _render(fixture_corpus)
    emit_gate_record(pack, result.content_hash, "2026-06-14T12:00:00Z",
                     verdict=VERDICT_PASS, reviewer="curator")
    assert is_publish_eligible(pack)
    assert_publish_eligible(pack)  # does not raise


def test_AC_CLP_PUSH_5_no_record_refused(fixture_corpus):
    """No gate record at all -> publish refused."""
    pack, _ = _render(fixture_corpus)
    # No emit_gate_record call.
    with pytest.raises(UngatedPublishError):
        assert_publish_eligible(pack)


def test_AC_CLP_PUSH_5_pending_refused(fixture_corpus):
    pack, result = _render(fixture_corpus)
    emit_gate_record(pack, result.content_hash, "t", verdict=VERDICT_PENDING)
    with pytest.raises(UngatedPublishError):
        assert_publish_eligible(pack)


def test_AC_CLP_PUSH_5_fail_refused(fixture_corpus):
    pack, result = _render(fixture_corpus)
    emit_gate_record(pack, result.content_hash, "t", verdict=VERDICT_FAIL)
    with pytest.raises(UngatedPublishError):
        assert_publish_eligible(pack)


def test_AC_CLP_PUSH_5_content_hash_mismatch_refused(fixture_corpus):
    """A gate PASS recorded against a DIFFERENT content-hash (the pack
    body changed after the pass) -> publish refused. A stale gate pass
    cannot launder a re-rendered body."""
    pack, result = _render(fixture_corpus)
    emit_gate_record(pack, "deadbeef" * 8, "t",
                     verdict=VERDICT_PASS, reviewer="curator")
    assert result.content_hash != "deadbeef" * 8
    with pytest.raises(UngatedPublishError):
        assert_publish_eligible(pack)
