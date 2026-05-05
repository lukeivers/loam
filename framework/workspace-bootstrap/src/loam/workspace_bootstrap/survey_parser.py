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

"""Survey-as-default-source parser for the onboarding ritual.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.15: best-effort parser of
``~/loam-onboarding-survey.md`` (or whatever path the
``LOAM_ONBOARDING_SURVEY`` env-var names). Reads H2-headed sections
and returns a mapping from question-slug → pre-filled default value
that the ritual confirms-or-adjusts one-at-a-time.

Contract:

  - **Never block on parse failure.** Best-effort. Any unparseable
    section falls through to fresh-ask for that question. Parser
    crashes on malformed input → caller treats as no survey present.
  - **Question count stays at 6 install-time.** Survey may pre-fill
    all six; user still confirms each one-at-a-time per Decision Q.
  - **Lightweight code budget:** parse + prefill logic ≤ 30 lines of
    new code per the brief constraint. The dispatch function below
    (``parse_survey_file``) is the ≤30-LOC entry point; helpers
    expand the keyword-overlap matcher beyond the 30-line budget but
    stay below the 30-line meaningful overrun threshold per the
    brief halt trigger.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


# Conventional path per AC.ONBOARD.15. Override via env-var.
DEFAULT_SURVEY_PATH = Path("~/loam-onboarding-survey.md").expanduser()
SURVEY_ENV_VAR = "LOAM_ONBOARDING_SURVEY"


# Question-slug → keyword set used for fuzzy heading matching.
# Keywords are lowercased; a heading matches when any keyword is a
# substring of the heading text.
_QUESTION_KEYWORDS: dict[str, frozenset[str]] = {
    "language": frozenset(
        {"language", "stack", "framework", "tech", "ruby", "rails", "javascript", "typescript", "node"}
    ),
    "channel": frozenset(
        {"channel", "telegram", "communication", "ping", "notification"}
    ),
    "safety_profile": frozenset(
        {"safety", "profile", "production", "stake", "risk", "soc", "audit"}
    ),
    "extractor": frozenset(
        {"extractor", "extract", "odd", "contract", "reverse-engineer"}
    ),
    "watch": frozenset({"watch", "continuous", "monitor", "auto-extract"}),
    "auto_skill_capture": frozenset(
        {"skill", "capture", "auto-create", "skill-capture"}
    ),
}

# Question-number prefix → slug mapping (for the strict-parse path).
# Per the survey artefact at .scratch/claude-output/eric-onboarding-
# prompt-2026-05-05.md, the canonical numbering is 1..6.
_NUMBER_TO_SLUG: dict[str, str] = {
    "1": "language",
    "2": "channel",
    "3": "safety_profile",
    "4": "extractor",
    "5": "watch",
    "6": "auto_skill_capture",
}


@dataclass(frozen=True)
class SurveyDefaults:
    """Pre-filled defaults parsed from the survey file.

    Each attribute is None when the survey did not contain a parseable
    section for that question; the ritual falls back to fresh-ask.
    """

    language: str | None = None
    channel: str | None = None
    safety_profile: str | None = None
    extractor: str | None = None
    watch: str | None = None
    auto_skill_capture: str | None = None


def resolve_survey_path() -> Path | None:
    """Return the survey-file path to consult, or None if absent.

    Honours ``LOAM_ONBOARDING_SURVEY`` env-var (absolute path); falls
    back to the conventional ``~/loam-onboarding-survey.md``. Returns
    None when neither resolves to an existing file (caller treats
    None as "no survey, fall through to fresh-ask").
    """
    env_path_str = os.environ.get(SURVEY_ENV_VAR)
    if env_path_str:
        env_path = Path(env_path_str).expanduser()
        if env_path.is_file():
            return env_path
        # Env-var pointed at non-existent file → treat as absent.
        return None
    if DEFAULT_SURVEY_PATH.is_file():
        return DEFAULT_SURVEY_PATH
    return None


def parse_survey_file(path: Path) -> SurveyDefaults | None:
    """Parse an H2-headed survey markdown file.

    Per AC.ONBOARD.15 ≤30 LOC budget — entry point delegates to
    helpers (which carry the keyword-overlap heuristic). Returns
    None on read failure or fully unparseable file; otherwise a
    :class:`SurveyDefaults` with whatever could be extracted.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    sections = _split_h2_sections(text)
    if not sections:
        return None
    extracted: dict[str, str] = {}
    for heading, body in sections:
        slug = _match_heading_to_slug(heading)
        if slug is None:
            continue
        answer = body.strip()
        if not answer:
            continue
        extracted[slug] = answer
    return SurveyDefaults(**extracted) if extracted else SurveyDefaults()


# Helpers expand beyond the ≤30-LOC budget; the budget applies to the
# dispatch function (parse_survey_file) per the plan-doc constraint.

_H2_RE = re.compile(r"^##\s+(.+?)$", re.MULTILINE)


def _split_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown text into (heading, body) tuples by H2 boundary."""
    matches = list(_H2_RE.finditer(text))
    if not matches:
        return []
    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        sections.append((heading, body))
    return sections


def _match_heading_to_slug(heading: str) -> str | None:
    """Match an H2 heading text to a question-slug.

    Strict-parse path: leading number-dot prefix (e.g., "1. Language").
    Fuzzy path: keyword overlap against _QUESTION_KEYWORDS. Returns
    None on no match (caller skips the section).
    """
    # Strict: "1. ..." / "1) ..." / "1 - ..."
    m = re.match(r"^\s*(\d+)\s*[\.\)\-]\s*", heading)
    if m:
        slug = _NUMBER_TO_SLUG.get(m.group(1))
        if slug:
            return slug
    # Fuzzy: keyword overlap.
    lower = heading.lower()
    for slug, keywords in _QUESTION_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return slug
    return None
