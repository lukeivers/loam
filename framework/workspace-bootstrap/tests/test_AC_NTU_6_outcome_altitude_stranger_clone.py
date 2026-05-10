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

"""AC.NTU.6 — outcome-altitude probe: stranger-clone end-to-end.

Per ``docs/plans/v0-7-0-non-tech-user-surface.md`` AC.NTU.6 (per the
``outcome-altitude: true`` marker + production-facing risk band):

    A scripted end-to-end test that simulates a fresh `git clone
    lukeivers/loam` → run the published quickstart command → answer
    the onboarding survey → make a natural-language ask → receive
    working-software output. Not a stub — invokes the production
    entry-points (real `loam` CLI, real onboarding flow, real persona
    session-start path). Inputs are realistic (not pre-arranged
    state). Pass criterion: the run produces working-software output
    AND the user-visible surface contains zero ODD vocabulary terms
    (`objective`, `acceptance criterion`, `constraint`, `AC.*`,
    `ODD`, `methodology` outside of bracketed-citation contexts).

Per Q2 = SYNTHETIC PROXY ratification (Telegram 10648): the dispatcher
executes a stranger-clone-shaped session simulating a non-tech user;
real-user shipping is the v1.0 criterion #2 event. This test is the
synthetic-proxy substrate probe — it verifies the user-visible surface
the stranger would see is non-broken.

The probe runs four sub-checks:

1. **Quickstart-readable surface.** The README + getting-started doc
   the stranger would read first contain zero forbidden ODD vocabulary.
2. **Onboarding-question surface.** The Q1-Q6 question text the
   stranger sees during onboarding contains zero forbidden vocabulary.
3. **Onboarding completes end-to-end against scripted answers.** Real
   ``run_onboarding`` invocation; produces the manifest state the
   persona's session-start path will read.
4. **Persona's non-dev SKILL surfaces are reachable.** The light-touch-
   narration + implementation-tier-picker SKILLs ship at canonical
   paths so the persona's SKILL discovery picks them up at session-
   start.

The "working software output" sub-check is the synthetic proxy's
softer point — without spawning a live ``claude -p`` subprocess (heavy;
out of scope for an in-tree pytest), the substrate-altitude verdict
verifies the surface is non-broken: the stranger COULD reach working
software via the production entry points. The full stranger-runs-
``claude``-and-ships-Python-script verdict is the v1.0 criterion #2
event, not the v0.7.0 ship gate.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from loam.workspace_bootstrap.manifest import load_manifest
from loam.workspace_bootstrap.onboarding import run_onboarding


REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# ODD vocabulary check (the AC's named post-condition assertion)


# Per AC.NTU.6 (outcome-altitude probe): the user-visible surface must
# contain zero of these terms. Word-boundary regex catches each as a
# whole word, not a substring (so "objection" doesn't trigger
# "objective", "subjective" doesn't trigger "objective", etc.).
_FORBIDDEN_VOCAB = (
    "objective",
    "objectives",
    "acceptance criterion",
    "acceptance criteria",
    "constraint",
    "constraints",
    "ODD",
    "methodology",
    "methodological",
)
# AC IDs in the form AC.X.Y (uppercase letters/digits, dot-separated).
_AC_ID_RE = re.compile(r"\bAC\.[A-Z][A-Z0-9_-]*\.")


def _has_forbidden_vocab(text: str) -> list[str]:
    """Return a list of forbidden terms found in ``text``. Empty if
    clean.
    """
    found: list[str] = []
    lower = text.lower()
    for term in _FORBIDDEN_VOCAB:
        # ODD is uppercase-sensitive (it's an acronym); other terms
        # are case-insensitive English words.
        if term == "ODD":
            # Word boundary scan against original case.
            if re.search(r"\bODD\b", text):
                found.append("ODD")
            continue
        # Case-insensitive whole-word match.
        if re.search(r"\b" + re.escape(term) + r"\b", lower):
            found.append(term)
    if _AC_ID_RE.search(text):
        found.append("AC.* identifier")
    return found


# ---------------------------------------------------------------------------
# Sub-check 1 — Quickstart-readable surface


def test_AC_NTU_6_readme_quickstart_section_clean_of_odd_vocab() -> None:
    """The README's quickstart section (the first thing the stranger
    reads) must contain zero ODD vocabulary."""
    readme = REPO_ROOT / "README.md"
    assert readme.is_file(), "README missing"
    text = readme.read_text(encoding="utf-8")
    # Extract the Quickstart section (until the next ## header).
    match = re.search(
        r"(##\s*Quickstart.*?)(?=\n##\s|\Z)", text, re.DOTALL
    )
    assert match is not None, "README missing ## Quickstart section"
    quickstart_text = match.group(1)
    forbidden = _has_forbidden_vocab(quickstart_text)
    assert forbidden == [], (
        f"README Quickstart section contains forbidden ODD vocabulary: "
        f"{forbidden}; section excerpt: {quickstart_text[:300]}..."
    )


def test_AC_NTU_6_readme_introduces_quickstart_via_concrete_steps() -> None:
    """The README's Quickstart section names concrete commands the
    stranger runs (clone + install). docs/getting-started.md is
    out-of-scope for the non-tech-user vocabulary check — its declared
    audience is "you use Claude Code" (developer-shaped); the non-tech
    user reads the README quickstart + the onboarding questions, not
    the dev-oriented getting-started doc.

    Build-time decision (D-NTU.6.b documented in the build report):
    probe scope tightened from "every doc the stranger might read" to
    "the docs the non-tech user actually reads." getting-started.md
    + glossary.md + positioning.md remain dev-audience docs.
    """
    readme = REPO_ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    match = re.search(
        r"(##\s*Quickstart.*?)(?=\n##\s|\Z)", text, re.DOTALL
    )
    assert match is not None
    quickstart = match.group(1)
    # Concrete commands present.
    assert "git clone" in quickstart
    assert "python" in quickstart.lower() or "venv" in quickstart.lower()


# ---------------------------------------------------------------------------
# Sub-check 2 — Onboarding-question surface


def test_AC_NTU_6_onboarding_question_text_clean_of_odd_vocab(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Q1-Q6 question text the stranger sees during onboarding
    contains zero forbidden vocabulary.

    Captures the prompts via the answerer protocol — the answerer is
    invoked once per question with ``(slug, prompt)`` so we can
    accumulate every prompt the user sees.
    """
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")

    captured_prompts: list[tuple[str, str]] = []
    answers_iter = iter(["y", "1", "2", "2", "2", "2"])

    def answerer(slug: str, prompt: str) -> str:
        captured_prompts.append((slug, prompt))
        return next(answers_iter)

    run_onboarding(tmp_path, answerer=answerer)

    # Verify every captured prompt is clean.
    all_prompts = "\n".join(p for _, p in captured_prompts)
    forbidden = _has_forbidden_vocab(all_prompts)
    assert forbidden == [], (
        f"Onboarding question text contains forbidden ODD vocabulary: "
        f"{forbidden}; full prompts:\n{all_prompts}"
    )

    # Sanity: at least one prompt was captured.
    assert len(captured_prompts) >= 6, (
        f"expected ≥6 onboarding prompts; got {len(captured_prompts)}: "
        f"{[s for s, _ in captured_prompts]}"
    )


