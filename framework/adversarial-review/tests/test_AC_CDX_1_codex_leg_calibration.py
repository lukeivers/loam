# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.CDX.1 (outcome-altitude, WS-D2) — n=1 calibration: a seeded-flaw artifact
run through the Codex leg via the production pipeline surfaces the planted
defect, tagged ``leg="codex"``, and ``calibrate`` reads back a nonzero catch
rate.

Deterministic (mirrors the sealed AC.AR.10 posture, D-CDX.5): only the ``codex``
process boundary is stubbed — ``shutil.which`` (binary present) and
``subprocess.run`` (canned codex ``--json`` output carrying the seeded anchor).
The REAL argv-build, env-scrub, ``--json`` extraction, ``parse_findings``,
registry resolution, and calibration scoring all execute. The live-codex
model-quality proof is the opt-in ``test_AR_S_real_codex_smoke`` (owner-gated)."""
from __future__ import annotations

import json
import subprocess

from conftest import finding_block

from adversarial_review import codex
from adversarial_review.calibration import SeededFlaw, calibrate
from adversarial_review.manual import review_text
from adversarial_review.registry import Role

# An artifact carrying one planted, distinctively-anchored flaw.
_SEEDED_ARTIFACT = (
    "# Market-sizing memo\n\n"
    "The TAM is asserted as CODEX_FLAW_UNSOURCED_TAM of $9B with no bottom-up "
    "derivation or citation anywhere in the memo.\n"
    "The remaining sections are internally consistent and correctly derive the "
    "serviceable segment from the stated (if unsourced) top-line figure.\n"
)
_FLAWS = [
    SeededFlaw(
        "CX1",
        "CODEX_FLAW_UNSOURCED_TAM",
        "the TAM figure is unsourced",
        "HIGH",
    ),
]
_OBJECTIVE = "a defensible market-sizing memo: every material figure sourced."


def _canned_codex_stdout() -> str:
    """A realistic ``codex exec --json`` DIFF-phase reply carrying the anchor.

    The DERIVE phase (artifact-blind) and the DIFF phase share one ``ModelFn``;
    the DIFF phase demands the ``FINDING…END`` shape, so a single canned reply
    carrying a FINDING block satisfies both phases (DERIVE just gets it as its
    free-form 'spec', which is harmless — only DIFF output is parsed for
    findings)."""
    block = finding_block(
        'the TAM line "CODEX_FLAW_UNSOURCED_TAM"',
        "HIGH",
        'the TAM "CODEX_FLAW_UNSOURCED_TAM" of $9B is asserted with no '
        "bottom-up derivation or citation.",
    )
    return json.dumps({"type": "agent_message", "text": block}) + "\n"


def _install_fake_codex(monkeypatch, *, stdout: str, returncode: int = 0):
    """Stub ONLY the codex process boundary; everything else is real."""
    captured: dict = {}

    def _fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(codex.shutil, "which", lambda _bin: "/usr/local/bin/codex")
    monkeypatch.setattr(codex.subprocess, "run", _fake_run)
    return captured


def test_AC_CDX_1_calibrate_through_codex_leg_catches_planted_flaw(monkeypatch):
    # Codex-only CRITIC so the caught finding is unambiguously the codex leg's.
    captured = _install_fake_codex(monkeypatch, stdout=_canned_codex_stdout())
    registry = codex.codex_critic_registry(include_claude=False)

    result = calibrate(_SEEDED_ARTIFACT, _OBJECTIVE, _FLAWS, registry=registry)

    assert result.ran is True
    assert result.catch_rate == 1.0
    assert "CX1" in result.caught
    # The real leg actually spawned the read-only codex argv.
    assert captured["argv"][:5] == [
        "/usr/local/bin/codex",
        "exec",
        "--json",
        "--sandbox",
        "read-only",
    ]


def test_AC_CDX_1_finding_is_tagged_codex_through_production_entry(monkeypatch):
    # Through review_text (the production entry), the surfaced finding carries
    # leg="codex" and the run reports codex as a producing leg.
    _install_fake_codex(monkeypatch, stdout=_canned_codex_stdout())
    registry = codex.codex_critic_registry(include_claude=False)

    result = review_text(_SEEDED_ARTIFACT, _OBJECTIVE, registry=registry)

    assert result.ran is True
    assert result.legs_used == ("codex",)
    anchored = [
        f
        for f in result.verdict.findings
        if "CODEX_FLAW_UNSOURCED_TAM" in f.location
        or "CODEX_FLAW_UNSOURCED_TAM" in f.scenario
    ]
    assert anchored, "the planted defect did not surface through the codex leg"
    assert all(f.leg == "codex" for f in anchored)


def test_AC_CDX_1_raw_stdout_fallback_still_yields_findings(monkeypatch):
    # Robustness (D-CDX.2): if codex emits plain text (not JSONL), the
    # format-agnostic FINDING…END parse still recovers the finding.
    raw_block = finding_block(
        'the TAM line "CODEX_FLAW_UNSOURCED_TAM"',
        "HIGH",
        'the TAM "CODEX_FLAW_UNSOURCED_TAM" is unsourced.',
    )
    _install_fake_codex(monkeypatch, stdout=raw_block + "\n")
    registry = codex.codex_critic_registry(include_claude=False)

    result = calibrate(_SEEDED_ARTIFACT, _OBJECTIVE, _FLAWS, registry=registry)
    assert result.ran is True
    assert "CX1" in result.caught
