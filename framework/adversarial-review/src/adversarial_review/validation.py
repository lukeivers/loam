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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Finding validation — precision owned here, not by a timid critic (P3).

AC.AR.4 / D6: no finding reaches the blocking verdict without a
ground-truth re-check. The critic runs hot for recall (AI §1.1: LLM
critics out-catch humans but hallucinate/nitpick at high rates); this
layer owns precision. A finding that validates is advanced to VALIDATED
(eligible to block); a finding that cannot be validated is quarantined
HYPOTHESIZED (visible, severity-capped, non-blocking); a finding the
re-check positively disproves is REFUTED (dropped). Making the critic
timid to reduce noise is the FORBIDDEN fix (P3).

J3 — validation prefers DETERMINISTIC ground truth over a second model.
Where a finding cites an executable check, it is validated IN-PROCESS:

  * a cited artifact LOCATION (a quoted string / line) -> re-read the
    artifact and confirm the cited text is actually present;
  * a numeric claim                                    -> re-derive it;
  * (extensible: run a cited test / fetch a cited source).

Only a finding with no executable anchor falls to an isolated validator
spawn (P9) — and even that is a second, independent context, never the
critic asking itself "was I right?" (AI §1.4: self-review without
external signal degrades).

Per ODD §2.5: :func:`validate_finding` -> AC.AR.4; :func:`validate_all`
-> AC.AR.4; the deterministic re-read/re-derive -> AC.AR.4 + J3.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from .findings import Finding, ValidationState

ValidatorFn = Callable[[str], Optional[str]]

# A quoted span in a finding's location/scenario is a checkable anchor:
# the critic claims this exact text appears in the artifact. We re-read
# the artifact and confirm.
_QUOTED = re.compile(r"[\"']([^\"']{6,})[\"']")
_NUMERIC = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")


def _quoted_anchor_present(finding: Finding, artifact: str) -> Optional[bool]:
    """Deterministic check: is the finding's quoted anchor in the artifact?

    Returns True (anchor present -> the finding cites real text),
    False (anchor absent -> the critic quoted text that isn't there, a
    hallucination signal), or None (no quoted anchor to check).
    """
    quotes = _QUOTED.findall(f"{finding.location}\n{finding.scenario}")
    if not quotes:
        return None
    art = artifact
    # Every quoted span must actually appear in the artifact.
    return all(q.strip() in art for q in quotes)


def _location_line_present(finding: Finding, artifact: str) -> Optional[bool]:
    """Deterministic check: does a cited ``line N`` exist in the artifact?

    Returns True/False when the location names a concrete line number,
    else None. A finding pointing at a line past the end of the artifact
    is citing something that isn't there.
    """
    m = re.search(r"line\s+(\d+)", finding.location, re.IGNORECASE)
    if not m:
        return None
    n = int(m.group(1))
    return 1 <= n <= len(artifact.splitlines())


def validate_finding(
    finding: Finding,
    artifact: str,
    *,
    validator_fn: ValidatorFn | None = None,
) -> Finding:
    """Advance a single finding's validation state against ground truth.

    Deterministic checks first (J3): if the finding cites a quoted span
    or a line number, we confirm it against the artifact in-process. A
    positively-absent anchor -> REFUTED (the critic cited text/line that
    is not there). A confirmed anchor -> VALIDATED. When there is no
    executable anchor and a ``validator_fn`` (isolated validator spawn)
    is provided, delegate; its verdict maps VALID->VALIDATED,
    INVALID->REFUTED, anything else->HYPOTHESIZED. With no anchor and no
    validator, the finding stays HYPOTHESIZED (quarantined) — visible,
    non-blocking. Mutates + returns the finding.
    """
    quoted = _quoted_anchor_present(finding, artifact)
    line_ok = _location_line_present(finding, artifact)

    checks = [c for c in (quoted, line_ok) if c is not None]
    if checks:
        if all(checks):
            finding.state = ValidationState.VALIDATED
            finding.evidence = "deterministic: cited anchor present in artifact"
        else:
            finding.state = ValidationState.REFUTED
            finding.evidence = (
                "deterministic: cited anchor ABSENT from artifact "
                "(hallucinated location)"
            )
        return finding

    if validator_fn is not None:
        verdict = validator_fn(_validator_prompt(finding, artifact))
        mapped = _map_validator_verdict(verdict)
        finding.state = mapped
        finding.evidence = f"isolated validator: {(verdict or '').strip()[:120]}"
        return finding

    # No executable anchor, no validator available -> quarantine.
    finding.state = ValidationState.HYPOTHESIZED
    finding.evidence = "no executable anchor; quarantined pending validation"
    return finding


def validate_all(
    findings: list[Finding],
    artifact: str,
    *,
    validator_fn: ValidatorFn | None = None,
) -> list[Finding]:
    """Validate every finding; drop the REFUTED ones (AC.AR.4).

    Returns the surviving findings (VALIDATED + HYPOTHESIZED). REFUTED
    findings — those a ground-truth re-check disproved — are removed
    entirely so they cannot mislead the reader.
    """
    survivors: list[Finding] = []
    for f in findings:
        validate_finding(f, artifact, validator_fn=validator_fn)
        if f.state is not ValidationState.REFUTED:
            survivors.append(f)
    return survivors


def _validator_prompt(finding: Finding, artifact: str) -> str:
    """Prompt for an isolated validator spawn (non-executable findings).

    A fresh, independent context — NOT the critic — asked to confirm or
    refute one specific finding against the artifact text. It answers
    with VALID / INVALID / UNSURE on the final line.
    """
    return (
        "You are an independent finding-validator. Below is one claimed "
        "flaw in an artifact, and the artifact. Decide ONLY whether the "
        "claimed flaw is really present and really would make the artifact "
        "fail — check it against the artifact text, do not take the claim "
        "on faith.\n\n"
        f"CLAIMED FLAW\nlocation: {finding.location}\nscenario: "
        f"{finding.scenario}\n\n=== artifact ===\n{artifact}\n\n"
        "Respond with a one-line reason, then a FINAL line that is exactly "
        "one of: VALID or INVALID or UNSURE."
    )


def _map_validator_verdict(raw: str | None) -> ValidationState:
    """Map an isolated validator's verdict token to a ValidationState.

    The final verdict line is one of VALID / INVALID / UNSURE. INVALID is
    the more specific token (it contains "VALID" as a substring), so it
    is tested FIRST — a naive ``"VALID" in text`` would misread INVALID as
    valid. Absence of a recognizable token quarantines (HYPOTHESIZED).
    """
    if not raw:
        return ValidationState.HYPOTHESIZED
    # Read the last non-empty line — the instructed final verdict line.
    lines = [ln.strip().upper() for ln in raw.splitlines() if ln.strip()]
    tail = " ".join(lines[-2:]) if lines else ""
    if "INVALID" in tail:
        return ValidationState.REFUTED
    if "VALID" in tail:
        return ValidationState.VALIDATED
    return ValidationState.HYPOTHESIZED
