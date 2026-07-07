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

"""AC.RTEL.4 — FAIL-OPEN. A telemetry write failure (unwritable sink)
does not raise and does not change retrieve()'s returned block.

The recorder is instrumentation on the every-turn recall path; a broken
sink must degrade to no-telemetry, never break the turn.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus


def _cfg(tmp_path: Path, corpus_dir: Path, telemetry_dir) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        telemetry_dir=telemetry_dir,
    )


def test_AC_RTEL_4_unwritable_sink_never_raises_or_changes_block(
    tmp_path: Path,
) -> None:
    corpus_dir = tmp_path / "memory"
    write_corpus(corpus_dir)

    # An unwritable sink: a telemetry_dir whose parent is a FILE, so the
    # recorder's mkdir(parents=True) raises NotADirectoryError — which
    # the fail-open guard must swallow.
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a directory", encoding="utf-8")
    bad_dir = blocker / "retrieval-telemetry"

    off = retrieve(
        prompt="continue the batch",
        config=_cfg(tmp_path, corpus_dir, telemetry_dir=None),
    )
    # Must not raise.
    with_bad = retrieve(
        prompt="continue the batch",
        config=_cfg(tmp_path, corpus_dir, telemetry_dir=bad_dir),
    )

    assert with_bad == off, (
        "a failing telemetry sink changed the recall block — fail-open "
        "must leave recall byte-identical"
    )
    # No file/dir was created at the bad path.
    assert not bad_dir.exists()
