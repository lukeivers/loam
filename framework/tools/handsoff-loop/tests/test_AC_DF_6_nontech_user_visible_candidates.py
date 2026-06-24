"""AC.DF.6 — candidate designs are framed for the user's tech level
(defaulting NON-TECHNICAL); a non-tech user is never offered a candidate
whose primary interaction is developer machinery.

For a non-technical user (the default and the demo case) every surfaced
candidate is something the user can personally SEE and USE without
developer skill — a visible/interactive experience OR a sensible
automated delivery — and NO surfaced candidate's primary interaction is a
command-line tool, a daemon / background-watch service, a drop-folder to
configure, or any surface that presumes developer machinery.

Outcome, not method: the test asserts the SURFACED candidate set for a
non-tech user contains only see-and-use / sensible-delivery shapes and
excludes CLI/daemon-primary shapes. It does not prescribe how the tech
level is inferred or how the constraint is applied — a prompt constraint,
a seed partition, a held-out classifier, or any combination satisfies it.

Two checks:

  * a DETERMINISTIC offline check (the bulk of the file): the model
    double tries to hand a non-tech user a CLI candidate and a daemon
    candidate; the production path must drop them, surfacing only
    operable candidates — and FAIL (refuse) if it cannot assemble a real
    operable choice. This is the falsifiable AC.DF.6 guarantee.
  * an OUTCOME-ALTITUDE live check (env-gated): a real
    generate_candidate_designs run over the rehearsal-1 ask (a
    non-technical accounting-firm owner) with no pre-arranged state must
    surface ONLY candidates that pass the held-out is_nontech_operable
    classifier the generator never saw. Marked outcome-altitude: true.

This is the owner ruling
`2026-06-24-design-first-non-tech-user-visible-outputs` made falsifiable:
rehearsal-1 offered a CLI (option 1) and a "file-watch daemon" (option 3)
to a non-technical user — AC.DF.6 fails any candidate set that does that.

Per docs/plans/handsoff-design-first-and-build-heartbeat.md §5.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.generative import (  # noqa: E402
    GenerationUnavailable,
    TECH_LEVEL_NON_TECHNICAL,
    TECH_LEVEL_TECHNICAL,
    generate_candidate_designs,
    is_nontech_operable,
)
from handsoff_loop.grounding import (  # noqa: E402
    GroundingOutcome,
    PractitionerNorm,
)
from handsoff_loop.request_intent import RequestIntent  # noqa: E402


def _intent(ask="reconcile my firm's bank statements against the books each month"):
    return RequestIntent(
        ask=ask,
        inferred_intent=f"You want a tool for: {ask}",
        objective=f"objective derived from: {ask}",
    )


def _grounding():
    return GroundingOutcome(
        grounded=True, objective="obj",
        summary="Practitioners reconcile line by line.",
        norms=[PractitionerNorm(
            norm_id="N1", norm="Nothing is silently dropped.",
            source_url="https://example.org/a", source_title="A",
            http_status=200)],
        expert_gate_flags=[],
        record_path="/tmp/rec.md",
    )


def _candidate(form_factor, tool_plan, slug):
    return {
        "form_factor": form_factor,
        "tool_plan": tool_plan,
        "data_shape": "Reads input, writes output.",
        "gate_plain": f"Done when the {slug} produces a clean result.",
        "sample_output": {
            "summary": "Processed 12 rows; 2 need a human's eyes.",
            "rows": [{"id": 1, "status": "ok"},
                     {"id": 2, "status": "ok"}],
            "review_queue": [{"id": 7, "why": "ambiguous"}],
        },
    }


# --- the held-out classifier (the falsifiable AC.DF.6 check) ----------

def test_classifier_disqualifies_cli_and_daemon_for_nontech():
    # The exact rehearsal-1 failures: a command-line tool + a file-watch
    # daemon offered to a non-technical user. Both must be rejected.
    ok_cli, _ = is_nontech_operable(
        "one-shot command-line tool",
        "Run the tool from your terminal with the path to the files.")
    assert ok_cli is False
    ok_daemon, _ = is_nontech_operable(
        "file-watch daemon",
        "A background service watches a drop folder and runs nightly.")
    assert ok_daemon is False


def test_classifier_accepts_visible_and_delivery_for_nontech():
    # Visible/interactive experiences pass.
    ok_app, _ = is_nontech_operable(
        "web review app",
        "You open a web page, review the results on screen, click approve.")
    assert ok_app is True
    # A sensible automated delivery passes even though "scheduled" is
    # adjacent to the daemon family — the user touches the EMAIL, not a
    # daemon they manage.
    ok_email, _ = is_nontech_operable(
        "scheduled email report",
        "The finished report is emailed to you on a schedule; nothing to "
        "set up.")
    assert ok_email is True


# --- the production path drops CLI/daemon for a non-tech user ----------

def test_nontech_default_drops_cli_and_daemon_candidates():
    # The model double tries to hand the non-tech user a CLI and a daemon;
    # the production path must drop them and surface only operable ones.
    forms = [
        ("one-shot command-line tool",
         "Run it in your terminal on a folder of files."),
        ("web review app",
         "You open a page, review each item on screen, click approve."),
        ("file-watch daemon",
         "A background service watches a drop folder and runs nightly."),
        ("scheduled email report",
         "The finished reconciled report is emailed to you each month."),
    ]
    state = {"i": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = state["i"]
        state["i"] = i + 1
        ff, tp = forms[i % len(forms)]
        return {"result": json.dumps(_candidate(ff, tp, f"s{i}"))}

    # n=4 so all four shapes are attempted; the default tech level is
    # non-technical (no user_tech_level passed).
    cands = generate_candidate_designs(
        _intent(), _grounding(), n=4, llm_json_fn=_fn)

    # No surfaced candidate may be a CLI/daemon-primary shape.
    for c in cands:
        ok, why = is_nontech_operable(c.form_factor, c.tool_plan)
        assert ok, f"surfaced a non-operable candidate: {c.form_factor!r} ({why})"
    # The two operable candidates survived; the CLI + daemon were dropped.
    surfaced = {c.form_factor.lower() for c in cands}
    assert "one-shot command-line tool" not in surfaced
    assert "file-watch daemon" not in surfaced
    assert len(cands) >= 2


def test_nontech_refuses_when_only_machinery_candidates_remain():
    # If EVERY candidate the model returns is developer machinery, the
    # non-tech stage cannot surface a real operable choice — it must
    # refuse, not hand the user a CLI/daemon set.
    machinery = [
        ("one-shot command-line tool", "Run it in your terminal."),
        ("file-watch daemon", "A background service watches a folder."),
        ("cron job", "A crontab entry runs the script nightly."),
    ]
    state = {"i": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = state["i"]
        state["i"] = i + 1
        ff, tp = machinery[i % len(machinery)]
        return {"result": json.dumps(_candidate(ff, tp, f"m{i}"))}

    with pytest.raises(GenerationUnavailable, match="real choice"):
        generate_candidate_designs(_intent(), _grounding(),
                                   n=3, llm_json_fn=_fn)


def test_technical_user_still_gets_machinery_candidates():
    # The constraint is tech-level, NOT hardcode-web-only: a confirmed
    # TECHNICAL user may still be offered a CLI/daemon direction (the
    # mechanism is "infer level, constrain space", per the owner ruling).
    forms = ["one-shot CLI tool", "background daemon", "review-queue app"]
    state = {"i": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = state["i"]
        state["i"] = i + 1
        return {"result": json.dumps(
            _candidate(forms[i % len(forms)], "a tool", f"t{i}"))}

    cands = generate_candidate_designs(
        _intent(), _grounding(), n=3,
        user_tech_level=TECH_LEVEL_TECHNICAL, llm_json_fn=_fn)
    # The technical user is NOT filtered down — machinery candidates stand.
    surfaced = {c.form_factor.lower() for c in cands}
    assert any("cli" in s or "daemon" in s for s in surfaced)


def test_default_tech_level_is_non_technical():
    # The default (no user_tech_level) must be the constrained non-tech
    # path — a CLI candidate offered by the model is dropped by default.
    forms = [
        ("one-shot command-line tool", "Run it in your terminal."),
        ("web review app", "You open a page and approve on screen."),
        ("scheduled email report", "The report is emailed to you monthly."),
    ]
    state = {"i": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = state["i"]
        state["i"] = i + 1
        ff, tp = forms[i % len(forms)]
        return {"result": json.dumps(_candidate(ff, tp, f"d{i}"))}

    cands = generate_candidate_designs(_intent(), _grounding(),
                                       n=3, llm_json_fn=_fn)
    assert "one-shot command-line tool" not in {c.form_factor.lower()
                                                 for c in cands}


# --- outcome-altitude: a real generation surfaces only operable shapes -
# outcome-altitude: true

_LIVE = os.environ.get("HANDSOFF_LIVE_OA") == "1"


@pytest.mark.skipif(
    not _LIVE,
    reason="outcome-altitude live test — set HANDSOFF_LIVE_OA=1 to run "
           "(real claude -p, no pre-arranged state)")
def test_OA_real_nontech_generation_surfaces_only_operable_candidates():
    # A REAL generate_candidate_designs run over the rehearsal-1 ask (a
    # non-technical accounting-firm owner), no pre-arranged state, using
    # the production claude -p dispatch. Every surfaced candidate must
    # pass the held-out is_nontech_operable classifier the generator never
    # saw. This is the owner's "non-tech users only see see-and-use /
    # sensible-delivery candidates" ruling, verified end-to-end.
    intent = _intent(
        "I run a small accounting firm. Each month I need our bank "
        "statements reconciled against the books and the differences "
        "flagged for me to look at.")
    cands = generate_candidate_designs(
        intent, _grounding(), n=3,
        user_tech_level=TECH_LEVEL_NON_TECHNICAL)
    assert len(cands) >= 2, "live run did not surface a real choice"
    for c in cands:
        ok, why = is_nontech_operable(c.form_factor, c.tool_plan)
        assert ok, (
            f"live run surfaced a candidate a non-tech user cannot "
            f"operate: {c.form_factor!r} — {why}")
