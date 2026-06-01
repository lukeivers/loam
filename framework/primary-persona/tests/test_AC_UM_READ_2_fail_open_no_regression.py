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

"""AC.UM.READ.2 — fail-open to the openness prior, no regression.

When the matrix file is missing / unreadable / malformed, the read-path
degrades to the openness prior (or no injection) and NEVER raises — the
turn proceeds exactly as the un-personalized keep-pace chain does today.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace import interaction_model as im


def test_AC_UM_READ_2_missing_file_loads_empty_model(tmp_path: Path) -> None:
    """A claude_home with NO matrix file loads an empty model (never raises)."""
    model = im.load_interaction_model(tmp_path)
    assert isinstance(model, im.InteractionModel)
    assert model.areas == {}


def test_AC_UM_READ_2_missing_cell_degrades_to_openness_prior(
    tmp_path: Path,
) -> None:
    """A missing cell resolves to the openness prior — open exposure, the
    CAUTIOUS surface autonomy (never the bold value)."""
    model = im.load_interaction_model(tmp_path)  # empty
    exp = model.cell_or_prior("ops-and-money", "technical-exposure")
    aut = model.cell_or_prior("ops-and-money", "autonomy")
    assert exp.value == "open"
    assert aut.value == "surface"  # never escalates to bold autonomy


def test_AC_UM_READ_2_garbled_matrix_never_raises(tmp_path: Path) -> None:
    """A wholly-garbled matrix file parses to an empty model, no raise."""
    (tmp_path / "INTERACTION-MODEL.md").write_text(
        "this is not\na matrix at all\n{{{ broken", encoding="utf-8"
    )
    model = im.load_interaction_model(tmp_path)
    assert model.areas == {} or all(
        not v for v in model.areas.values()
    )


def test_AC_UM_READ_2_contributor_returns_none_on_total_failure(
    tmp_path: Path,
) -> None:
    """The read-path contributor NEVER raises — a broken envelope or
    missing matrix yields None (no injection), so the chain proceeds."""
    cfg = im.InteractionModelConfig(claude_home=tmp_path / "no-such-dir")
    contrib = im.build_interaction_model_contributor(cfg)
    # A garbage envelope must not raise.
    assert contrib(None) is None or isinstance(contrib(None), str)  # type: ignore[arg-type]
    assert contrib({}) is None or isinstance(contrib({}), str)
    # The contributor with no matrix still fails open (the openness prior
    # is the injection floor — a string or None, never an exception).
    out = contrib({"prompt": "anything"})
    assert out is None or isinstance(out, str)


def test_AC_UM_READ_2_malformed_axis_line_skipped_not_fatal(
    tmp_path: Path,
) -> None:
    """A matrix with one malformed axis line still parses the rest — the
    bad cell degrades to the prior; the good cells survive."""
    (tmp_path / "INTERACTION-MODEL.md").write_text(
        "# interaction-model\n\n"
        "## code-and-builds\n"
        "technical-exposure: { value: deep, confidence: high, evidence: [] }\n"
        "autonomy: THIS LINE IS MALFORMED\n",
        encoding="utf-8",
    )
    model = im.load_interaction_model(tmp_path)
    # The good cell parsed.
    assert model.cell("code-and-builds", "technical-exposure").value == "deep"
    # The malformed cell degrades to the prior (cautious autonomy).
    assert model.cell_or_prior("code-and-builds", "autonomy").value == "surface"
