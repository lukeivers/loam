"""AC.DF.7 — every candidate design carries a user-operable end-to-end
LAUNCH workflow; a non-tech user is never offered a candidate whose launch
requires a terminal, a script run, or a dev-env.

AC.DF.6 guarantees the OUTPUT is visible (a wizard/app, not a CLI).
AC.DF.7 goes one layer deeper: a design can be visible (a GUI) yet still
UN-LAUNCHABLE by the target user. The rehearsal-2 failure built a Tkinter
wizard whose only way in was `python reconcile_gui.py` in a terminal —
visible output, but the launch path was the exact technical task the
non-tech user cannot do. Visible output is necessary but NOT sufficient:
the whole path to STARTING and USING the tool must be operable by the
target user.

So every candidate carries (a) a launch_mechanism label and (b) the
literal, ordered user_workflow steps. For a non-technical user the launch
must be a browser URL/link, a double-click packaged app, or email/file
delivery — and no workflow step may require a terminal/script/dev-env.

Outcome, not method: the test asserts the SURFACED candidate set for a
non-tech user carries a user-operable launch workflow on every candidate
(verified by the held-out is_launch_user_operable classifier the generator
never saw), and that a visible-output candidate with a terminal-only launch
is DROPPED. It does not prescribe the launch UI or how the constraint is
applied — a prompt constraint, a held-out classifier, or both satisfy it.

Two checks:

  * a DETERMINISTIC offline check (the bulk of the file): the model double
    tries to hand a non-tech user a candidate whose OUTPUT is a nice GUI
    but whose only launch is `python foo.py` in a terminal; the production
    path must drop it, surfacing only launch-operable candidates — and
    FAIL (refuse) if it cannot assemble a real operable choice.
  * an OUTCOME-ALTITUDE live check (env-gated): a real
    generate_candidate_designs run over the rehearsal-2 ask (a
    non-technical accounting-firm owner) with no pre-arranged state must
    surface ONLY candidates that pass the held-out
    is_launch_user_operable classifier the generator never saw. Marked
    outcome-altitude: true.

This is the owner ruling
`2026-06-24-design-must-carry-user-operable-launch-workflow` made
falsifiable: rehearsal-2 offered a Tkinter GUI launched by
`python reconcile_gui.py` to a non-technical user — AC.DF.7 fails any
candidate whose launch is a developer task even when its output is a GUI.

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
    CandidateDesign,
    GenerationUnavailable,
    TECH_LEVEL_NON_TECHNICAL,
    TECH_LEVEL_TECHNICAL,
    generate_candidate_designs,
    is_launch_user_operable,
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


def _candidate(form_factor, tool_plan, slug, *, launch="", workflow=()):
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
        "launch_mechanism": launch,
        "user_workflow": list(workflow),
    }


# --- the held-out classifier (the falsifiable AC.DF.7 check) ----------

def test_classifier_disqualifies_terminal_script_launch():
    # The exact rehearsal-2 failure: a GUI whose only way in is a terminal
    # script. The OUTPUT is visible, but the LAUNCH is a developer task.
    ok, why = is_launch_user_operable(
        "desktop app started from a terminal",
        ["Open a terminal",
         "Run python reconcile_gui.py",
         "Use the window that opens"])
    assert ok is False, why
    # A bare "run the script" launch is rejected.
    ok2, _ = is_launch_user_operable(
        "python script",
        ["Run the script with python3 to start the tool"])
    assert ok2 is False
    # A dev-env install step is rejected.
    ok3, _ = is_launch_user_operable(
        "local app",
        ["Install Python", "Run the program from the command line"])
    assert ok3 is False


def test_classifier_accepts_browser_doubleclick_and_delivery_launch():
    # A web app opened by URL — operable.
    ok_web, _ = is_launch_user_operable(
        "web app opened by URL",
        ["Open your web browser",
         "Go to the address we give you",
         "Drag your two files onto the page",
         "Click Reconcile",
         "Review the flagged rows"])
    assert ok_web is True
    # A double-click packaged app — operable.
    ok_dc, _ = is_launch_user_operable(
        "double-click app",
        ["Double-click the app icon on your desktop",
         "Pick your two files",
         "Click Reconcile"])
    assert ok_dc is True
    # Email/file delivery — operable.
    ok_email, _ = is_launch_user_operable(
        "scheduled email report",
        ["The finished report is emailed to you each month",
         "Open the file we send and read it"])
    assert ok_email is True


def test_classifier_rejects_no_launch_path():
    # A candidate that never tells the user how to START it cannot be
    # vouched operable.
    ok, _ = is_launch_user_operable("", [])
    assert ok is False


# --- the production path drops a terminal-launch GUI for a non-tech user

def test_nontech_default_drops_terminal_launched_gui():
    # The model double hands the non-tech user a visible GUI whose only
    # launch is a terminal script (rehearsal-2), plus two operable ones.
    # The production path must drop the terminal-launched one.
    forms = [
        ("desktop wizard (Tkinter)",
         "A friendly window with steps to reconcile your files.",
         "desktop app started from a terminal",
         ["Open a terminal", "Run python reconcile_gui.py",
          "Use the window"]),
        ("web review app",
         "You open a page, review each item on screen, click approve.",
         "web app opened by URL",
         ["Open your browser", "Go to the address", "Click Reconcile"]),
        ("scheduled email report",
         "The finished reconciled report is emailed to you each month.",
         "scheduled email report",
         ["The report is emailed to you", "Open the file we send"]),
    ]
    state = {"i": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = state["i"]
        state["i"] = i + 1
        ff, tp, launch, wf = forms[i % len(forms)]
        return {"result": json.dumps(
            _candidate(ff, tp, f"s{i}", launch=launch, workflow=wf))}

    cands = generate_candidate_designs(
        _intent(), _grounding(), n=3, llm_json_fn=_fn)

    # Every surfaced candidate carries a user-operable launch workflow.
    for c in cands:
        ok, why = is_launch_user_operable(c.launch_mechanism, c.user_workflow)
        assert ok, (
            f"surfaced a candidate the user cannot launch: "
            f"{c.form_factor!r} — {why}")
    # The terminal-launched GUI was dropped despite its visible output.
    surfaced = {c.form_factor.lower() for c in cands}
    assert "desktop wizard (tkinter)" not in surfaced
    assert len(cands) >= 2


def test_nontech_refuses_when_only_unlaunchable_candidates_remain():
    # If EVERY candidate the model returns is un-launchable by the user
    # (terminal/script launches), the non-tech stage cannot surface a real
    # operable choice — it must refuse, not hand the user a script set.
    unlaunchable = [
        ("web review app",
         "You review on a screen.",
         "started from a terminal",
         ["Open a terminal", "Run python app.py"]),
        ("desktop tool",
         "A window opens.",
         "command-line launch",
         ["Run the script with python3"]),
        ("local app",
         "A window opens.",
         "dev environment",
         ["Install Python", "Run the command in your shell"]),
    ]
    state = {"i": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = state["i"]
        state["i"] = i + 1
        ff, tp, launch, wf = unlaunchable[i % len(unlaunchable)]
        return {"result": json.dumps(
            _candidate(ff, tp, f"u{i}", launch=launch, workflow=wf))}

    with pytest.raises(GenerationUnavailable, match="real choice"):
        generate_candidate_designs(_intent(), _grounding(),
                                   n=3, llm_json_fn=_fn)


def test_chosen_candidate_carries_launch_into_build_direction():
    # AC.DF.7 build-target linkage: the chosen candidate's launch mechanism
    # + literal workflow flow into the buildable-design direction brief, so
    # the build TARGETS the form-factor the user settled on (a web-app-by-URL
    # design does not condition the build toward a desktop script).
    cand = CandidateDesign(
        form_factor="web app opened by URL",
        tool_plan="You open a page and reconcile your files.",
        data_shape="two CSVs in, one report out",
        gate_plain="Done when the page shows a clean reconciliation.",
        sample_output={"summary": "ok"},
        launch_mechanism="web app opened by URL",
        user_workflow=("Open your web browser",
                       "Go to the address we give you",
                       "Drag your two files onto the page",
                       "Click Reconcile"),
    )
    brief = cand.as_direction_brief()
    assert "web app opened by URL" in brief
    # The build is told to TARGET this launch form-factor, not advise it.
    assert "MUST target" in brief
    # The literal user workflow is carried so the build honors the steps.
    assert "Drag your two files onto the page" in brief


def test_technical_user_not_launch_filtered():
    # The constraint is tech-level, NOT hardcode-web-only: a confirmed
    # TECHNICAL user may still be offered a terminal-launched direction
    # (the mechanism is "infer level, constrain space", per the owner
    # ruling) — the launch filter does not apply to a technical user.
    forms = [
        ("one-shot CLI tool",
         "Run it from your terminal.",
         "command-line launch",
         ["Run the tool from your terminal"]),
        ("review-queue app",
         "A web page you open.",
         "web app opened by URL",
         ["Open your browser", "Go to the address"]),
        ("background daemon",
         "A service runs nightly.",
         "command-line launch",
         ["Start the service with a shell command"]),
    ]
    state = {"i": 0}

    def _fn(prompt, *, model="sonnet", timeout=0):
        i = state["i"]
        state["i"] = i + 1
        ff, tp, launch, wf = forms[i % len(forms)]
        return {"result": json.dumps(
            _candidate(ff, tp, f"t{i}", launch=launch, workflow=wf))}

    cands = generate_candidate_designs(
        _intent(), _grounding(), n=3,
        user_tech_level=TECH_LEVEL_TECHNICAL, llm_json_fn=_fn)
    # The technical user is NOT launch-filtered — a terminal-launch
    # direction can stand.
    surfaced = {c.form_factor.lower() for c in cands}
    assert any("cli" in s or "daemon" in s for s in surfaced)


# --- outcome-altitude: a real generation surfaces only launchable shapes
# outcome-altitude: true

_LIVE = os.environ.get("HANDSOFF_LIVE_OA") == "1"


@pytest.mark.skipif(
    not _LIVE,
    reason="outcome-altitude live test — set HANDSOFF_LIVE_OA=1 to run "
           "(real claude -p, no pre-arranged state)")
def test_OA_real_nontech_generation_surfaces_only_launchable_candidates():
    # A REAL generate_candidate_designs run over the rehearsal-2 ask (a
    # non-technical accounting-firm owner), no pre-arranged state, using
    # the production claude -p dispatch. Every surfaced candidate must
    # carry a launch workflow that passes the held-out
    # is_launch_user_operable classifier the generator never saw — and
    # carry a non-empty literal user_workflow. This is the owner's "the
    # design must carry the user-operable end-to-end launch workflow"
    # ruling, verified end-to-end.
    intent = _intent(
        "I run a small accounting firm. Each month I need our bank "
        "statements reconciled against the books and the differences "
        "flagged for me to look at.")
    cands = generate_candidate_designs(
        intent, _grounding(), n=3,
        user_tech_level=TECH_LEVEL_NON_TECHNICAL)
    assert len(cands) >= 2, "live run did not surface a real choice"
    for c in cands:
        assert c.user_workflow, (
            f"live candidate carried no literal user workflow: "
            f"{c.form_factor!r}")
        ok, why = is_launch_user_operable(c.launch_mechanism, c.user_workflow)
        assert ok, (
            f"live run surfaced a candidate a non-tech user cannot "
            f"launch: {c.form_factor!r} — {why}")