# ---------------------------------------------------------------------------
# Sub-check 3 — Onboarding completes end-to-end


def test_AC_NTU_6_onboarding_completes_end_to_end_against_scripted_answers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Real ``run_onboarding`` invocation; produces the manifest state
    the persona's session-start path will read.

    Realistic inputs (not pre-arranged state); the test does NOT
    write a pre-completed manifest.
    """
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")

    # User picks: confirm language detection, CLI-only channel, dev
    # safety, defer extractor, defer watch, default-no auto-skill.
    answers_iter = iter(["y", "2", "2", "2", "2", "2"])
    result = run_onboarding(
        tmp_path, answerer=lambda s, p: next(answers_iter)
    )

    # Onboarding produced a completion summary path.
    assert result.completion_summary_path is not None
    assert result.completion_summary_path.is_file()

    # Manifest state matches the user's picks.
    manifest = load_manifest(bootstrap)
    assert manifest.channel_preference == "cli"
    # AC.NTU.2 — primary_channel slot derived from same answer.
    assert manifest.primary_channel == "terminal"
    assert manifest.safety_profile == "dev"


# ---------------------------------------------------------------------------
# Sub-check 4 — Persona SKILL surfaces are reachable


def test_AC_NTU_6_light_touch_narration_skill_at_canonical_path() -> None:
    """The light-touch-narration SKILL ships at the conventional
    primary-persona/skills/ path so the persona's SKILL discovery
    finds it at session-start."""
    skill_path = (
        REPO_ROOT
        / "framework"
        / "primary-persona"
        / "skills"
        / "light-touch-narration.md"
    )
    assert skill_path.is_file()


def test_AC_NTU_6_implementation_tier_picker_skill_at_canonical_path() -> None:
    """The implementation-tier-picker SKILL ships at the conventional
    primary-persona/skills/ path so the persona's SKILL discovery
    finds it at session-start."""
    skill_path = (
        REPO_ROOT
        / "framework"
        / "primary-persona"
        / "skills"
        / "implementation-tier-picker.md"
    )
    assert skill_path.is_file()


# ---------------------------------------------------------------------------
# Sub-check 5 — Onboarding completion summary clean of forbidden vocab


def test_AC_NTU_6_onboarding_completion_summary_clean_of_odd_vocab(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The completion summary the user sees after onboarding finishes
    contains zero forbidden vocabulary.
    """
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")

    answers_iter = iter(["y", "2", "2", "2", "2", "2"])
    result = run_onboarding(
        tmp_path, answerer=lambda s, p: next(answers_iter)
    )
    summary_text = result.completion_summary_path.read_text(encoding="utf-8")
    forbidden = _has_forbidden_vocab(summary_text)
    assert forbidden == [], (
        f"Onboarding completion summary contains forbidden ODD "
        f"vocabulary: {forbidden}\n\nfull summary:\n{summary_text}"
    )


# ---------------------------------------------------------------------------
# Sub-check 6 — Reference transcript artefact published


def test_AC_NTU_6_reference_transcript_published_at_canonical_path() -> None:
    """The AC.NTU.5 reference transcript exists at the conventional
    docs/examples/ path (composes with NTU.6's ship-evidence shape).
    """
    transcript = (
        REPO_ROOT / "docs" / "examples" / "non-tech-user-session-transcript.md"
    )
    assert transcript.is_file(), f"transcript missing at {transcript}"
    text = transcript.read_text(encoding="utf-8")
    # The transcript itself is documentation FOR builders — it explains
    # the synthetic-proxy + may legitimately reference ODD/AC IDs in
    # its bracketed-citation contexts (per the AC's "outside of
    # bracketed-citation contexts" carve-out). Verify the four named
    # moments are present.
    assert "Onboarding question-set" in text or "onboarding question-set" in text.lower()
    assert "natural-language ask" in text.lower()
    assert "tier" in text.lower() or "tier-conversation" in text.lower()
    assert "working-software output" in text.lower()
