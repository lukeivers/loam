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

"""AC.PMGEN.1 — the generated companion is in sync with the catalogue.

The human-readable companion at ``docs/design/protection-matrix.md`` is
GENERATED from the catalogue (DO-NOT-hand-edit). After this cycle's catalogue
edits (two new rows + the narration fold), the committed companion must
reflect them: every catalogue row id appears in the companion's matrix table,
and the companion has been refreshed (not left stale).

The rendered body carries a ``Coverage checked: <date>`` line, so a byte-exact
compare across days is not the sync property; the durable property is that the
SET of rows + their gap verdicts in the committed companion equals the
catalogue's — i.e. the companion is a faithful projection of the current YAML.
"""

from __future__ import annotations

from loam.protection_matrix.check import (
    companion_doc_path,
    render_companion_doc,
    run_coverage_check,
)


def test_AC_PMGEN_1_every_catalogue_row_is_in_the_committed_companion() -> None:
    """The committed companion names every current catalogue row id."""
    report = run_coverage_check()
    companion = companion_doc_path(report.repo_root)
    assert companion.is_file(), "the generated companion must be committed"
    body = companion.read_text(encoding="utf-8")
    for v in report.verdicts:
        assert v.row.id in body, (
            f"catalogue row {v.row.id} is missing from the committed "
            f"companion — the companion is stale; regenerate with "
            f"`loam guards --refresh`."
        )
    # This cycle's three landed bindings are present in the companion.
    assert "FM.PROCESS-DRIFT" in body
    assert "FM.COMMS-PATH-DEAD" in body


def test_AC_PMGEN_1_committed_companion_matches_a_fresh_render() -> None:
    """The committed companion equals a fresh render (modulo the date line).

    The only intentionally-volatile line is the ``Coverage checked: <date>``
    stamp; every other line of the committed companion must equal a fresh
    re-derivation — proving it was regenerated from the current catalogue,
    not hand-edited or left stale.
    """
    report = run_coverage_check()
    companion = companion_doc_path(report.repo_root)
    committed = companion.read_text(encoding="utf-8")
    # The refresh path writes ``render_companion_doc(report) + "\n"`` — mirror
    # that so the comparison is against the exact artefact the CLI produces.
    fresh = render_companion_doc(report) + "\n"

    def _strip_volatile(text: str) -> list[str]:
        return [
            ln
            for ln in text.splitlines()
            if not ln.startswith("*Coverage checked:")
        ]

    assert _strip_volatile(committed) == _strip_volatile(fresh), (
        "the committed companion diverges from a fresh render of the current "
        "catalogue (beyond the date line) — it is stale or hand-edited; "
        "regenerate with `loam guards --refresh`."
    )


def test_AC_PMGEN_1_companion_carries_the_generated_banner() -> None:
    """The companion keeps its GENERATED / DO-NOT-hand-edit banner."""
    report = run_coverage_check()
    body = companion_doc_path(report.repo_root).read_text(encoding="utf-8")
    assert "GENERATED" in body
    assert "DO NOT hand-edit" in body
